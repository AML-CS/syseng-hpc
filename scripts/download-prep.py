#!/usr/bin/env python3
#################################################################
# Python Script to retrieve 1 online Data file of 'ds337.0',
# total 91.07M. This script uses 'requests' to download data.
#
# Highlight this script by Select All, Copy and Paste it into a file;
# make the file executable and run it on command line.
#
# You need pass in your password as a parameter to execute
# this script; or you can set an environment variable RDAPSWD
# if your Operating System supports it.
#
# Contact tcram@ucar.edu (Thomas Cram) for further assistance.
#################################################################


import sys, os
import glob
from pathlib import Path
import requests
from datetime import datetime, timedelta

def check_file_status(filepath, filesize):
    sys.stdout.write('\r')
    sys.stdout.flush()
    size = int(os.stat(filepath).st_size)
    percent_complete = (size/filesize)*100
    sys.stdout.write('%.3f %s' % (percent_complete, '% Completed'))
    sys.stdout.flush()


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)+1):
        yield start_date + timedelta(n)
            
def pad_zero(idx):
    if idx < 10:
        return f"0{idx}"
    else:
        return idx

if __name__ == '__main__':
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
    values = {'email': email , 'passwd': pswd, 'action': 'login'}

    ret = requests.post(url,data=values)
    if ret.status_code != 200:
        print('Bad Authentication')
        print(ret.text)
        exit(1)

    start_date = datetime.strptime(sys.argv[1], '%Y-%m-%d')
    end_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')
    date_range = daterange(start_date, end_date) 

    dspath = 'https://rda.ucar.edu/data/ds337.0/'
    filelist = [('tarfiles/{0:%Y}/prepbufr.{0:%Y}{0:%m}{0:%d}.nr.tar.gz'.format(date), date) for date in date_range]
    Path('prep-data').mkdir(parents=True, exist_ok=True)

    for (file, date) in filelist:
        filename=dspath+file
        file_base = os.path.basename(file)
        print('Downloading',filename)
        req = requests.get(filename, cookies = ret.cookies, allow_redirects=True, stream=True)
        filesize = int(req.headers['Content-length'])
        with open(file_base, 'wb') as outfile:
            chunk_size=1048576
            for chunk in req.iter_content(chunk_size=chunk_size):
                outfile.write(chunk)
                if chunk_size < filesize:
                    check_file_status(file_base, filesize)
        check_file_status(file_base, filesize)

        filename="prepbufr.{0:%Y}{0:%m}{0:%d}.nr.tar.gz".format(date)
        folder="{0:%Y}{0:%m}{0:%d}.nr".format(date)
        os.system(f"tar xzf {filename}")
        os.system(f"mv {folder}/* prep-data && rm -rf {folder}")
        os.system(f"rm {filename}")
        print(f"{filename} unziped and saved in ./prep-data!")
    
    os.system('cd $WRFDA_DIR && rm -rf ob*.bufr')
    for idx, filename in enumerate(glob.glob(f"{os.getcwd()}/prep-data/*")):
        os.system(f"cd $WRFDA_DIR && ln -s {filename} ob{pad_zero(idx+1)}.bufr")
    
    print("Symbolic links created successfully!")