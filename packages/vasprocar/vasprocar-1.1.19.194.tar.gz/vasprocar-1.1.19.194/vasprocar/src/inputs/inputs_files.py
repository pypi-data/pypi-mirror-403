# VASProcar Copyright (C) 2023
# GNU GPL-3.0 license

print("#######################################################")
print("################ input Files Generator ################")
print("#######################################################")
print(" ")

print("#######################################################")
print("# Which input file do you want?                      ##")
print("#######################################################")
print("# [1]  All input files                               ##")
print("# [2]  Bands (Plot 2D)                               ##")
print("# [3]  Projection of Spin components                 ##")
print("# [4]  Projection of Orbitals                        ##")
print("# [5]  Projection of the REGIONS (Location)          ##")
print("# [6]  DOS                                           ##")
print("# [7]  Electrostatic Potential in X,Y,Z direction    ##")
print("# [8]  CHGCAR file analysis                          ##")
print("# [9]  Spin Texture - Contour Video                  ##")
print("# [10] Spin Texture - Video                          ##")
print("# ================================================== ##")
print("# [0] Return to the main menu                        ##")
print("#######################################################")
tipo = input (" "); tipo = int(tipo)
print(" ")

if (tipo == 0): execute_python_file(filename = '_settings.py')

# ------------------------------------------------------------------------------
# Checking if the "inputs" folder exists, if it does not exist it is created ---
# ------------------------------------------------------------------------------
if os.path.isdir(dir_files + '/inputs'):
    0 == 0
else:
    os.mkdir(dir_files + '/inputs')
# ---------------------------------

#----------------------------------------------------------------------
# Copy [input files] to the input folder directory --------------------
#----------------------------------------------------------------------

if (tipo == 2 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.bands'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.bands')
   except: 0 == 0
   #--------------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.bands'
   destination = dir_files + '/inputs/input.vasprocar.bands'
   shutil.copyfile(source, destination)

if (tipo == 3 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.spin'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.spin')
   except: 0 == 0
   #------------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.spin'
   destination = dir_files + '/inputs/input.vasprocar.spin'
   shutil.copyfile(source, destination)

if (tipo == 4 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.orbitals'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.orbitals')
   except: 0 == 0
   #----------------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.orbitals'
   destination = dir_files + '/inputs/input.vasprocar.orbitals'
   shutil.copyfile(source, destination)

if (tipo == 5 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.location'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.location')
   except: 0 == 0
   #----------------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.location'
   destination = dir_files + '/inputs/input.vasprocar.location'
   shutil.copyfile(source, destination)

if (tipo == 6 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.dos'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.dos')
   except: 0 == 0
   #-----------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.dos'
   destination = dir_files + '/inputs/input.vasprocar.dos'
   shutil.copyfile(source, destination)

if (tipo == 7 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.locpot'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.locpot')
   except: 0 == 0
   #--------------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.locpot'
   destination = dir_files + '/inputs/input.vasprocar.locpot'
   shutil.copyfile(source, destination)

if (tipo == 8 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.chgcar'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.chgcar')
   except: 0 == 0
   #--------------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.chgcar'
   destination = dir_files + '/inputs/input.vasprocar.chgcar'
   shutil.copyfile(source, destination)

if (tipo == 9 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.spin_video'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.spin_video')
   except: 0 == 0
   #------------------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.spin_video'
   destination = dir_files + '/inputs/input.vasprocar.spin_video'
   shutil.copyfile(source, destination)

if (tipo == 10 or tipo == 1):
   try: f = open(dir_files + '/inputs/input.vasprocar.fermi_surface'); f.close(); os.remove(dir_files + '/inputs/input.vasprocar.fermi_surface')
   except: 0 == 0
   #---------------------------------------------------------
   source = main_dir + 'inputs/input.vasprocar.fermi_surface'
   destination = dir_files + '/inputs/input.vasprocar.fermi_surface'
   shutil.copyfile(source, destination)

#-----------------------------------------------------------------
print(" ")
print("======================= Completed =======================")
print(" ")
#-----------------------------------------------------------------

#=======================================================================
# User option to perform another calculation or finished the code ======
#=======================================================================
if (len(inputs) == 0):
   execute_python_file(filename = '_loop.py')
