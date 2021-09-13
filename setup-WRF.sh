#!/usr/bin/env bash
#
# Setup and build WRF 4.3 as module
# Tested in Centos 7, Uninorte HPC
# Author: sjdonado@uninorte.edu.co
#

# Install and update low level dependencies
# sudo yum -y update
# sudo yum -y upgrade

# (not required if exists gnu8 module)
# sudo yum -y install wget gcc gcc-gfortran libtool automake autoconf make m4 java-11-openjdk csh

module purge
module load autotools ohpc gnu8/8.3.0 cmake/3.15.4

# sudo yum-config-manager --enable epel
# sudo yum -y install libgfortran5 mesa-libGL-devel

## Dir structure
export ROOT_DIR="/work/syseng/pub/WRFV4.3"
mkdir -p $ROOT_DIR/downloads
mkdir -p $ROOT_DIR/model
mkdir -p $ROOT_DIR/data

## Download dependencies
cd $ROOT_DIR/downloads
# wget -c http://cola.gmu.edu/grads/2.2/grads-2.2.0-bin-centos7.3-x86_64.tar.gz
# wget -c https://www.zlib.net/zlib-1.2.11.tar.gz
# wget -c https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.12/hdf5-1.12.1/src/hdf5-1.12.1.tar.gz
# wget -c https://github.com/Unidata/netcdf-c/archive/refs/tags/v4.8.1.tar.gz -O netcdf-c-4.8.1.tar.gz
# wget -c https://github.com/Unidata/netcdf-fortran/archive/refs/tags/v4.5.3.tar.gz -O netcdf-fortran-4.5.3.tar.gz
# wget -c https://download.sourceforge.net/libpng/libpng-1.6.37.tar.gz
# wget -c https://github.com/jasper-software/jasper/archive/refs/tags/version-2.0.33.tar.gz -O jasper-version-2.0.33.tar.gz
# wget -c https://github.com/wrf-model/WRF/archive/refs/tags/v4.3.tar.gz -O WRF-4.3.tar.gz
# wget -c https://github.com/wrf-model/WPS/archive/refs/tags/v4.3.tar.gz -O WPS-4.3.tar.gz

# Compilers env flags
export DIR=$ROOT_DIR/library
export CC=gcc
export CXX=g++
export FC=gfortran
export F77=gfortran
# export WRFIO_NCD_LARGE_FILE_SUPPORT=1
# export J="-j 1"

# Setup zlib 1.2.11
tar -xvzf $ROOT_DIR/downloads/zlib-1.2.11.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/zlib-1.2.11/
./configure --prefix=$DIR
make
make install

export ZLIB=$DIR

# Installing HDF5 1.12.1
tar -xvzf $ROOT_DIR/downloads/hdf5-1.12.1.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/hdf5-1.12.1
./configure --prefix=$DIR --with-zlib=$DIR --enable-hl --enable-fortran
make
make install

export HDF5=$DIR

export LD_LIBRARY_PATH=$DIR/lib
export LDFLAGS=-L$DIR/lib
export CPPFLAGS=-I$DIR/include

# Installing netcdf-c-4.8.1
tar -xvzf $ROOT_DIR/downloads/netcdf-c-4.8.1.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/netcdf-c-4.8.1
./configure --prefix=$DIR
make check
make install

export LIBS="-lnetcdf -lhdf5_hl -lhdf5 -lz"

# Installing netcdf-fortran-4.5.3
tar -xvzf $ROOT_DIR/downloads/netcdf-fortran-4.5.3.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/netcdf-fortran-4.5.3
./configure --prefix=$DIR
make check
make install

export NETCDF=$DIR
export PATH=$DIR/bin:$PATH

############################ WRF 4.3 ###################################

# Setup WRF-4.3
tar -xvzf $ROOT_DIR/downloads/WRF-4.3.tar.gz -C $ROOT_DIR/model
cd $ROOT_DIR/model/WRF-4.3
./clean -a
./configure # 34, 1 for gfortran and distributed memory

./compile em_real >& compile.out

echo "If compilation was successful, you should see wrf.exe"
ls -l main/*.exe
if [ ! -f main/wrf.exe ]; then
    echo "wrf.exe not found"
    exit 1
fi

export WRF_DIR=$ROOT_DIR/model/WRF-4.3

exit 0

############################ WPS 4.3 ###################################

# Setup libpng-1.6.37
tar -xvzf $ROOT_DIR/downloads/libpng-1.6.37.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/libpng-1.6.37
./configure --prefix=$DIR
make
make install

# Setup jasper-version-2.0.33
tar -xvzf $ROOT_DIR/downloads/jasper-version-2.0.33.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/jasper-version-2.0.33
export JASPER_BUILD_DIR=$ROOT_DIR/downloads/jasper-version-2.0.33-build
mkdir -p $JASPER_BUILD_DIR
cmake -G "Unix Makefiles" -H$(pwd) -B$JASPER_BUILD_DIR -DCMAKE_INSTALL_PREFIX=$DIR
cd $JASPER_BUILD_DIR
make clean all
make test
make install
mv $DIR/lib64/* $DIR/lib
rmdir $DIR/lib64

export JASPERLIB=$DIR/lib
export JASPERINC=$DIR/include

# Setup WPSV4.3
tar -xvzf $ROOT_DIR/downloads/WPS-4.3.tar.gz -C $ROOT_DIR/model
cd $ROOT_DIR/model/WPS-4.3
./clean
./configure # 3
./compile >& compile.out

echo "If compilation was successful, you should see geogrid.exe, metgrid.exe and ungrib.exe"
ls -l *.exe
if [ ! -f geogrid.exe ] || [ ! -f metgrid.exe ] || [ ! -f ungrib.exe ]; then
    echo "geogrid.exe, metgrid.exe or ungrib.exe not found"
    exit 1
fi

######################## Post-Processing Tools ####################

# Setup Grads 2.2.0
tar -xvzf $ROOT_DIR/downloads/grads-2.2.0-bin-centos7.3-x86_64.tar.gz -C $ROOT_DIR/downloads
mv $ROOT_DIR/downloads/grads-2.2.0/bin/* $DIR/bin
mv $ROOT_DIR/downloads/grads-2.2.0/lib/* $DIR/lib

# Setup ARWpost
cd $ROOT_DIR/downloads
wget -c http://www2.mmm.ucar.edu/wrf/src/ARWpost_V3.tar.gz
tar -xvzf $ROOT_DIR/downloads/ARWpost_V3.tar.gz -C $ROOT_DIR/model
cd $ROOT_DIR/model/ARWpost
./clean
sed -i -e 's/-lnetcdf/-lnetcdff -lnetcdf/g' $ROOT_DIR/model/ARWpost/src/Makefile
./configure # 3
sed -i -e 's/-C -P/-P/g' $ROOT_DIR/model/ARWpost/configure.arwp
./compile

######################## Model Setup Tools ########################

# Setup DomainWizard
cd $ROOT_DIR/downloads
wget -c http://esrl.noaa.gov/gsd/wrfportal/domainwizard/WRFDomainWizard.zip
mkdir $ROOT_DIR/model/WRFDomainWizard
unzip $ROOT_DIR/downloads/WRFDomainWizard.zip -d $ROOT_DIR/model/WRFDomainWizard
chmod +x $ROOT_DIR/model/WRFDomainWizard/run_DomainWizard

echo "Adding scripts to PATH..."
export PATH=/work/syseng/pub/syseng-hpc/scripts:$PATH

echo "Writting modulefile..."

mkdir -p /opt/ohpc/pub/modulefiles/wrf/
cat > /opt/ohpc/pub/modulefiles/wrf/4.3  <<EOL
#%Module1.0#####################################################################

proc ModulesHelp { } {
    puts stderr " "
    puts stderr "This module loads WRF-4.3 and dependencies"
    puts stderr "\nVersion 4.3\n"
}

module-whatis "Name: wrf/4.3"
module-whatis "Version: 4.3"
module-whatis "Category: utility, developer support"
module-whatis "Keywords: System, Utility"
module-whatis "The Weather Research and Forecasting (WRF) model"
module-whatis "URL https://github.com/wrf-model/WRF"

set             version                 4.3

prepend-path    PATH                    $PATH
prepend-path    LD_LIBRARY_PATH         $LD_LIBRARY_PATH

setenv          CC                      gcc
setenv          CXX                     g++
setenv          FC                      gfortran
setenv          F77                     gfortran

setenv          HDF5                    $ROOT_DIR/library

setenv          CPPFLAGS                -I$ROOT_DIR/library/include
setenv          LDFLAGS                 -L$ROOT_DIR/library/lib

setenv          NETCDF                  $ROOT_DIR/library

setenv          LIBS                    -lnetcdf -lhdf5_hl -lhdf5 -lz

setenv          JASPERLIB               $JASPERLIB
setenv          JASPERINC               $JASPERINC

setenv          NAMELISTS_DIR           /work/syseng/pub/syseng-hpc/namelists
setenv          BIN_DIR	                /work/syseng/pub/syseng-hpc/scripts
setenv          WRF_ROOT_DIR            $ROOT_DIR
setenv          WRF_DIR                 $ROOT_DIR/model/WRF-4.3
setenv          WPS_DIR                 $ROOT_DIR/model/WPS-4.3
setenv          GEOG_DATA_PATH          $ROOT_DIR/data/WPS_GEOG
setenv          REAL_DATA_PATH          $ROOT_DIR/data/WPS_REAL
setenv          ARW_POST                $ROOT_DIR/model/ARWpost

set-alias       download-grib	        "python3 /work/syseng/pub/syseng-hpc/scripts/download-grib.py"

EOL

echo "Setting permissions..."

chgrp -R syseng $ROOT_DIR
chmod -R 777 $ROOT_DIR

echo "WRF-4.3 installed successfully!"
echo "IMPORTANT: Download WRF Preprocessing System (WPS) Geographical Input Data Mandatory Fields using ./download-geog-data"
