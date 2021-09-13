#!/usr/bin/env python3
import os
import re
import subprocess

def update_namelist(namelist_path, options):
    with open(namelist_path, "rw") as namelist:
        content = namelist.read()
        for (key, value) in options.items():
           content = re.sub(r'(' + key + '\s*\=)(.*),', r'\1'+ value + ',')
        namelist.write(content)

def set_namelist_value(key, value):


if __name__ == '__main__':
    DATA_DIR = os.environ['DATA_DIR']
    WRFDA_DIR = os.environ['WRFDA_DIR']

    os.system("rm -rf $WRFDA_DIR/ob*.bufr")

    folder = f"{DATA_DIR}/prep-data"
    if (not os.path.isdir(folder)):
        raise ValueError(f"{folder} not found")

    subprocess.run(["chmod", "777", "-R", folder])

    for idx, filename in enumerate(glob.glob(f"{folder}/*")):
        linkname = f"ob{pad_zero(idx+1)}.bufr"
        subprocess.run(["ln", "-s", filename, f"{WRFDA_DIR}/{linkname}"])

    print("prep-data links created successfully!")