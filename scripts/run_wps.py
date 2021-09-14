#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import argparse
import datetime

from utils import print_msg, update_namelist

def init_cli():
    parser = argparse.ArgumentParser(description='Run geogrid + ungrid + metgrid')

    parser.add_argument('start_date', metavar='start_date', type=str,
                        help='First perturbation valid date (YYYY-mm-dd H)')

    parser.add_argument('end_date', metavar='end_date', type=str,
                        help='Last perturbation valid date (YYYY-mm-dd H)')

    parser.add_argument('--real-data', metavar='real_data', type=str,
                        help='GRIB2 observations')

    parser.add_argument('-i', '--interval', metavar='interval', type=int, default=6,
                        help='Hours interval, default: 6')

    parser.add_argument('-g', '--grid-size', metavar='grid_size', type=int,
                        default=25000, help='Grid size (meters), default: 25000')

    parser.add_argument('-d', '--debug', dest="debug", default=False,
                        action='store_true', help='Debug mode')

    return parser.parse_args()

if __name__ == '__main__':
    args = init_cli()
    debug_mode = args.debug
    start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d %H')
    end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d %H')
    interval = args.interval
    grid_size = args.grid_size
    real_data = os.path.abspath(args.real_data)

    WPS_DIR = os.environ.get('WPS_DIR', None)
    if WPS_DIR is None:
        raise Exception('Module wrf not loaded')

    WRF_DIR = os.environ.get('WRF_DIR', None)
    NAMELISTS_DIR = os.environ.get('NAMELISTS_DIR', None)
    NAMELIST_FILE = f"{NAMELISTS_DIR}/namelist.wps"

    options = {
        'start_date': f"'{start_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
        'end_date': f"'{end_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
        'interval_seconds': interval * 3600,
        'dx': grid_size,
        'dy': grid_size,
    }

    if debug_mode:
        for (key, value) in options.items():
            print_msg(f"{key}: {value}", 'header')

    os.system(f"ln -sf {NAMELIST_FILE} {WPS_DIR}/namelist.wps")
    update_namelist(NAMELIST_FILE, options)

    os.chdir(WPS_DIR)

    start = time.time()

    os.system('rm -rf GRIBFILE*')
    os.system('rm -rf PFILE*')
    os.system('rm -rf met_em*')
    os.system(f"rm -rf {WRF_DIR}/run/met_em*")

    print('Running geogrid...')
    if os.system('./geogrid.exe >& geogrid.log') != 0:
        print_msg(f"An error ocurred, check {WPS_DIR}/geogrid.log", 'fail')
        sys.exit(1)

    print_msg('Success complete', 'okgreen')

    print('Running ungrib...')
    real_data = os.path.abspath(real_data)
    print_msg(f"Using {real_data}", 'warning')

    os.system(f"./link_grib.csh {real_data}/*")
    os.system('ln -sf ungrib/Variable_Tables/Vtable.GFS Vtable')
    if os.system('./ungrib.exe >& ungrib.log') != 0:
        print_msg(f"An error ocurred, check {WPS_DIR}/ungrib.log", 'fail')
        sys.exit(1)

    print_msg('Success complete', 'okgreen')

    print('Running metgrid...')
    if os.system('./metgrid.exe >& metgrid.log') != 0:
        print_msg(f"An error ocurred, check {WPS_DIR}/metgrid.log", 'fail')
        sys.exit(1)

    os.system(f"ln -sf {WPS_DIR}/met_em* {WRF_DIR}/run")

    print_msg('Success complete', 'okgreen')
    print_msg("{:.3f} seconds".format(time.time() - start), 'okgreen')
