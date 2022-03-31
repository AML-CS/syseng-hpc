#!/usr/bin/env python3

import os
import sys
import time
import glob
import argparse
import datetime

from utils import print_msg, update_namelist

WPS_DIR = os.environ.get('WPS_DIR', None)
WRF_DIR = os.environ.get('WRF_DIR', None)

NAMELISTS_DIR = os.environ.get('NAMELISTS_DIR', None)
NAMELIST_FILE = f"{NAMELISTS_DIR}/namelist.wps"


def init_cli():
    parser = argparse.ArgumentParser(
        description='Run geogrid + ungrid + metgrid')

    parser.add_argument('start_date', metavar='start_date', type=str,
                        help='First perturbation valid date (YYYY-mm-dd H)')

    parser.add_argument('end_date', metavar='end_date', type=str,
                        help='Last perturbation valid date (YYYY-mm-dd H)')

    parser.add_argument('--data-dir', metavar='data_dir', type=str,
                        help='NETCDF data path')

    parser.add_argument('-i', '--interval', metavar='interval', type=int, default=6,
                        help='Hours interval, default: 6')

    parser.add_argument('-g', '--grid-size', metavar='grid_size', type=int,
                        default=None, help='Grid size (meters), default: None')

    parser.add_argument('-d', '--debug', dest="debug", default=False,
                        action='store_true', help='Debug mode')

    return parser.parse_args()


def update_wps_namelist(options, debug_mode):
    os.system(f"ln -sf {NAMELIST_FILE} {WPS_DIR}/namelist.wps")
    update_namelist(NAMELIST_FILE, options)

    if debug_mode:
        for (key, value) in options.items():
            print_msg(f"{key}: {value}", 'header')


if __name__ == '__main__':
    args = init_cli()
    debug_mode = args.debug
    start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d %H')
    end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d %H')
    interval = args.interval
    grid_size = args.grid_size
    data_dir = os.path.abspath(args.data_dir)

    if WPS_DIR is None:
        raise Exception('Module wrf not loaded')

    namelist_input = {
        'start_date': f"'{start_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
        'end_date': f"'{end_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
        'interval_seconds': interval * 3600,
    }

    if grid_size:
        namelist_input['dx'] = grid_size
        namelist_input['dy'] = grid_size

    update_wps_namelist(namelist_input, debug_mode)

    start = time.time()

    os.chdir(WPS_DIR)

    os.system('rm -f GRIBFILE.*')
    os.system('rm -f met_em.*')
    os.system('rm -f FILE:*')
    os.system('rm -f geo_em.*')
    os.system(f"rm -f {WRF_DIR}/run/met_em*")

    print('Running geogrid...')
    if os.system('./geogrid.exe >& geogrid.log') != 0 or len(glob.glob('geo_em*')) == 0:
        print_msg(f"An error ocurred, check {WPS_DIR}/geogrid.log", 'fail')
        sys.exit(1)

    print_msg('Success complete', 'okgreen')

    print('Running ungrib...')
    data_dir = os.path.abspath(data_dir)
    print_msg(f"Using {data_dir}", 'warning')

    os.system(f"./link_grib.csh {data_dir}/*")
    os.system('ln -sf ungrib/Variable_Tables/Vtable.GFS Vtable')
    if os.system('./ungrib.exe >& ungrib.log') != 0 or len(glob.glob('GRIBFILE*')) == 0:
        print_msg(f"An error ocurred, check {WPS_DIR}/ungrib.log", 'fail')
        sys.exit(1)

    print_msg('Success complete', 'okgreen')

    print('Running metgrid...')
    if os.system('./metgrid.exe >& metgrid.log') != 0 or len(glob.glob('met_em*')) == 0:
        print_msg(f"An error ocurred, check {WPS_DIR}/metgrid.log", 'fail')
        sys.exit(1)

    os.system(f"ln -sf {WPS_DIR}/met_em* {WRF_DIR}/run")

    print_msg('Success complete', 'okgreen')
    print_msg("{:.3f} seconds".format(time.time() - start), 'okgreen')
