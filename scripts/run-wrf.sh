#!/bin/sh
#
# Script file which helps to run WRF 4.2 and WRFDA 4.0
# Tested in Centos 7, Uninorte HPC
# Author: vdguevara@uninorte.edu.co
#

DIR="${BASH_SOURCE%/*}"
if [[ ! -d "$DIR" ]]; then DIR="$PWD"; fi
. "$DIR/print_msg"

options=$(getopt -o "WRw:r:o:f:t:s:h" --long help --long only-wrf --long only-real --long wrf-processors:\
                                    --long real-processors: --long output: --long from: --long to:\
                                    --long time: -- "$@")

function usage() {
    echo "Usage: $0 [options]"
    echo "Runs a WRF simulation using wrf.exe and real.exe"
    printf "\n  %-35s %s\n" "-W --only-wrf" "Run only wrf.exe"
    printf "  %-35s %s\n" "-R --only-real" "Run only real.exe"
    printf "  %-35s %s\n" "-w --wrf-processors=PROCESSORS" "How many processors to run wrf.exe with. The default value is 64"
    printf "  %-35s %s\n" "-r --real-processors=PROCESSOSRS" "How many processors to run real.exe with. The default value is 15"
    printf "  %-35s %s\n" "-f --from=DATE" "Start date"
    printf "  %-35s %s\n" "-t --to=DATE" "End date"
    printf "  %-35s %s\n" "-s --time=HOURS" "Simulation time in hours"
    printf "  %-35s %s\n\n" "-h --help" "Show this message and exit"
    exit 0
}

eval set -- "$options"

DIR=$(pwd)
REAL=true
WRF=true
WRF_PROCESSORS=10
REAL_PROCESSORS=5
DESTINATION=${HOME}/wrf/output

while true; do
    case "$1" in
        -W|--only-wrf)
            REAL=false
            ;;

        -R|--only-real)
            WRF=false
            ;;

        -w|--wrf-processors)
            shift
            WRF_PROCESSORS="$1"
            ;;

        -r|--real-processors)
            shift
            REAL_PROCESSORS="$1"
            ;;

        -o|--output)
            shift
            DESTINATION=$1
            ;;

        -h|--help)
            usage
            ;;

        -t|--to)
            shift
            TO=$1
            ;;

        -s|--time)
            shift
            TIME=$1
            ;;

        -f|--from)
            shift
            FROM=$1
            ;;

        --)
            shift
            break
            ;;
    esac
    shift
done

cd ${WRF_DIR}/run

# Namelist modification

if [[ -n $TIME ]]; then
    sed -i "s/run_hours.*/run_hours = ${TIME},/" namelist.input
    print_msg "Run hours: ${TIME}" -cmagenta
fi

if [[ -n $FROM ]]; then
    YEAR=$(date --date="${FROM}" +%Y)
    MONTH=$(date --date="${FROM}" +%m)
    DAY=$(date --date="${FROM}" +%d)
    HOUR=$(date --date="${FROM}" +%H)
    sed -i "s/start_year.*/start_year = $YEAR,/" namelist.input
    sed -i "s/start_month.*/start_month = $MONTH,/" namelist.input
    sed -i "s/start_day.*/start_day = $DAY,/" namelist.input
    sed -i "s/start_hour.*/start_hour = $HOUR,/" namelist.input
    print_msg "Start date: ${FROM}" -cmagenta
fi

if [[ -n $FROM ]]; then
    YEAR=$(date --date="${TO}" +%Y)
    MONTH=$(date --date="${TO}" +%m)
    DAY=$(date --date="${TO}" +%d)
    HOUR=$(date --date="${TO}" +%H)
    sed -i "s/end_year.*/end_year = $YEAR,/" namelist.input
    sed -i "s/end_month.*/end_month = $MONTH,/" namelist.input
    sed -i "s/end_day.*/end_day = $DAY,/" namelist.input
    sed -i "s/end_hour.*/end_hour = $HOUR,/" namelist.input
    print_msg "End date: ${FROM}" -cmagenta
fi

rm -f rsl.*
rm -f met_em*
ln -sf ${WPS_DIR}/met_em* .

if ${REAL}
then
    rm -f wrfinput_d* 2> /dev/null
    rm -f wrfbdy_d* 2> /dev/null 
    time mpirun -np ${REAL_PROCESSORS} ./real.exe
fi

if ${WRF}
then
    rm wrfout*
    time mpirun -np ${WRF_PROCESSORS} ./wrf.exe
    chown ${USER}:syseng wrfout*
    cd ${DIR}
    cp ${WRF_DIR}/run/wrfout* ${DESTINATION}
fi
