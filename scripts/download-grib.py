#!/usr/bin/env python3
#################################################################
# Python Script to retrieve 120 online Data files of 'ds083.2',
# total 3.09G. This script uses 'requests' to download data.
#
# Highlight this script by Select All, Copy and Paste it into a file;
# make the file executable and run it on command line.
#
# You need pass in your password as a parameter to execute
# this script; or you can set an environment variable RDAPSWD
# if your Operating System supports it.
#
# Contact rpconroy@ucar.edu (Riley Conroy) for further assistance.
#################################################################


import sys, os
import requests
from datetime import datetime, timedelta

def check_file_status(filepath, filesize):
    sys.stdout.write('\r')
    sys.stdout.flush()
    size = int(os.stat(filepath).st_size)
    percent_complete = (size/filesize)*100
    sys.stdout.write('%.3f %s' % (percent_complete, '% Completed'))
    sys.stdout.flush()

email = input('Email: ')
# Try to get password
try:
    import getpass
    input = getpass.getpass
except:
    try:
        input = raw_input
    except:
        pass

pswd = input('Password: ')

url = 'https://rda.ucar.edu/cgi-bin/login'
values = {'email' : email , 'passwd' : pswd, 'action' : 'login'}
# Authenticate
ret = requests.post(url,data=values)
if ret.status_code != 200:
    print('Bad Authentication')
    print(ret.text)
    exit(1)
dspath = 'https://rda.ucar.edu/data/ds083.2/'

start_date = datetime.strptime(sys.argv[1], '%Y-%m-%d')
end_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)+1):
            yield start_date + timedelta(n)
def pad_zero(time: str):
    if len(time) == 1:
        return f"0{time}"
    else:
        return time


filelist = []

for date in daterange(start_date, end_date):
    for i in range(0, 19, 6):
        filelist.append('grib2/{0:%Y}/{0:%Y}.{0:%m}/fnl_{0:%Y}{0:%m}{0:%d}_{1}_00.grib2'.format(date, pad_zero(str(i))))

#'grib2/2020/2020.11/fnl_20201130_18_00.grib2'

for file in filelist:
    filename=dspath+file
    file_base = os.path.basename(file)
    print('Downloading',file_base)
    req = requests.get(filename, cookies = ret.cookies, allow_redirects=True, stream=True)
    filesize = int(req.headers['Content-length'])
    with open(file_base, 'wb') as outfile:
        chunk_size=1048576
        for chunk in req.iter_content(chunk_size=chunk_size):
            outfile.write(chunk)
            if chunk_size < filesize:
                check_file_status(file_base, filesize)
    check_file_status(file_base, filesize)
    print()

