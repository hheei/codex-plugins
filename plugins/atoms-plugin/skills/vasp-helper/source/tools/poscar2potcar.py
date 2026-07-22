#!/usr/bin/env python
import argparse
import logging as log
import os
import h5py

def get_atoms_configuration(poscar):
    log.debug("Reading " + poscar)
    poscarfile = open(poscar)
    lines = poscarfile.readlines();
    poscarfile.close()
    potcar_info = lines[5].split()
    atoms_conf = []
    log.debug("atom configuration:")
    for atom in potcar_info:
        atom_conf = atom.split('/')
        if len(atom_conf) == 1:
            atom_conf.append('latest')
        atoms_conf.append(atom_conf)
        log.debug("    {atom:2s} {hash:8s}".format(atom=atom_conf[0], hash=atom_conf[1]))

    return atoms_conf

def get_potcar_from_h5(potcarh5, atoms_conf, pottype):
    # print(potcarh5[pottype].keys())
    potcar_info = []
    if pottype in potcarh5.keys():
        for atom_conf in atoms_conf:
            if atom_conf[0] in potcarh5[pottype].keys():
                atom_rev = potcarh5[pottype + "/" + atom_conf[0]].keys()
                for i in atom_rev:
                    if i.startswith(atom_conf[1]):
                        log.info(pottype + '/' + atom_conf[0] + '/' + atom_conf[1] + " found")
                        dat = potcarh5[pottype + "/" + atom_conf[0] + "/" + i][()][0]
                        potcar_info.append(dat.decode("utf-8"))
            else:
                log.error("{atom:2s} not found in h5".format(atom=atom_conf[0]))
    else:
        log.error("{pottype} not found in h5 file".format(pottype=pottype))
    return potcar_info

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tool for creating POTCAR out of POSCAR information.')
    parser.add_argument('pottype', help='type of potential, either LDA or PBE', choices=['LDA', 'PBE'])
    parser.add_argument('poscar', nargs='?', help='POSCAR file name', metavar='POSCAR', default='POSCAR')
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
    # get POSCAR-file
    #
    if args.poscar is None:
        if os.path.isfile('POSCAR'):
            args.poscar = 'POSCAR'
        else:
            raise NameError("POSCAR not found")
    #
    # get POTCAR-file
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
    atoms_conf = get_atoms_configuration(args.poscar)
    potcar_info = get_potcar_from_h5(potcarh5, atoms_conf, args.pottype)

    potcar_file = open("POTCAR", "w")
    potcar_file.write(''.join(potcar_info))
    potcar_file.close()

    potcarh5.close()
