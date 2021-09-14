#!/usr/bin/env python3

import os
import sys
import time
import glob
import subprocess
import argparse
import datetime

from utils import print_msg, update_namelist

def init_cli():
    parser = argparse.ArgumentParser(description='Generate WRFDA Background error be.dat')

    parser.add_argument('start_date', metavar='start_date', type=str,
                        help='First perturbation valid date (YYYY-mm-dd H)')

    parser.add_argument('end_date', metavar='end_date', type=str,
                        help='Last perturbation valid date (YYYY-mm-dd H)')

    parser.add_argument('-i', '--interval', metavar='interval', type=int, default=6,
                        help='Hours interval, default: 6')

    parser.add_argument('-g', '--grid-size', metavar='grid_size', type=int,
                        default=25000, help='Grid size (meters), default: 25000')

    parser.add_argument('-o', '--output', metavar='output', type=str,
                        default='.', help='Output directory')

    parser.add_argument('-n', '--ntasks', metavar='ntasks', type=int,
                        default=16, help='MPI processors or SLURM tasks')

    parser.add_argument('--only-wrf', dest="run_real", default=True,
                        action='store_false', help='Run only wrf.exe')

    parser.add_argument('--only-real', dest="run_wrf", default=True,
                        action='store_false', help='Run only real.exe')

    parser.add_argument('--srun', dest="srun", default=False, action='store_true',
                        help='Run with srun (inside sbatch or salloc)')

    parser.add_argument('-d', '--debug', dest="debug", default=False,
                        action='store_true', help='Debug mode')

    return parser.parse_args()

def call_model(type, wrf_dir, output, ntasks, srun):
    os.chdir(f"{wrf_dir}/run")

    start = time.time()

    os.system('rm -f rsl.*')

    if type == 'real':
        os.system('rm -f wrfinput*')
        os.system('rm -f wrfbdy*')
        print_msg('Running real.exe...', 'header')

    if type == 'wrf':
        os.system('rm -rf wrfout*')
        print_msg('Running wrf.exe...', 'header')

    if srun:
        subprocess.run(['srun', '-n', str(ntasks), '--mpi=pmi2', f"{type}.exe"])
    else:
        subprocess.run(['mpirun', '-n', str(ntasks), f"{type}.exe"])

    if type == 'real' and len(glob.glob('wrfbdy*')) == 0:
        print_msg(f"error on run real.exe", 'fail')
        os.system('cat rsl.error*')
        sys.exit(1)

    if type == 'wrf' and len(glob.glob('wrfout*')) == 0:
        print_msg(f"error on run wrf.exe", 'fail')
        os.system('cat rsl.error*')
        sys.exit(1)

    if type == 'wrf':
        os.system('chmod 777 wrfout*')
        os.system(f"cp wrfout* {output}")

    print_msg('Success complete', 'okgreen')
    print_msg("{:.3f} seconds".format(time.time() - start), 'okgreen')

if __name__ == '__main__':
    args = init_cli()
    debug_mode = args.debug
    start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d %H')
    end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d %H')
    interval = args.interval
    grid_size = args.grid_size
    run_real = args.run_real
    run_wrf = args.run_wrf
    output = args.output
    ntasks = args.ntasks
    srun = args.srun

    WRF_DIR = os.environ.get('WRF_DIR', None)
    if WRF_DIR is None:
        raise Exception('Module wrf not loaded')

    NAMELISTS_DIR = os.environ.get('NAMELISTS_DIR', None)
    NAMELIST_FILE = f"{NAMELISTS_DIR}/namelist-wrf.input"

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
        'frames_per_outfile': 1000,
        'time_step': interval,
        'dx': grid_size,
        'dy': grid_size,
    }

    if debug_mode:
        for (key, value) in options.items():
            print_msg(f"{key}: {value}", 'header')

    os.system(f"ln -sf {NAMELIST_FILE} {WRF_DIR}/run/namelist.input")
    update_namelist(NAMELIST_FILE, options)

    if run_real:
        call_model('real', WRF_DIR, output, ntasks, srun)

    if run_wrf:
        call_model('wrf', WRF_DIR, output, ntasks, srun)
