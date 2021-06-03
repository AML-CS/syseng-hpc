#!/bin/sh
#
# Setup and build WRFDA 4.0 as module
# Tested in Centos 7, Uninorte HPC
# Author: sjdonado@uninorte.edu.co
#

# Load dependencies
module load wrf/4.2.0

## Dir structure
export ROOT_DIR="/opt/ohpc/pub/WRFDA-4DVAR"
mkdir -p $ROOT_DIR/downloads
mkdir -p $ROOT_DIR/model

############################ WRFDA 4.0 ###################################
## Download and Build WRFDA/WRFPLUS
## Download and Build OBSPROC and GEN_BE
########################################################################

# Download WRFDA/WRFPLUS
cd $ROOT_DIR/downloads
wget -c https://www2.mmm.ucar.edu/wrf/src/WRFV4.0.TAR.gz
tar -xvzf $ROOT_DIR/downloads/WRFV4.0.TAR.gz -C $ROOT_DIR/model

cp -r $ROOT_DIR/model/WRF $ROOT_DIR/model/WRFPLUS
cp -r $ROOT_DIR/model/WRF $ROOT_DIR/model/WRFDA

# Compile WRFPLUS
cd $ROOT_DIR/model/WRFPLUS
./configure wrfplus # 18, gfortran and distributed memory
./compile wrf

echo "If compilation was successful, you should see the WRFPLUS executable"
ls -ls main/*.exe

export WRFPLUS_DIR=$ROOT_DIR/model/WRFPLUS

# Compile WRFDA
cd $ROOT_DIR/model/WRFDA
./clean
./configure 4dvar # 18, gfortran and distributed memory
./compile all_wrfvar >& compile.out

echo "Successful compilation will produce 44 executables: (including da_wrfvar.exe)"
ls -l var/build/*exe var/obsproc/src/obsproc.exe

export WRFDA_DIR=$ROOT_DIR/model/WRFDA

echo "Writting scripts..."
# TODO: git clone

echo "Writting modulefile..."

mkdir -p /opt/ohpc/pub/modulefiles/wrfda/
cat > /opt/ohpc/pub/modulefiles/wrfda/4.0 <<EOL
#%Module1.0#####################################################################

proc ModulesHelp { } {

        puts stderr " "
        puts stderr "This module loads WRFDA/WRFPLUS"
        puts stderr "\nVersion 4.0\n"

}

module-whatis "Name: wrfda/4.0"
module-whatis "Version: 4.0"
module-whatis "Category: utility, developer support"
module-whatis "Keywords: System, Utility"
module-whatis "The Weather Research and Forecasting (WRF) model"
module-whatis "URL https://www2.mmm.ucar.edu/wrf/users/download/get_sources.html#WRFDA"

set             version                 4.0

prepend-path    PATH                    /opt/ohpc/pub/syseng-hpc/scripts
setenv          WRFDA_ROOT_DIR          /opt/ohpc/pub/WRFDA-4DVAR
setenv          WRFDA_DIR               /opt/ohpc/pub/WRFDA-4DVAR/work_dir
setenv          OBSPROC_DIR		/opt/ohpc/pub/WRFDA-4DVAR/model/WRFDA/var/obsproc

set-alias	download-obs		"python3 /opt/ohpc/pub/syseng-hpc/scripts/download-obs.py"
set-alias	download-prep		"python3 /opt/ohpc/pub/syseng-hpc/scripts/download-prep.py"
set-alias	download-obs		"python3 /opt/ohpc/pub/syseng-hpc/scripts/download-obs.py"
set-alias	run-obsproc		"python3 /opt/ohpc/pub/syseng-hpc/scripts/run-obsproc.py"

EOL

echo "Setting permissions..."

chgrp -R syseng $ROOT_DIR
chmod -R 777 $ROOT_DIR

echo "DONE! WRFDA-4.0 installed successfully"
