#!/bin/sh
#
# Script file which helps to run WRF 4.2 and WRFDA 4.0
# Tested in Centos 7, Uninorte HPC
# Author: vdguevara@uninorte.edu.co
#

options=$(getopt -o p --long --processors: -- "$@")
eval set -- "$options"

PROCESSORS=10
while true; do
    case "$1" in
        -o|--processors)
            shift
            PROCESSORS=$1
            ;;
        --)
            shift
            break
            ;;
    esac
    shift
done

cd $WRFDA_DIR
ln -sf $WRF_DIR/run/wrfinput_d01 .
ln -sf wrfinput_d01 fg
ln -sf $WRF_DIR/run/wrfbdy_d01 .

time mpirun -np ${PROCESSORS} ./da_wrfvar.exe
