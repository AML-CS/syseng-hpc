#!/bin/sh
#
# Script file which helps to run WRF 4.2 and WRFDA 4.0
# Tested in Centos 7, Uninorte HPC
# Author: vdguevara@uninorte.edu.co
#

DIR=$(realpath "${BASH_SOURCE%/*}")
if [[ ! -d "$DIR" ]]; then DIR="${PWD}"; fi
. "${DIR}/print_msg"

options=$(getopt -o p:d:h --long help --long prefix: --long directory -- "$@")
eval set -- "$options"

function usage() {
    echo "Usage: $0 [options] [START] END"
    echo "Generates an ensemble with members from START to END"
    printf "\n  %-30s %s\n" "-p --prefix=PREFIX" "The prefix of the member filenames (ex: m would generate m1, m2, m3,...). Default is 'm'"
    printf "  %-30s %s\n" "-d --directory=DIRECTORY" "The directory where the members are going to be stored. Default is \$WRFDA_DIR/wrf_out"
    printf "  %-30s %s\n\n" "-h --help" "Show this message and exit"
    exit 0
}

PREFIX="m"
DIRECTORY="$WRFDA_DIR/wrf_out"
while true; do
 case "$1" in
    -p|--prefix)
        shift
        PREFIX=$1
        ;;
    -d|--directory)
        shift
        DIRECTORY=$(realpath $1)
        mkdir -p $1
        ;;
    -h|--help)
        usage
        ;;
    --)
        shift
        break
        ;;
 esac
 shift
done

START=1
N=2

if [[ -n $1 ]];
then
    N=$1
fi

if [[ -n $2 ]]; then
    START=$1
    N=$2
fi

cd $WRFDA_DIR
print_msg "Running simulation..."
${DIR}/run-wrf --wrf-processors 10 --output ${DIRECTORY}/original
for (( i=${START}; i<=$N; i++ )); do
    print_msg "Member ${i}" -cmagenta
    print_msg "Generating first initial condition..."
    ${DIR}/run-wrf --only-real --real-processors 10
    sed -i "s/^[[:space:]]*seed_array2.*/seed_array2=${i}/" namelist.input
    print_msg "Perturbing initial condition..."
    ${DIR}/run-wrfda --processors 10
    if [[ -f wrfvar_output ]]; then
        print_msg "Running simulation with new initial conditions..."
        cp wrfvar_output ${WRF_DIR}/run/wrfinput_d01
        ${DIR}/run-wrf --only-wrf --wrf-processors 10 --output ${DIRECTORY}/${PREFIX}${i}
        print_msg "Ensemble member ${i} created succesfully" -cgreen
    fi
done
