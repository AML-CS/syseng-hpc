#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import argparse
import datetime

from utils import print_msg, update_namelist

OBSPROC_DIR = os.environ.get('OBSPROC_DIR', None)

NAMELISTS_DIR = os.environ.get('NAMELISTS_DIR', None)
NAMELIST_FILE = f"{NAMELISTS_DIR}/namelist-obsproc.input"

def init_cli():
    parser = argparse.ArgumentParser(description='Run geogrid + ungrid + metgrid')

    # parser.add_argument('start_date', metavar='start_date', type=str,
    #                     help='First perturbation valid date (YYYY-mm-dd H)')

    # parser.add_argument('end_date', metavar='end_date', type=str,
    #                     help='Last perturbation valid date (YYYY-mm-dd H)')

    # parser.add_argument('--metar-data', metavar='metar_data', type=str,
    #                     help='METAR observations')

    # parser.add_argument('-i', '--interval', metavar='interval', type=int, default=6,
    #                     help='Hours interval, default: 6')

    # parser.add_argument('-g', '--grid-size', metavar='grid_size', type=int,
    #                     default=25000, help='Grid size (meters), default: 25000')

    parser.add_argument('-d', '--debug', dest="debug", default=False,
                        action='store_true', help='Debug mode')

    return parser.parse_args()

def update_obsproc_namelist(options, debug_mode):
    os.system(f"ln -sf {NAMELIST_FILE} {OBSPROC_DIR}/namelist.obsproc")
    update_namelist(NAMELIST_FILE, options)

    if debug_mode:
        for (key, value) in options.items():
            print_msg(f"{key}: {value}", 'header')

if __name__ == '__main__':
    args = init_cli()
    debug_mode = args.debug
    # start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d %H')
    # end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d %H')
    # metar_data = os.path.abspath(args.metar_data)

    if OBSPROC_DIR is None:
        raise Exception('Module wrfda not loaded')

    update_obsproc_namelist({
        'obs_gts_filename': f"'{OBSPROC_DIR}/obs.2022022012'",
        'time_window_min': '2022-02-20_11:00:00',
        'time_analysis': '2022-02-20_12:00:00',
        'time_window_max': '2022-02-20_13:00:00',
        # 'start_date': f"'{start_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
        # 'end_date': f"'{end_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
    }, debug_mode)

    start = time.time()

    os.chdir(OBSPROC_DIR)

    if os.system('./obsproc.exe >& obsproc.log') != 0:
        print_msg(f"An error ocurred, check {OBSPROC_DIR}/obsproc.log", 'fail')
        sys.exit(1)

    print_msg('Success complete', 'okgreen')
    print_msg("{:.3f} seconds".format(time.time() - start), 'okgreen')
