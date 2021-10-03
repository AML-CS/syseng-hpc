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

    options = {
        'start_year': start_date.year,
        'start_month': str(start_date.month).zfill(2),
        'start_day': str(start_date.day).zfill(2),
        'start_hour': str(start_date.hour).zfill(2),
        'end_year': end_date.year,
        'end_month': str(end_date.month).zfill(2),
        'end_day': str(end_date.day).zfill(2),
        'end_hour': str(end_date.hour).zfill(2),
        'interval_seconds': interval * 3600,
        'history_interval': interval * 60,
        'frames_per_outfile': 1,
        'time_step': interval,
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

    os.system(f"ls {BE_DATA_DIR}")
    print_msg(f"Formatting {BE_DATA_DIR}", 'header')

    interval_delta = datetime.timedelta(hours=interval)
    hour_delta = datetime.timedelta(hours=24)
    p_start_date = start_date
    p_end_date = end_date - hour_delta

    while p_start_date <= p_end_date:
        folder_path = f"{BE_DATA_DIR}/{p_start_date.strftime('%Y%m%d%H')}"
        os.system(f"mkdir -p {folder_path}")

        for i in range(1, int(24 / interval) + 1):
            file_delta = datetime.timedelta(hours=interval*i)
            filename_date = (p_start_date + file_delta).strftime('%Y-%m-%d_%H:%M:%S')
            os.system(f"cp {BE_DATA_DIR}/wrfout_d01_{filename_date} {folder_path}")

        p_start_date += interval_delta

    valid_start_date = start_date + hour_delta
    valid_end_date = p_end_date - hour_delta

    # TODO: only works for the data example https://www2.mmm.ucar.edu/wrf/users/docs/user_guide_v4/v4.0/users_guide_chap6.html#_Domain-specific_background_error
    # Error candidates: NUM_LEVELS, INTERVAL
    # Debug: generate-wrfda-be "2021-01-05 00" "1021-01-06 18" -i 6 -n 64 -g 25000 --data-dir ./ --srun
    # Next steps: debug with -g 1000
    env_vars = {
        'WRFVAR_DIR': f"{WRFDA_ROOT}/model/WRFDA",
        'NL_CV_OPTIONS': 5,
        'START_DATE': valid_start_date.strftime('%Y%m%d%H'),
        'END_DATE': valid_end_date.strftime('%Y%m%d%H'),
        'NUM_LEVELS': 32, # 40 (default)
        'BIN_TYPE': 5,
        'INTERVAL': interval, # 12 (default)
        'FC_DIR': BE_DATA_DIR,
        'RUN_DIR': GEN_BE_DIR
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

