#!/usr/bin/env bash
#
# Setup and build WRFDA 4.3 as module
# Tested in Centos 7, Uninorte HPC
# Author: sjdonado@uninorte.edu.co
#

# Load dependencies
module load gnu8/8.3.0 openmpi3/3.1.4 wrf/4.3

## Dir structure
export ROOT_DIR="/work/syseng/pub/WRFDA-4DVARV4.3"
mkdir -p $ROOT_DIR/downloads
mkdir -p $ROOT_DIR/model

############################ WRFDA 4.3 ###################################

# Unpack WRFPLUS + WRFDA
wget -c https://github.com/wrf-model/WRF/archive/refs/tags/v4.3.tar.gz -O $ROOT_DIR/downloads/WRF-4.3.tar.gz
tar -xvzf $ROOT_DIR/downloads/WRF-4.3.tar.gz -C $ROOT_DIR/model

cp -R $ROOT_DIR/model/WRF-4.3/ $ROOT_DIR/model/WRFPLUSV4
cp -R $ROOT_DIR/model/WRF-4.3/ $ROOT_DIR/model/WRFDA

# Setup WRFPLUS
cd $ROOT_DIR/model/WRFPLUSV4
./clean -a
./configure wrfplus # 18, gfortran and distributed memory
./compile wrfplus >& compile.out

echo "If compilation was successful, you should see the WRFPLUS executable"
ls -l main*.exe

if [ ! -f main/wrfplus.exe ]; then
    echo "wrfplus.exe not found"
    exit 1
fi

export WRFPLUS_DIR=$ROOT_DIR/model/WRFPLUSV4

# Setup WRFDA
cd $ROOT_DIR/model/WRFDA
./clean -a
./configure 4dvar # 18, gfortran and distributed memory
./compile all_wrfvar >& compile.out

echo "Successful compilation will produce 44 executables: (including da_wrfvar.exe)"
ls -l var/build/*exe var/obsproc/src/obsproc.exe

if [ ! -f  var/build/da_wrfvar.exe ]; then
    echo "da_wrfvar.exe not found"
    exit 1
fi

export WRFDA_DIR=$ROOT_DIR/model/WRFDA

echo "Creating work-dir and linking files..."

mkdir -p $ROOT_DIR/work-dir

ln -s $ROOT_DIR/model/WRFDA/var/build/da_wrfvar.exe $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/var/build/da_update_bc.exe $ROOT_DIR/work-dir

ln -s $ROOT_DIR/model/WRFDA/run/LANDUSE.TBL $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/run/GENPARM.TBL $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/run/SOILPARM.TBL $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/run/VEGPARM.TBL $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/run/RRTM_DATA_DBL $ROOT_DIR/work-dir/RRTM_DATA_DBL
ln -s $ROOT_DIR/model/WRFDA/run/RRTMG_LW_DATA $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/run/RRTMG_SW_DATA $ROOT_DIR/work-dir

ln -s $ROOT_DIR/model/WRFDA/run/ozone.formatted $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/run/ozone_lat.formatted $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/run/ozone_plev.formatted $ROOT_DIR/work-dir
ln -s $ROOT_DIR/model/WRFDA/var/test/update_bc/parame.in $ROOT_DIR/work-dir

echo "Writting modulefile..."

mkdir -p /opt/ohpc/pub/modulefiles/wrfda/
cat > /opt/ohpc/pub/modulefiles/wrfda/4.3 <<EOL
#%Module1.0#####################################################################

proc ModulesHelp { } {
    puts stderr " "
    puts stderr "This module loads WRFDA/WRFPLUS"
    puts stderr "\nVersion 4.3\n"
}

module-whatis "Name: wrfda/4.3"
module-whatis "Version: 4.3"
module-whatis "Category: utility, developer support"
module-whatis "Keywords: System, Utility"
module-whatis "The Weather Research and Forecasting (WRF) model"
module-whatis "URL https://www2.mmm.ucar.edu/wrf/users/download/get_sources.html#WRFDA"

set             version                 4.3

setenv          WRFDA_ROOT              $ROOT_DIR
setenv          WRFPLUS_DIR             $ROOT_DIR/model/WRFPLUSV4
setenv          WRFDA_DIR               $ROOT_DIR/work-dir
setenv          OBSPROC_DIR		        $ROOT_DIR/model/WRFDA/var/obsproc

set-alias	    download-obs		    "python3 /work/syseng/pub/syseng-hpc/scripts/download-obs.py"
set-alias	    download-prep		    "python3 /work/syseng/pub/syseng-hpc/scripts/download-prep.py"
set-alias	    download-obs		    "python3 /work/syseng/pub/syseng-hpc/scripts/download-obs.py"
set-alias	    run-obsproc		        "python3 /work/syseng/pub/syseng-hpc/scripts/run-obsproc.py"

EOL

echo "Setting permissions..."

chgrp -R syseng $ROOT_DIR
chmod -R 777 $ROOT_DIR

echo "WRFDA-4.3 installed successfully!"
