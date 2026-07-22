import numpy

def recover_original(vaspfile, path):
    content = {}
    try:
        filerecover = vaspfile[path]
        print filerecover
        content = filerecover['content'].value.tolist()
        #print(content)
        return content
    except:
        print("error reading ")

def write_recovered(content, filename, mode):
    with open(filename, mode) as outfile:
        for i in content:
            outfile.write(i)
            outfile.write("\n")
#
# INCAR
#
def read_incar(vaspfile, path):
    result = {}
    incar = vaspfile[path]
    for i in incar.keys():
        # decode numpy bytes (strings stored in HDF5 are retrieved as dtype bytes_)
        if type(incar[i].value) == numpy.bytes_:
            value = incar[i].value.decode()
        else:
            if "bool" in incar[i].attrs:
                if incar[i].attrs["bool"] == 1:
                    if incar[i].value == 1:
                        value = ".TRUE."
                    else:
                        value = ".FALSE."
            elif type(incar[i].value) is numpy.ndarray:
                numlist=incar[i].value.tolist()
                if type(numlist[1])==float:
                    value = ' '.join(['{:.2f}'.format(x) for x in incar[i].value.tolist()])
                elif type(numlist[1])==int:
                    value = ' '.join(['{:d}'.format(x) for x in incar[i].value.tolist()])
                else:
                    print "ERROR converting list in INCAR"
            else:
                value = incar[i].value
        result[i] = value
    return result

def write_incar(incar, filename, mode):
    with open(filename, mode) as outfile:
        for key, value in incar.items():
            outfile.write(" ".join([key.upper(), "=", str(value)]))
            outfile.write("\n")

#
# KPOINTS
#
def read_kpoints(vaspfile, path):
    result = {}
    kpoints = vaspfile[path + "/"]
    for key, value in kpoints.iteritems():
        result[key] = value[()]
    return result


def write_kpoints(kpoints, filename, mode):
    with open(filename, mode) as outfile:
        # general info
        outfile.write("{}\n".format(kpoints['sznamk']))
        outfile.write("{:3d}\n".format(kpoints['number_kpoints']))
        # depending on user supplied kpoints input configuration generate output
        # Monkhorst-Pack
        if (kpoints['mode'][0].lower() == 'm'):
            outfile.write("{}\n".format(kpoints['mode']))
            outfile.write("{:3d}{:3d}{:3d}\n".format(kpoints['nkpx'], kpoints['nkpy'], kpoints['nkpz']))
            try:
                outfile.write("{0[shift][0]:f} {0[shift][1]:f} {0[shift][2]:f}\n".format(kpoints))
            except:
                pass
        # Gamma
        elif (kpoints['mode'][0].lower() == 'g'):
            outfile.write("{}\n".format(kpoints['mode']))
            outfile.write("{:3d}{:3d}{:3d}\n".format(kpoints['nkpx'], kpoints['nkpy'], kpoints['nkpz']))
            try:
                outfile.write("{0[shift][0]:f} {0[shift][1]:f} {0[shift][2]:f}\n".format(kpoints))
            except:
                pass

        # Line-mode
        elif (kpoints['mode'][0].lower() == 'l'):
            outfile.write("{}\n".format(kpoints['mode']))
            outfile.write("{}\n".format(kpoints['coordinate_space']))
            for coord in kpoints['coordinates_kpoints']:
                outfile.write("{0[0]:f} {0[1]:f} {0[2]:f}\n".format(coord))
        # Explicit kpoints given + tetrahedron mode
        elif (kpoints['mode'][0].lower() == 'e'):
            outfile.write("{}\n".format(kpoints['coordinate_space']))
            for i in range(kpoints['coordinates_kpoints'].shape[0]):
                outfile.write("{0[0]:f} {0[1]:f} {0[2]:f} {1:f}\n".format(kpoints['coordinates_kpoints'][i],kpoints['weights_kpoints'][i]))
            try:
                numtet = kpoints['number_tetrahedras']
                outfile.write("{}\n".format('Tetrahedra'))
                outfile.write("{:d}   {:.12f}\n".format(kpoints['number_tetrahedras'], kpoints['volume_weight_tetrahedra']))
                for i in range(numtet):
                    print(kpoints['coordinate_id_tetrahedra'][i][0])
                    outfile.write("{0[0]:d}     {0[1]:d} {0[2]:d} {0[3]:d} {0[4]:d}\n".format(kpoints['coordinate_id_tetrahedra'][i]))
            except:
                pass
        # Automatic
        elif (kpoints['mode'][0].lower() == 'a'):
            outfile.write("{}\n".format(kpoints['mode']))
            outfile.write(" {:f}\n".format(kpoints['rk_length']))
        # Basis vectors
        elif (kpoints['mode'][0].lower() == 'b'):
            outfile.write("{}\n".format(kpoints['coordinate_space']))
            for coord in kpoints['basis_vectors']:
                outfile.write("{0[0]:f} {0[1]:f} {0[2]:f}\n".format(coord))
            try:
                outfile.write("{0[shift][0]:f} {0[shift][1]:f} {0[shift][2]:f}\n".format(kpoints))
            except:
                pass
#
# POSCAR
#
def read_poscar(vaspfile, path):
    result = {}
    poscar = vaspfile[path + "/"]
    for key, value in poscar.iteritems():
        result[key] = value[()]
    return result

def write_poscar(poscar, filename, mode):
    with open(filename, mode) as outfile:
#        for key, value in poscar.iteritems():
#            print(key, value)
#        print(poscar)
        outfile.write("{}\n".format(poscar['sznam']))
        try:
            outfile.write(" {:f}\n".format(poscar['scale']))
        except:
            if (poscar['scale_x'] == poscar['scale_y'] and poscar['scale_x'] == poscar['scale_z']):
                outfile.write(" {:f}\n".format(poscar['scale_x']))
            else:
                outfile.write(" {:f} {:f} {:f}\n".format(poscar['scale_x'], poscar['scale_y'], poscar['scale_z']))
        for vec in poscar['lattice_vectors']:
            outfile.write("  {0[0]:21.16f} {0[1]:21.16f} {0[2]:21.16f}\n".format(vec))
        try:
            atom_def = []
            for k in range(len(poscar['ion_types'])):
                if (poscar['ion_sha256'][k]) != '':
                    atom_def.append(poscar['ion_types'][k] + '/'  + poscar['ion_sha256'][k])
                else:
                    atom_def.append(poscar['ion_types'][k])
            outfile.write(''.join("   {}".format(k) for k in atom_def) + '\n')
        except:
            pass
        outfile.write(''.join("{:6d}".format(k) for k in poscar['number_ion_types']) + '\n')
        if (poscar['selective_dynamics'] == 1):
            outfile.write('Selective dynamcis\n')
        if (poscar['direct_coordinates'] == 1) :
            outfile.write('Direct\n')
        else:
            outfile.write('Cartesian\n')
        if (poscar['selective_dynamics'] == 1):
            for i in range(poscar['position_ions'].shape[0]):
                pos = poscar['position_ions'][i]
                seldyn = []
                for j in poscar['selective_dynamics_ions'][i]:
                    if (j == 0):
                        seldyn.append("F")
                    else:
                        seldyn.append("T")
                outfile.write(" {0[0]:19.16f} {0[1]:19.16f} {0[2]:19.16f}   {1[0]}   {1[1]}   {1[2]}\n".format(pos, seldyn))
        else:
            for pos in poscar['position_ions']:
                outfile.write(" {0[0]:19.16f} {0[1]:19.16f} {0[2]:19.16f}\n".format(pos))
        # lattice velocities
        try:
            lattvec = poscar['lattice_velocities']
            outfile.write('Lattice velocities\n')
            for vel in lattvel:
                outfile.write(" {0[0]:19.16f} {0[1]:19.16f} {0[2]:19.16f}\n".format(vel))
        except:
            pass
        # empty spheres
        try:
            outfile.write('Empty spheres\n' + ''.join("{:6d}".format(k) for k in poscar['number_empty_sphere_types']) + '\n')
            for pos in poscar['position_empty_spheres']:
                outfile.write(" {0[0]:19.16f} {0[1]:19.16f} {0[2]:19.16f}\n".format(pos))
        except:
            pass
        # velocities
        try:
            velocities = poscar['ion_velocities']
            if (poscar['direct_coordinates_velocities'] == 1):
                outfile.write('Direct\n')
            else:
                outfile.write('Cartesian\n')
            for vel in velocities:
                outfile.write(" {0[0]:15.8e} {0[1]:15.8e} {0[2]:15.8e}\n".format(vel))

        except:
            pass
        #predictor coordinates
        try:
            outfile.write(' \n           1\n' + "{:21.17f}\n".format(poscar['potim']))
            outfile.write(''.join("{:16.8e}".format(k) for k in poscar['nose_thermostat']) + '\n')
            for pos in poscar['predictor_coordinates']:
                outfile.write("{0[0]:16.8e}{0[1]:16.8e}{0[2]:16.8e}\n".format(pos))
            for pos in poscar['predictor_coordinates_2']:
                outfile.write("{0[0]:16.8e}{0[1]:16.8e}{0[2]:16.8e}\n".format(pos))
            for pos in poscar['predictor_coordinates_3']:
                outfile.write("{0[0]:16.8e}{0[1]:16.8e}{0[2]:16.8e}\n".format(pos))
        except:
            pass
#
# XDATCAR
#
def read_xdatcar(vaspfile, path):
    result = []
    xdatcar = vaspfile[path + "/"]
    for group in xdatcar:
        step = vaspfile[path + "/" + group + "/positions/"]
        stepresult = {}
        for key, value in step.iteritems():
            stepresult[key] = value[()]
        result.append((group, stepresult))
    return result

def write_xdatcar(xdatcardir, filename, mode):
    with open(filename, mode) as outfile:
        xdatcardir.sort(key=lambda tup: int(tup[0]))

        for item in xdatcardir:
            xdatcar = item[1]
            try:
                outfile.write("{}\n".format(xdatcar['sznam']))
                outfile.write(" {:d}\n".format(int(xdatcar['scale'])))
                for vec in xdatcar['lattice_vectors']:
                    outfile.write(" {0[0]:12.6f} {0[1]:12.6f} {0[2]:12.6f}\n".format(vec))
                try:
                    outfile.write(''.join("    {}".format(k) for k in xdatcar['ion_types']) + '\n')
                except:
                    pass
                outfile.write(''.join("{:4d}".format(k) for k in xdatcar['number_ion_types']) + '\n')
            except:
                pass
            outfile.write('Direct configuration=      ' + item[0] + '\n')
            for pos in xdatcar['position_ions']:
                outfile.write(" {0[0]:12.8f} {0[1]:12.8f} {0[2]:12.8f}\n".format(pos))
#
# DOSCAR
#
def read_dos(vaspfile, path):
    result = {}
    result['anorm'] = vaspfile[path + "/anorm"][...]
    result['aomega'] = vaspfile[path + "/aomega"][()]
    result['nions'] = vaspfile[path + "/nions"][()]
    result['potim'] = vaspfile[path + "/potim"][()]
    result['sznam1'] = vaspfile[path + "/sznam1"][()]
    result['temperature'] = vaspfile[path + "/temperature"][()]
    result['jobpar'] = vaspfile[path + "/jobpar"][()]
    result['lpar'] = vaspfile[path + "/lpar"][()]

    ##
    result['dos'] = vaspfile[path + "/dos"][...]
    result['dosi'] = vaspfile[path + "/dosi"][...]
    result['dospar'] = vaspfile[path + "/dospar"][...]
    result['efermi'] = vaspfile[path + "/efermi"][()]
    result['emax'] = vaspfile[path + "/emax"][()]
    result['emin'] = vaspfile[path + "/emin"][()]
    result['ncdij'] = vaspfile[path + "/ncdij"][()]
    result['nedos'] = vaspfile[path + "/nedos"][()]
    result['nionp'] = vaspfile[path + "/nionp"][()]
    return result

def write_dos(dos, filename, mode):
    with open(filename, mode) as outfile:
        outfile.write("{0[nionp]:4d}{0[nions]:4d}{0[jobpar]:4d}{0[ncdij]:4d}".format(dos))
        outfile.write("\n")
        outfile.write("{0[aomega]:15.7e}".format(dos))
        outfile.write(''.join("{:15.7e}".format(k) for k in dos['anorm']))
        outfile.write("{0[potim]:15.7e}".format(dos))
        outfile.write("\n")
        outfile.write("{0[temperature]:15.7e}\n".format(dos))
        outfile.write(" CAR\n")
        outfile.write("{}\n".format(dos['sznam1'].decode('US-ASCII')))

        outfile.write("{0[emax]:16.8f}{0[emin]:16.8f}{0[nedos]:5d}{0[efermi]:16.8f}{1:16.8f}\n".format(dos,1.0))
        deltae = (dos['emax'] - dos['emin'])/(dos['nedos'] - 1)
        for i in range(0, dos['nedos']):
            en = dos['emin'] + deltae*i
            doses = dos['dos'][:,i]
            dosies = dos['dosi'][:,i]
            outfile.write("   {0:8.3f}".format(en))
            outfile.write(''.join("{:16.8e}".format(k) for k in doses))
            outfile.write(''.join("{:16.8e}".format(k) for k in dosies))
            outfile.write("\n")

        if dos['lpar'] >= -1:
            for n in range(0, dos['nionp']):
                outfile.write("{0[emax]:16.8f}{0[emin]:16.8f}{0[nedos]:5d}{0[efermi]:16.8f}{1:16.8f}\n".format(dos,1.0))
                for i in range(0, dos['nedos']):
                    en = dos['emin'] + deltae*i
                    output = []
                    for lpro in range(0, dos['lpar']):
                        for spin in range(0, dos['ncdij']):
                            output.append(dos['dospar'][spin,n,lpro,i])

                    outfile.write("   {0:8.3f}".format(en))
                    outfile.write(''.join("{:16.8e}".format(k) for k in output))
                    outfile.write("\n")

#
# EIGENVAL
#
def read_eigenvalues(vaspfile, path):
    result = {}
    result['anorm'] = vaspfile[path + "/anorm"][...]
    result['aomega'] = vaspfile[path + "/aomega"][()]
    result['ispin'] = vaspfile[path + "/ispin"][()]
    result['kpoints'] = vaspfile[path + "/kpoints"][()]
    result['nb_tot'] = vaspfile[path + "/nb_tot"][()]
    result['nblocks'] = vaspfile[path + "/nblocks"][()]
    result['nelectrons'] = vaspfile[path + "/nelectrons"][()]
    result['nions'] = vaspfile[path + "/nions"][()]
    result['potim'] = vaspfile[path + "/potim"][()]
    result['sznam1'] = vaspfile[path + "/sznam1"][()]
    result['temperature'] = vaspfile[path + "/temperature"][()]
    ##
    result['eigenvalues'] = vaspfile[path + "/eigenvalues"][...]
    result['fermiweights'] = vaspfile[path + "/fermiweights"][...]
    result['kpoint_coords'] = vaspfile[path + "/kpoint_coords"][...]
    result['kpoints_symmetry_weight'] = vaspfile[path + "/kpoints_symmetry_weight"][...]
    return result


def write_eigenvalues(eigenval, filename, mode):
    with open(filename, mode) as outfile:
        outfile.write("{0[nions]:5d}{0[nions]:5d}{0[nblocks]:5d}{0[ispin]:5d}".format(eigenval))
        outfile.write("\n")
        outfile.write("{0[aomega]:15.7e}".format(eigenval))
        outfile.write(''.join("{:15.7e}".format(k) for k in eigenval['anorm']))
        outfile.write("{0[potim]:15.7e}".format(eigenval))
        outfile.write("\n")
        outfile.write("{0[temperature]:15.7e}\n".format(eigenval))
        outfile.write(" CAR\n")
        outfile.write("{}\n".format(eigenval['sznam1'].decode('US-ASCII')))
        outfile.write("{1:7d}{0[kpoints]:7d}{0[nb_tot]:7d}\n".format(eigenval, int(eigenval['nelectrons'])))

        for k in range(0, eigenval['kpoints']):
            kcoord = eigenval['kpoint_coords'][k][:]
            outfile.write('\n' + ''.join("{:15.7e}".format(k) for k in kcoord))
            outfile.write("{:15.7e}".format(eigenval['kpoints_symmetry_weight'][k]) + '\n')
            for i in range(0, eigenval['nb_tot']):
                if (eigenval['ispin'] == 1):
                    eigval = eigenval['eigenvalues'][0][k][i]
                    weights = eigenval['fermiweights'][0][k][i]
                    outfile.write(" {:4d}    {:12.6f}  {:9.6f}\n".format(i+1,eigval, weights))
                else:
                    eigval1 = eigenval['eigenvalues'][0][k][i]
                    eigval2 = eigenval['eigenvalues'][1][k][i]
                    weights1 = eigenval['fermiweights'][0][k][i]
                    weights = eigenval['fermiweights'][1][k][i]
                    outfile.write(" {:4d}    {:12.6f}  {:12.6f}  {:9.6f}  {:9.6f}\n".format(i+1,eigval, weights))
