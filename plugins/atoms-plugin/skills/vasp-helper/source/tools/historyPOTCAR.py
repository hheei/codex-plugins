#!/usr/bin/env python
import importlib
import sys
import os

#sys.path.append("../../repositories/utils/python/")
#sys.path.append("/fs/home/wahl/repositories/vasp/tools/")
import vasp_potcarh5

try:
    h5py = importlib.import_module('h5py')
    numpy = importlib.import_module('numpy')
    argparse = importlib.import_module('argparse')
    log = importlib.import_module('logging')
    git = importlib.import_module('git')
    Repo = git.Repo
except ImportError as error:
    print(str(error) + " found, exiting!")
    sys.exit(1)

def deleteDirectory(dirName):
    if (os.path.isdir(dirName)):
        log.info("deleting directory {path}".format(path=dirName))
        for root, dirs, files in os.walk(dirName, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(dirName)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tool for creating historic POTCAR.h5 files.')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('--compression-ratio', metavar='COMPRESSION_RATIO', help='compression ratio for h5 dataset compression', default=0, type=int, choices=range(0,10))
    parser.add_argument('file', help='history data file')

    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)5s: %(message)s", level=log.DEBUG)
        log.info("Verbose output!")
    else:
        log.basicConfig(format="%(levelname)5s: %(message)s", level=log.INFO)

    historyfilename = args.file
    tmpdir = 'tmp'
    potcarh5 = 'POTCAR.h5'
    historyfile = open(historyfilename, 'r')
    omit_set_latest = False

    content = historyfile.readlines()
    lines = []
    for line in content:
        row = line.split()
        lines.append(row)
    # create temporary git directory
    deleteDirectory(tmpdir)
    os.makedirs(tmpdir)

    for line in lines:
        git_dir = line[0]
        git_dir_name = os.path.split(git_dir)[-1]
        tmp_git_dir = tmpdir+'/'+git_dir_name
        h5_main_path = line[1]
        git_commit_hash = line[2]
        if len(line) == 4:
            attribute_text = line[3]
            print(attribute_text)
        else:
            attribute_text = ''

        if not os.path.exists(tmp_git_dir):
            log.info('Cloning repository '+git_dir)
            Repo.clone_from(git_dir, tmp_git_dir)
        else:
            log.debug('Repository exists  '+git_dir_name)
        repo = Repo(tmp_git_dir)
        assert not repo.bare
        git = repo.git
        log.info('')
        log.info('checking out repository: ' + git_commit_hash)
        try:
            git.checkout(git_commit_hash)
        except:
            log.error('Could not checkout branch with hash: ' + git_commit_hash)
            deleteDirectory(tmpdir)
            log.error('Stopping')
            sys.exit(1)

        log.debug('temporary git directory: {dir}'.format(dir=tmp_git_dir))
        potcar_paths = vasp_potcarh5.getPOTCARs(tmp_git_dir)
        # print(potcar_paths)
        h5_paths = []
        for line in potcar_paths:
            pot_dir_name = os.path.split(line.replace('/POTCAR', ''))[-1]
            h5_paths.append(h5_main_path + '/' + pot_dir_name)
        potcars = zip(potcar_paths, h5_paths)

        vasp_potcarh5.dumpPOTCARs(potcarh5, potcars, git_commit_hash, omit_set_latest, attribute_text, args.compression_ratio)

    deleteDirectory(tmpdir)
