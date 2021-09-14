#!/usr/bin/env python3

import os
import subprocess
import glob

if __name__ == '__main__':
    WRFDA_DIR = os.environ.get('WRFDA_DIR', None)
    if WRFDA_DIR is None:
        raise Exception('Module wrfda not loaded')

    DATA_DIR = os.environ.get('DATA_DIR', None)

    os.system(f"rm -rf {WRFDA_DIR}/ob*.bufr")

    folder = f"{DATA_DIR}/prep-data"
    if (not os.path.isdir(folder)):
        raise Exception(f"{folder} not found")

    subprocess.run(["chmod", "777", "-R", folder])

    for idx, filename in enumerate(glob.glob(f"{folder}/*")):
        linkname = f"ob{str(idx+1).zfill(2)}.bufr"
        subprocess.run(["ln", "-s", filename, f"{WRFDA_DIR}/{linkname}"])

    print("prep-data links created successfully!")