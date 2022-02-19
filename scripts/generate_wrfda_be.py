#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import argparse
import datetime

import run_wrf
from utils import print_msg, update_namelist, update_env_variables

def init_cli():
    parser = argparse.ArgumentParser(description='Generate WRFDA Background error be.dat')

    parser.add_argument('start_date', metavar='start_date', type=str,
                        help='First perturbation valid date (YYYY-mm-dd H)')

    parser.add_argument('end_date', metavar='end_date', type=str,
                        help='Last perturbation valid date (YYYY-mm-dd H)')

    parser.add_argument('--data-dir', metavar='data_dir', type=str,
                        help='Directory with ./prep-data and ./real-data')

    parser.add_argument('-i', '--interval', metavar='interval', type=int, default=6,
                        help='Hours interval, default: 6')

    parser.add_argument('-g', '--grid-size', metavar='grid_size', type=int,
                        default=25000, help='Grid size (meters), default: 25000')

    parser.add_argument('-n', '--ntasks', metavar='ntasks', type=int,
                        default=16, help='MPI processors or SLURM tasks')

    parser.add_argument('--srun', dest="srun", default=False, action='store_true',
                        help='Run with srun (inside sbatch or salloc)')

    parser.add_argument('-d', '--debug', dest="debug", default=False,
                        action='store_true', help='Debug mode')

    return parser.parse_args()

if __name__ == '__main__':
    args = init_cli()
    debug_mode = args.debug
    start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d %H')
    end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d %H')
    data_dir = args.data_dir
    interval = args.interval
    grid_size = args.grid_size
    ntasks = args.ntasks
    srun = args.srun

    WRF_DIR = os.environ.get('WRF_DIR', None)
    if WRF_DIR is None:
        raise Exception('Module wrf not loaded')

    WRFDA_DIR = os.environ.get('WRFDA_DIR', None)
    if WRFDA_DIR is None:
        raise Exception('Module wrfda not loaded')

    WRFDA_ROOT = os.environ.get('WRFDA_ROOT', None)
    NAMELISTS_DIR = os.environ.get('NAMELISTS_DIR', None)

    FCST_RANGE1 = 24
    FCST_RANGE2 = 12

    interval_delta =  datetime.timedelta(hours=interval)
    fcst_range1_delta = datetime.timedelta(hours=FCST_RANGE1)

    valid_start_date = start_date - fcst_range1_delta
    valid_end_date = end_date + fcst_range1_delta

    options = {
        'start_year': valid_start_date.year,
        'start_month': str(valid_start_date.month).zfill(2),
        'start_day': str(valid_start_date.day).zfill(2),
        'start_hour': str(valid_start_date.hour).zfill(2),
        'end_year': valid_end_date.year,
        'end_month': str(valid_end_date.month).zfill(2),
        'end_day': str(valid_end_date.day).zfill(2),
        'end_hour': str(valid_end_date.hour).zfill(2),
        'interval_seconds': interval * 3600,
        'history_interval': interval * 60,
        'frames_per_outfile': 1,
        'time_step': 6,
        'dx': grid_size,
        'dy': grid_size,
    }

    if debug_mode:
        for (key, value) in options.items():
            print_msg(f"{key}: {value}", 'header')

    update_namelist(f"{NAMELISTS_DIR}/namelist-wrf.input", options)

    BE_DATA_DIR = f"{os.path.abspath(data_dir)}/be-data"
    GEN_BE_DIR = f"{os.path.abspath(data_dir)}/gen-be"

    subprocess.run(['rm', f"{WRFDA_DIR}/be.dat"])
    subprocess.run(['rm', '-rf', BE_DATA_DIR, GEN_BE_DIR])

    os.system(f"mkdir -p {BE_DATA_DIR}")
    os.system(f"mkdir -p {GEN_BE_DIR}")

    run_wrf.call_model('real', WRF_DIR, 8, srun)
    run_wrf.call_model('wrf', WRF_DIR, ntasks, srun, output=BE_DATA_DIR)

    print_msg(f"Formatting {BE_DATA_DIR}", 'header')
    os.system(f"ls {BE_DATA_DIR}")

    p_start_date = start_date

    while p_start_date <= end_date:
        folder_path = f"{BE_DATA_DIR}/{p_start_date.strftime('%Y%m%d%H')}"
        os.system(f"mkdir -p {folder_path}")

        for i in range(1, 3):
            file_delta = datetime.timedelta(hours=FCST_RANGE2*i)
            filename_date = (p_start_date + file_delta).strftime('%Y-%m-%d_%H:%M:%S')
            os.system(f"cp {BE_DATA_DIR}/wrfout_d01_{filename_date} {folder_path}")

        p_start_date += interval_delta

    gen_be_start_date = start_date + fcst_range1_delta
    gen_be_end_date = end_date - fcst_range1_delta

    env_vars = {
        'WRFVAR_DIR': f"{WRFDA_ROOT}/model/WRFDA",
        'NL_CV_OPTIONS': 7, # u/v wind control variables
        'START_DATE': gen_be_start_date.strftime('%Y%m%d%H'),
        'END_DATE': gen_be_end_date.strftime('%Y%m%d%H'),
        'NUM_LEVELS': 40, # = bottom_top = e_vert - 1
        'BIN_TYPE': 5,
        'FC_DIR': BE_DATA_DIR,
        'RUN_DIR': GEN_BE_DIR,
        'FCST_RANGE1': FCST_RANGE1,
        'FCST_RANGE2': FCST_RANGE2,
        'INTERVAL': interval
    }

    print_msg('Running gen_be_wrapper.ksh', 'header')
    start = time.time()

    gen_be_wrapper = f"{WRFDA_ROOT}/model/WRFDA/var/scripts/gen_be/gen_be_wrapper.ksh"
    update_env_variables(gen_be_wrapper, env_vars)

    subprocess.run([gen_be_wrapper])

    output_file = f"{GEN_BE_DIR}/be.dat"
    if os.path.isfile(output_file):
        os.system(f"ln -sf {output_file} {WRFDA_DIR}")
        print_msg('Success complete', 'okgreen')
        print_msg("{:.3f} seconds".format(time.time() - start), 'okgreen')

