#!/usr/bin/env python3

import os
import sys
import time
import glob
import subprocess
import argparse
import datetime

import run_wrf
from run_wrf import WRF_DIR, update_wrf_namelist

from utils import print_msg, update_namelist

WRFDA_DIR = os.environ.get('WRFDA_DIR', None)

NAMELISTS_DIR = os.environ.get('NAMELISTS_DIR', None)
NAMELIST_FILE = f"{NAMELISTS_DIR}/namelist-wrfda.input"

def init_cli():
    parser = argparse.ArgumentParser(description='Run WRFDA da_wrfvar.exe + generate ensemble')

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

    parser.add_argument('--generate-ensemble', metavar="generate_ensemble",
                        type=int, default=0, help='Number of ensemble members')

    parser.add_argument('-n', '--ntasks', metavar='ntasks', type=int,
                        default=16, help='MPI processors or SLURM tasks')

    parser.add_argument('--srun', dest="srun", default=False, action='store_true',
                        help='Run with srun (inside sbatch or salloc)')

    parser.add_argument('-d', '--debug', dest="debug", default=False,
                        action='store_true', help='Debug mode')

    return parser.parse_args()

def call_model(wrf_dir, wrfda_dir, ntasks, srun):
    os.chdir(wrfda_dir)

    start = time.time()

    os.system('rm -f wrfinput*')
    os.system('rm -f wrfbdy*')
    os.system('rm -f wrfvar_output*')
    os.system('rm -f rsl.*')

    os.system(f"cp {wrf_dir}/run/wrfbdy_d01 .")
    os.system(f"ln -sf {wrf_dir}/run/wrfinput_d01 .")
    os.system('ln -sf wrfinput_d01 fg')

    if srun:
        subprocess.run(['srun', '-n', str(ntasks), '--mpi=pmi2', 'da_wrfvar.exe'])
    else:
        subprocess.run(['mpirun', '-n', str(ntasks), 'da_wrfvar.exe'])

    if not os.path.isfile('wrfvar_output'):
        print_msg(f"error on run da_wrfvar.exe", 'fail')
        os.system('cat rsl.error*')
        return False

    print_msg('Success complete', 'okgreen')
    print_msg("{:.3f} seconds".format(time.time() - start), 'okgreen')

    return True

def update_wrfda_namelist(options, debug_mode):
    os.system(f"ln -sf {NAMELIST_FILE} {WRFDA_DIR}/namelist-wrfda.input")
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
    output = os.path.abspath(args.output)
    generate_ensemble = args.generate_ensemble
    ntasks = args.ntasks
    srun = args.srun

    if WRFDA_DIR is None:
        raise Exception('Module wrfda not loaded')

    options = {
        'start_year': start_date.year,
        'start_month': str(start_date.month).zfill(2),
        'start_day': str(start_date.day).zfill(2),
        'start_hour': str(start_date.hour).zfill(2),
        'end_year': end_date.year,
        'end_month': str(end_date.month).zfill(2),
        'end_day': str(end_date.day).zfill(2),
        'end_hour': str(end_date.hour).zfill(2),
        'analysis_date': f"'{start_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
        'time_window_min': f"'{start_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
        'time_window_max': f"'{end_date.strftime('%Y-%m-%d_%H:%M:%S')}'",
        'interval_seconds': interval * 3600,
        'time_step': 6,
        'frames_per_outfile': 1000,
        'dx': grid_size,
        'dy': grid_size,
    }
    update_wrfda_namelist(options, debug_mode)

    update_wrf_namelist({
        'start_year': options['start_year'],
        'start_month': options['start_month'],
        'start_day': options['start_day'],
        'start_hour': options['start_hour'],
        'end_year': options['end_year'],
        'end_month': options['end_month'],
        'end_day': options['end_day'],
        'end_hour': options['end_hour'],
        'interval_seconds': options['interval_seconds'],
        'history_interval': interval * 60,
        'frames_per_outfile': options['frames_per_outfile'],
        'time_step': options['time_step'],
        'dx': options['dx'],
        'dy': options['dy'],
    }, debug_mode)

    start = time.time()

    run_wrf.call_model('real', WRF_DIR, 8, srun)
    run_wrf.call_model('wrf', WRF_DIR, ntasks, srun, output=f"{output}/fg")

    if generate_ensemble > 0:

        for i in range(1, generate_ensemble + 1):
            print_msg(f"Member {i}", 'header')

            print('Generating first initial condition...')
            run_wrf.call_model('real', WRF_DIR, 8, srun)

            ensemble_options = {
                'seed_array1': start_date.strftime('%Y%m%d%H'),
                'seed_array2': i
            }
            update_wrfda_namelist(ensemble_options, debug_mode)

            print('Perturbing initial condition...')
            if call_model(WRF_DIR, WRFDA_DIR, ntasks, srun):
                print('Updating boundary conditions...')
                os.system('./da_update_bc.exe >& update.out')
                os.system(f"cp wrfbdy_d01 {WRF_DIR}/run")

                print('Running simulation with new initial conditions...')
                os.system(f"cp wrfvar_output {WRF_DIR}/run/wrfinput_d01")
                run_wrf.call_model('wrf', WRF_DIR, ntasks, srun, output=f"{output}/e{str(i).zfill(3)}")
                print_msg(f"Ensemble member {i} created", 'okgreen')

        print_msg(f"Ensemble generated succesfully", 'okgreen')
    else:
        call_model(WRF_DIR, WRFDA_DIR, ntasks, srun)
        os.system(f"cp wrfvar_output {output}/wrfvar_output")

    print_msg("{:.3f} seconds".format(time.time() - start), 'okgreen')
