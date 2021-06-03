#!/usr/bin/env bash

options=$(getopt -o p: --long processors: -- "$@")
eval set -- "$options"

PROCESSORS=5
while true; do
    case "$1" in
    -p|--processors)
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
cp $WRF_DIR/run/wrfbdy_d01 . 
ln -sf $WRF_DIR/run/wrfinput_d01 .
ln -sf wrfinput_d01 fg

echo "Running wrfda with ${PROCESSORS} processors"
time mpirun -n ${PROCESSORS} ./da_wrfvar.exe > /dev/null 2>&1
