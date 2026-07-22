#!/usr/bin/env python
import argparse
import logging as log
import os
import h5py

import hashlib

def read_potcar_file_and_check_for_hash(potcar):
    potcar_file = open(potcar, "r")
    content = potcar_file.read()
    configs = content.split("End of Dataset\n")
    configs.pop()
    hashes = []
    for config in configs:
        tmp = config.split('\n')
        if tmp[3].strip().startswith('SHA256'):
            hashes.append(tmp[3].split()[2])

    return {"content" : configs, "hashes" : hashes}

def get_hash_from_potcarh5(potcarh5, content):

    #calculate hash sha256
    m = hashlib.sha256()
    m.update(content + "End of Dataset\n")
    hash = m.hexdigest()
    log.debug("calculated hash: {hash}".format(hash=hash))
    #
    # try to find hash via calculated hash
    #
    potentialtypes = ["LDA", "PBE"]
    hashes = []
    for pottype in potentialtypes:
        atom_names = potcarh5[pottype].keys()
        for atom_name in atom_names:
            atom_rev = potcarh5[pottype + "/" + atom_name].keys()
            atom_rev.remove('latest')
            if hash in atom_rev:
                return {'hash' : hash, 'type' : pottype, 'name': atom_name}
    #
    # search by comparing content of potentials
    #
    potentialtypes = ["LDA", "PBE"]
    hashes = []
    for pottype in potentialtypes:
        atom_names = potcarh5[pottype].keys()
        for atom_name in atom_names:
            atom_rev = potcarh5[pottype + "/" + atom_name].keys()
            atom_rev.remove('latest')
            for atom_item in atom_rev:
                atom_content = potcarh5[pottype + "/" + atom_name + "/" + atom_item].value
                atom = atom_content[0].split("\n")
                #
                # remove SHA256 and COPYR Lines by line number
                #
                for i in range(4):
                    atom.pop(3)
                atom.pop()
                atom.pop()
                content = content.rstrip()
                tmp = "\n"
                tmp = tmp.join(atom)
                if (tmp == content):
                    return {'hash' : atom_item, 'type' : pottype, 'name': atom_name}
    return {'hash' : '--', 'type' : '--', 'name': '--'}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tool for getting hashes of POTCAR')
    parser.add_argument('--potcar', help='POTCAR file name', metavar='potcar')
    parser.add_argument('--potcarh5', help='POTCAR.h5 file name', metavar='potcarh5')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    args = parser.parse_args()
    #
    # verbosity
    #
    if args.verbose:
        log.basicConfig(format="%(levelname)5s: %(message)s", level=log.DEBUG)
        log.info("Verbose output!")
    else:
        log.basicConfig(format="%(levelname)5s: %(message)s", level=log.INFO)
    #
    # get POTCAR.h5-file
    #
    if args.potcar is None:
        if os.path.isfile('POTCAR'):
            args.potcar = 'POTCAR'
        else:
            raise NameError("POTCAR not found")
    #
    # get POTCAR.h5-file
    #
    if args.potcarh5 is None:
        if (os.environ.get('VASP_POTENTIALS') is not None):
            args.potcarh5 = os.environ.get('VASP_POTENTIALS')
        else:
            raise NameError('POTCAR.h5 not found')
    log.info("Using {path2h5} for lookup".format(path2h5=args.potcarh5))
    #
    # check po
    #
    potcarh5 = h5py.File(args.potcarh5, "r")
    #
    # try to open POSCAR and read atom information
    #
    potcars = read_potcar_file_and_check_for_hash(args.potcar)

    hashes = []
    if (potcars["hashes"] == []):
        for item in potcars["content"]:
            hashes.append(get_hash_from_potcarh5(potcarh5, item))


    if (potcars["hashes"] != []):
        log.info("Found following hashes in file:")
        for item in potcars["hashes"]:
            log.info("    {hash_short}  {hash}".format(hash_short=item[0:8], hash=item))
    else:
        log.info("Found following hashes in file:")
        log.info("")
        log.info("Type | Atom                | short    | long")
        log.info("--------------------------------------------------------------------------------------------------------")
        for item in hashes:
            log.info("{pottype:3s}  | {atom_name:19s} | {hash_short:8s} | {hash}".format(pottype=item['type'], atom_name=item['name'], hash_short=item['hash'][0:8], hash=item['hash']))
        potcarh5.close()
