#!/usr/bin/env python3
#
# Author vdguevara@uninorte.edu.co
# More info: https://aml-cs.github.io
#

import sys, os
import requests
from datetime import datetime


def check_file_status(filepath, filesize):
    sys.stdout.write('\r')
    sys.stdout.flush()
    size = int(os.stat(filepath).st_size)
    percent_complete = (size/filesize)*100
    print_progress_bar(size, filesize)

def print_progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '*', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

path = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/'
today = datetime.now()
start = 0
end = 24
time = "18"

if len(sys.argv) == 2:
    time = sys.argv[1]

for i in range(start, end+1, 3):
    filename = "gfs.{0:%Y}{0:%m}{0:%d}/{2}/atmos/gfs.t{2}z.pgrb2full.0p50.f{1}".format(today, str(i).zfill(3), time)
    fullname = path + filename
    print(fullname)
    file_base = os.path.basename(filename)
    print(f"Downloading {file_base}")
    req = requests.get(fullname, stream=True)
    filesize = int(req.headers['Content-Length'])
    print(f"Size: {filesize/1024**2} MiB")
    with open(file_base, 'wb') as outfile:
        chunk_size = 1048576
        for chunk in req.iter_content(chunk_size=chunk_size):
            outfile.write(chunk)
            if chunk_size < filesize:
                check_file_status(file_base, filesize)

print("Downloads completed!")
