#!/usr/bin/env python
import h5py
import sys, os

sys.path.append(os.path.dirname(__file__))
import vasph5

def print_header(headertxt):
    print("==============================================================")
    print("{}".format(headertxt))
    print("")

if __name__ == "__main__":
    vaspout = h5py.File('vaspout.h5','r')

    outfile = "INCAR.extracted"
    print("Generating INCAR")
    incardict = vasph5.read_incar(vaspout, "/input/incar")
    vasph5.write_incar(incardict, outfile, "w")

    outfile = "KPOINTS.extracted"
    print("Generating KPOINTS")
    kpointsdict = vasph5.read_kpoints(vaspout, "/input/kpoints")
    vasph5.write_kpoints(kpointsdict, outfile, "w")

    outfile = "POSCAR.extracted"
    print("Generating POSCAR")
    poscardict = vasph5.read_poscar(vaspout, "input/poscar")
    vasph5.write_poscar(poscardict, outfile, "w")

    outfile = "INCAR.orig"
    print("Recover INCAR")
    content = vasph5.recover_original(vaspout, "/original/incar")
    if content:
        vasph5.write_recovered(content, outfile, "w")

    outfile = "KPOINTS.orig"
    print("Recover KPOINTS")
    content = vasph5.recover_original(vaspout, "/original/kpoints")
    if content:
        vasph5.write_recovered(content, outfile, "w")

    outfile = "POSCAR.orig"
    print("Recover POSCAR")
    content = vasph5.recover_original(vaspout, "/original/poscar")
    if content:
        vasph5.write_recovered(content, outfile, "w")

    outfile = "POTCAR.orig"
    print("Recover POTCAR")
    content = vasph5.recover_original(vaspout, "/input/potcar")
    if content:
        vasph5.write_recovered(content, outfile, "w")

    # outfile = "pyout-xdatcar.txt"
    # print("Generating XDATCAR --> " + outfile)
    # xdatcardict = vasph5.read_xdatcar(vaspout, "intermediate")
    # vasph5.write_xdatcar(xdatcardict, outfile, "w")
    #
    # outfile = "pyout-eigenval.txt"
    # print("Generating EIGENVAL --> " + outfile)
    # evaldict = vasph5.read_eigenvalues(vaspout, "/results/eigenvalues")
    # vasph5.write_eigenvalues(evaldict, outfile, 'w+')
    #
    # outfile = "pyout-doscar.txt"
    # print("Generating DOSCAR --> " + outfile)
    # dosdict = vasph5.read_dos(vaspout, "/results/dos")
    # vasph5.write_dos(dosdict, outfile, 'w+')
    #
    # outfile = "pyout-contcar.txt"
    # print("Generating CONTCAR --> " + outfile)
    # contcardict = vasph5.read_poscar(vaspout, "results/positions")
    # vasph5.write_poscar(contcardict, outfile, "w")
    #
