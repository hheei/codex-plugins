#!/usr/bin/env python
import importlib
import sys
import os
try:
    h5py = importlib.import_module('h5py')
    numpy = importlib.import_module('numpy')
    argparse = importlib.import_module('argparse')
    log = importlib.import_module('logging')
except ImportError as error:
    print(str(error) + " found, exiting!")
    sys.exit(1)

try:
    git = importlib.import_module('git')
    git_commit_option = True
except ImportError as error:
    print(str(error) + " found, --git-commit option disables")
    git_commit_option = False


def getPOTCARs(directory):
    """returns a list of all subdirectories containing POTCAR files

    Parameters
    ----------
    directory: str
        Directory in which all directories are searched for POTCARs.

    Returns
    -------
    list
        a list of directories containing POTCAR files
    """
    potcars = []

    if (os.path.isdir(directory)):
        for item in os.listdir(directory):
            if os.path.exists(directory + '/' + item + '/POTCAR'):
                potcars.append(directory + '/' + item + '/POTCAR')
    else:
        raise IOError("Directory {dir} not found".format(dir=directory))
    # for root, dir, filenames in os.walk(directory):
    #     print(root, dir, filenames)
    #     for file in filenames:
    #         if "POTCAR" == file:
    #             potcars.append(root)
    return potcars

def dumpPOTCARs(h5file, potcars, git_commit_hash, omit_set_latest, attribute_text, compression_ratio):
    """writes POTCARS, supplied as list of directories containing POTCARS, to h5 file

    Parameters
    ----------
    h5file: str
        name of h5 file to be opened or created
    potcars: list of tuples
        list of tuples of strings containing directories containing POTCARs and their paths in h5 file
    git_commit_hash: str
        git commit hash
    omit_set_latest: bool
        decider whether latest soft link should be set to POTCARs in h5-file
    """
    try:
        potcarh5 = h5py.File(h5file, "a")
    except IOError as e:
        log.error(e)
        log.error('Could not open {h5file}, probably it is opened by another application?'.format(h5file=h5file))
        sys.exit(1)

    if ((attribute_text != '') and (len(attribute_text.split(':')) != 2)):
        log.warning('Could not set attribute :' + attribute_text)
        attribute_text = ''

    for potcar in potcars:
        dumpPOTCAR(potcarh5, potcar, git_commit_hash, omit_set_latest, attribute_text, compression_ratio)

    potcarh5.close()

def dumpPOTCAR(potcarh5, potcar, git_commit_hash, omit_set_latest, attribute_text, compression_ratio):
    """writes POTCARS, supplied as list of directories containing POTCARS, to h5 file

    Parameters
    ----------
    potcarh5: file
        file handle to alreay opened h5 file
    potcar: tuple of str
        tuple of string
            1. element: directory containing POTCAR
            2. element: path in h5 file
    git_commit_hash: str
        git commit hash
    omit_set_latest: bool
        decider whether latest soft link should be set to POTCARs in h5-file

    """
    potcar_path = potcar[0]

    if git_commit_option:
        if git_commit_hash == None:
            repo = git.Repo(potcar_path, search_parent_directories=True)
            git_commit_hash = repo.head.object.hexsha
    h5_path = potcar[1]
    pfile = open(potcar_path, "r")
    content = numpy.string_(pfile.read())
    length = len(content)
    pfile.close()
    str_content=content.decode('UTF-8')
    sha256 = (str_content[str_content.find("SHA256") + 10:str_content.find("SHA256") + 74])

    exists = h5_path+"/"+sha256 in potcarh5

    if exists:
        log.debug('{proc:9s} {potcar_name:19s}   sha: {sha}'.format(proc='exists:',
                                                                  potcar_name=h5_path,
                                                                  sha=sha256[0:12]))
        #
        # logic is reversed here, first appearance is latest, all other wont have the latest flag, therefore commented out
        # no update of information
        #
        #
        # update git commit only if no commit was set beforehand on existing potential
        #
        # if git_commit_hash is not None:
        #     old_commit = potcarh5[h5_path+"/"+sha256].attrs.get('git-commit')
        #     if old_commit is None:
        #         old_commit = 'None'
        #         log.info('{proc:9s} {potcar_name:19s}   sha: {sha}   git-commit: {old} --> {new}'.format(proc='update:',
        #                                                                                              potcar_name=h5_path,
        #                                                                                              sha=sha256[0:12],
        #                                                                                              old=old_commit[0:12],
        #                                                                                              new=git_commit_hash[0:12]))
        #         potcarh5[h5_path + "/" + sha256].attrs['git-commit'] = git_commit_hash
        #
        # update latest tag
        # if "/" + h5_path + "/latest" in potcarh5:
        #     old_sha256 = potcarh5["/" + h5_path].get("latest", getlink=True).path
        #     if old_sha256 != sha256:
        #         if not omit_set_latest:
        #             log.info('{proc:9s} {potcar_name:19s}   latest-tag: {old} --> {new}'.format(proc='update:',
        #                                                                                       potcar_name=h5_path,
        #                                                                                       sha=sha256[0:12],
        #                                                                                       old=old_sha256[0:12],
        #                                                                                       new=sha256[0:12]))
        #             # log.info('updating latest tag to ' + sha256)
        #             del potcarh5["/" + h5_path + "/latest"]
        #             potcarh5["/" + h5_path + "/latest"] = h5py.SoftLink(sha256)
        # else:
        #     if not omit_set_latest:
        #         potcarh5["/" + h5_path + "/latest"] = h5py.SoftLink(sha256)
        #         log.info('{proc:9s} {potcar_name:19s}   latest-tag: {new}'.format(proc='set:',
        #                                                                         potcar_name=h5_path,
        #                                                                         new=sha256[0:12]))

    else:
        dset = potcarh5.create_dataset(h5_path+"/"+sha256, (1,), chunks=True, data=content, compression="gzip",
                                       compression_opts=compression_ratio)
        if (attribute_text != ''):
            if (len(attribute_text.split(':')) == 2):
                attribute_data = attribute_text.split(':')
                dset.attrs[attribute_data[0]] = attribute_data[1]
            else:
                log.warning('Could not set attribute : "' + attribute_text + '"')
                attribute_text = ''

        if (sha256 != ''):
            dset.attrs['sha'] = sha256

        if git_commit_hash is not None:
            dset.attrs['git-commit'] = git_commit_hash

            if not omit_set_latest and not ("/" + h5_path + "/latest" in potcarh5):
                log.info('{proc:9s} {potcar_name:19s}   sha: {sha}   git-commit: {git}   setting latest'.format(proc='new:',
                                                                                                          potcar_name=h5_path,
                                                                                                          sha=sha256[0:12],
                                                                                                          git=git_commit_hash[0:12]))
            else:
                log.info('{proc:9s} {potcar_name:19s}   sha: {sha}   git-commit: {git}'.format(proc='new:',
                                                                                               potcar_name=h5_path,
                                                                                               sha=sha256[0:12],
                                                                                               git=git_commit_hash[0:12]))
        else:
            if not omit_set_latest and not ("/" + h5_path + "/latest" in potcarh5):
                log.info('{proc:9s}  {potcar_name:19s}   sha: {sha}   setting latest'.format(proc='new:',
                                                                                             potcar_name=h5_path,
                                                                                             sha=sha256[0:12]))
            else:
                log.info('{proc:9s}  {potcar_name:19s}   sha: {sha}'.format(proc='new:',
                                                                            potcar_name=h5_path,
                                                                            sha=sha256[0:12]))

        if not omit_set_latest:
            if not ("/" + h5_path + "/latest" in potcarh5):
                potcarh5["/"+h5_path+"/latest"] = h5py.SoftLink(sha256)
            # del potcarh5["/" + h5_path + "/latest"]
            # potcarh5["/"+h5_path+"/latest"] = h5py.SoftLink(sha256)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tool for creating POTCAR.h5 files. If no POTCAR and H5_PATH are specified, in the local directory "LDA" and "PBE" directories are looked for and all potentials in subdirectories there are processed.')
    parser.add_argument('potcar', metavar='POTCAR', nargs='?', help='POTCAR added to POTCAR.h5')
    parser.add_argument('h5path', metavar='H5_PATH', nargs='?', help='path on POTCAR.h5')
    parser.add_argument('--omit-set-latest', help='omit setting latest link to this potential', default=False, action='store_true')
    parser.add_argument('--git-commit-hash', metavar='GIT_COMMIT_HASH', nargs=1, help='git commit hash used as attribute in h5 file')
    parser.add_argument('--attribute-text', metavar='ATTRIBUTE_TEXT', nargs=1, help='attribute text for potentials in h5 file', default='')
    parser.add_argument('--compression-ratio', metavar='COMPRESSION_RATIO', help='compression ratio for h5 dataset compression. If turned on, you need to configure your hdf5 install with the "-with-zlib" option, so it can handle the decompression', default=0, type=int, choices=range(0,10))
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)5s: %(message)s", level=log.DEBUG)
        log.info("Verbose output!")
    else:
        log.basicConfig(format="%(levelname)5s: %(message)s", level=log.INFO)

    log.debug(args)

        # log.basicConfig(filename='test.log', level=logging.INFO, filemode='w')
        # log.debug(potcar)

    if args.potcar is None:
        try:
            potcar_paths = getPOTCARs("LDA")
            h5_paths = []
            for item in potcar_paths:
                h5_paths.append(item.replace('/POTCAR', ''))
            potcars = zip(potcar_paths, h5_paths)
            dumpPOTCARs("POTCAR.h5", potcars, args.git_commit_hash, args.omit_set_latest, args.attribute_text, args.compression_ratio)
        except Exception as e:
            log.info(e)
        try:
            potcar_paths = getPOTCARs("PBE")
            h5_paths = []
            for item in potcar_paths:
                h5_paths.append(item.replace('/POTCAR', ''))
            potcars = zip(potcar_paths, h5_paths)
            dumpPOTCARs("POTCAR.h5", potcars, args.git_commit_hash, args.omit_set_latest, args.attribute_text, args.compression_ratio)
        except Exception as e:
            log.info(e)
    else:
        try:
            potcar_path = args.potcar
            if os.path.isdir(potcar_path):
                if os.path.exists(potcar_path+'/POTCAR'):
                    potcar_path = potcar_path+'/POTCAR'
                else:
                    raise IOError('POTCAR in directory {dir} not found'.format(dir=potcar_path))
            else:
                if not os.path.exists(potcar_path):
                    raise IOError('{path} not found'.format(path=potcar_path))
            # if potcar_path.endswith('POTCAR'):
            #     potcar_path = potcar_path.replace('/POTCAR', '')
            if args.h5path is None:
                parser.error('--h5-path has to be set if single POTCAR is given')
            potcar = zip([potcar_path], [args.h5path])
            print(potcar)
            dumpPOTCARs("POTCAR.h5", potcar, args.git_commit_hash, args.omit_set_latest, args.attribute_text, args.compression_ratio)
        except IOError as e:
            log.error(e)
            log.error('exiting')
            sys.exit(1)
