#!/bin/sh
#
# Setup and build WRF 4.2 as module
# Tested in Centos 7, Uninorte HPC
# Author: sjdonado@uninorte.edu.co
#

# Install and update low level dependencies
sudo yum -y update
sudo yum -y upgrade
sudo yum -y install wget gcc gcc-gfortran gcc-c++ libtool automake autoconf make m4 java-11-openjdk csh

## Dir structure
export ROOT_DIR="/opt/ohpc/pub/WRF_Model"
mkdir -p $ROOT_DIR/downloads
mkdir -p $ROOT_DIR/model

############################ WRF 4.2 ###################################
## Install dependencies
########################################################################

cd $ROOT_DIR/downloads
wget -c http://cola.gmu.edu/grads/2.2/grads-2.2.0-bin-centos7.3-x86_64.tar.gz
wget -c https://www.zlib.net/zlib-1.2.11.tar.gz
wget -c https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/hdf5-1.10.5/src/hdf5-1.10.5.tar.gz
wget -c -O netcdf-c-4.7.1.tar.gz https://github.com/Unidata/netcdf-c/archive/v4.7.1.tar.gz
#wget -c https://www.unidata.ucar.edu/downloads/netcdf/ftp/netcdf-c-4.7.1.tar.gz
wget -c https://www.unidata.ucar.edu/downloads/netcdf/ftp/netcdf-fortran-4.5.1.tar.gz
wget -c http://www.mpich.org/static/downloads/3.3.1/mpich-3.3.1.tar.gz
wget -c https://download.sourceforge.net/libpng/libpng-1.6.37.tar.gz
wget -c https://www.ece.uvic.ca/~frodo/jasper/software/jasper-1.900.1.zip

# Compilers env flags
export DIR=$ROOT_DIR/Library
export CC=gcc
export CXX=g++
export FC=gfortran
export F77=gfortran

# Setup Grads 2.2.0
tar -xvzf $ROOT_DIR/downloads/grads-2.2.0-bin-centos7.3-x86_64.tar.gz -C $ROOT_DIR/downloads
mv $ROOT_DIR/downloads/grads-2.2.0/bin/* $DIR/bin
mv $ROOT_DIR/downloads/grads-2.2.0/lib/* $DIR/lib

# Setup zlib 1.2.11
tar -xvzf $ROOT_DIR/downloads/zlib-1.2.11.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/zlib-1.2.11/
./configure --prefix=$DIR
make
make install

# Setup hdf5 library for netcdf4 functionality
tar -xvzf $ROOT_DIR/downloads/hdf5-1.10.5.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/hdf5-1.10.5
./configure --prefix=$DIR --with-zlib=$DIR --enable-hl --enable-fortran
make check
make install

export HDF5=$DIR
export LD_LIBRARY_PATH=$DIR/lib:$LD_LIBRARY_PATH

## Setup netcdf-c-4.7.1
tar -xzvf $ROOT_DIR/downloads/netcdf-c-4.7.1.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/netcdf-c-4.7.1/

export CPPFLAGS=-I$DIR/include
export LDFLAGS=-L$DIR/lib
./configure --prefix=$DIR --disable-dap

make check
make install

export PATH=$DIR/bin:$PATH
export NETCDF=$DIR

## Setup netcdf-fortran-4.5.1
tar -xvzf $ROOT_DIR/downloads/netcdf-fortran-4.5.1.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/netcdf-fortran-4.5.1/
export LIBS="-lnetcdf -lhdf5_hl -lhdf5 -lz" 

./configure --prefix=$DIR --disable-shared
make check
make install

## Setup mpich-3.3.1
tar -xvzf $ROOT_DIR/downloads/mpich-3.3.1.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/mpich-3.3.1/
./configure --prefix=$DIR
make
make install

export PATH=$DIR/bin:$PATH

# Setup libpng-1.6.37
tar -xvzf $ROOT_DIR/downloads/libpng-1.6.37.tar.gz -C $ROOT_DIR/downloads
cd $ROOT_DIR/downloads/libpng-1.6.37/
./configure --prefix=$DIR
make
make install

# Setup jasper-1.900.1
mkdir $ROOT_DIR/downloads/jasper-1.900.1
unzip $ROOT_DIR/downloads/jasper-1.900.1.zip
cd $ROOT_DIR/downloads/jasper-1.900.1
autoreconf -i
./configure --prefix=$DIR
make
make install
export JASPERLIB=$DIR/lib
export JASPERINC=$DIR/include

############################ WRF 4.2 ###################################
## Build model
## Downloaded from git tagged releases
########################################################################

# Setup WRFV4.2
cd $ROOT_DIR/downloads
wget -c https://github.com/wrf-model/WRF/archive/v4.2.tar.gz
tar -xvzf $ROOT_DIR/downloads/v4.2.tar.gz -C $ROOT_DIR/model
# cp -R $ROOT_DIR/model/WRF-4.2 $ROOT_DIR/model/WRF-4.2-real
# cp -R $ROOT_DIR/model/WRF-4.2 $ROOT_DIR/model/WRF-4.2-ideal

# Compile WRF-4.2
cd $ROOT_DIR/model/WRF-4.2
./clean
./configure # 34, 1 for gfortran and distributed memory
./compile em_real

echo "If compilation was successful, you should see wrf.exe and real.exe"
ls -l *exe

export WRF_DIR=$ROOT_DIR/model/WRF-4.2

# Setup WPSV4.2
cd $ROOT_DIR/downloads
wget -c https://github.com/wrf-model/WPS/archive/v4.2.zip
unzip $ROOT_DIR/downloads/v4.2.zip -d $ROOT_DIR/model
cd $ROOT_DIR/model/WPS-4.2
./clean
./configure #3
./compile

echo "If compilation was successful, you should see geogrid.exe, metgrid.exe and ungrib.exe"
ls -l *exe

######################## Post-Processing Tools ####################
# Setup ARWpost
cd $ROOT_DIR/downloads
wget -c http://www2.mmm.ucar.edu/wrf/src/ARWpost_V3.tar.gz
tar -xvzf $ROOT_DIR/downloads/ARWpost_V3.tar.gz -C $ROOT_DIR/model
cd $ROOT_DIR/model/ARWpost
./clean
sed -i -e 's/-lnetcdf/-lnetcdff -lnetcdf/g' $ROOT_DIR/model/ARWpost/src/Makefile
./configure #3
sed -i -e 's/-C -P/-P/g' $ROOT_DIR/model/ARWpost/configure.arwp
./compile

######################## Model Setup Tools ########################
# Setup DomainWizard
cd $ROOT_DIR/downloads
wget -c http://esrl.noaa.gov/gsd/wrfportal/domainwizard/WRFDomainWizard.zip
mkdir $ROOT_DIR/model/WRFDomainWizard
unzip $ROOT_DIR/downloads/WRFDomainWizard.zip -d $ROOT_DIR/model/WRFDomainWizard
chmod +x $ROOT_DIR/model/WRFDomainWizard/run_DomainWizard

echo "Writting scripts..."
# TODO: git clone

echo "Writting modulefile..."

mkdir -p /opt/ohpc/pub/modulefiles/wrf/
cat > /opt/ohpc/pub/modulefiles/wrf/4.2.0  <<EOL
#%Module1.0#####################################################################

proc ModulesHelp { } {
        puts stderr " "
        puts stderr "This module loads WRF-4.2.0 and dependencies"
        puts stderr "\nVersion 4.2.0\n"
}

module-whatis "Name: wrf/4.2.0"
module-whatis "Version: 4.2.0"
module-whatis "Category: utility, developer support"
module-whatis "Keywords: System, Utility"
module-whatis "The Weather Research and Forecasting (WRF) model"
module-whatis "URL https://github.com/wrf-model/WRF"

set             version                 4.2.0

prepend-path    PATH                    /opt/ohpc/pub/WRF_Model/Library/bin:/opt/ohpc/pub/WRF_Model/Library/bin:/opt/ohpc/pub/WRF_Model/Library/bin:/opt/ohpc/pub/WRF_Model/Library/bin:/root/install/WRF_Model/Library/bin:/opt/ohpc/pub/apps/miniconda/4.8.3/condabin:/opt/ohpc/pub/mpi/openmpi3-gnu8/3.1.4/bin:/opt/ohpc/pub/compiler/gcc/8.3.0/bin:/opt/ohpc/pub/utils/prun/1.3:/opt/ohpc/pub/utils/autotools/bin:/opt/ohpc/pub/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/var/lib/snapd/snap/bin:/root/bin
prepend-path    LD_LIBRARY_PATH         /opt/ohpc/pub/WRF_Model/Library/lib:/opt/ohpc/pub/WRF_Model/Library/lib:/opt/ohpc/pub/WRF_Model/Library/lib:/root/install/WRF_Model/Library/lib:/root/install/WRF_Model/Library/lib:/root/install/WRF_Model/Library/lib:/opt/ohpc/pub/mpi/openmpi3-gnu8/3.1.4/lib:/opt/ohpc/pub/compiler/gcc/8.3.0/lib64

setenv          CC                      gcc
setenv          CXX                     g++
setenv          FC                      gfortran
setenv          F77                     gfortran

setenv          HDF5                    /opt/ohpc/pub/WRF_Model/Library
setenv          LD_LIBRARY_PATH         /opt/ohpc/pub/WRF_Model/Library/lib:/opt/ohpc/pub/WRF_Model/Library/lib:/root/install/WRF_Model/Library/lib:/root/install/WRF_Model/Library/lib:/root/install/WRF_Model/Library/lib:/opt/ohpc/pub/mpi/openmpi3-gnu8/3.1.4/lib:/opt/ohpc/pub/compiler/gcc/8.3.0/lib64

setenv          CPPFLAGS                -I/opt/ohpc/pub/WRF_Model/Library/include
setenv          LDFLAGS                 -L/opt/ohpc/pub/WRF_Model/Library/lib

setenv          NETCDF                  /opt/ohpc/pub/WRF_Model/Library

setenv          LIBS                    -lnetcdf -lhdf5_hl -lhdf5 -lz

setenv          JASPERLIB               /opt/ohpc/pub/WRF_Model/Library/lib
setenv          JASPERINC               /opt/ohpc/pub/WRF_Model/Library/include

setenv          BIN_DIR	                /opt/ohpc/pub/syseng-hpc/scripts
setenv          WRF_ROOT_DIR            /opt/ohpc/pub/WRF_Model
setenv          WRF_DIR                 /opt/ohpc/pub/WRF_Model/model/WRF-4.2
setenv          WPS_DIR                 /opt/ohpc/pub/WRF_Model/model/WPS-4.2
setenv          GEOG_DATA_PATH          /opt/ohpc/pub/WRF_Model/data/WPS_GEOG
setenv          REAL_DATA_PATH          /opt/ohpc/pub/WRF_Model/data/WPS_REAL
setenv          ARW_POST                /opt/ohpc/pub/WRF_Model/model/ARWpost

set-alias       download-grib	        "sh /opt/ohpc/pub/syseng-hpc/scripts/download-grib.sh"
set-alias       run-wps                 "sh /opt/ohpc/pub/syseng-hpc/scripts/run-wps.sh"
set-alias       run-wrf                 "sh /opt/ohpc/pub/syseng-hpc/scripts/run-wrf.sh"
set-alias       run-arwpost             "sh /opt/ohpc/pub/syseng-hpc/scripts/run-arwpost.sh"

EOL

echo "Setting permissions..."

chgrp -R syseng $ROOT_DIR
chmod -R 777 $ROOT_DIR

echo "DONE! WRF-4.2.0 installed successfully"
