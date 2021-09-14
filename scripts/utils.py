#!/usr/bin/env python3

import os
import re

B_COLORS = {
	'HEADER': '\033[95m',
	'OKBLUE': '\033[94m',
	'OKCYAN': '\033[96m',
	'OKGREEN': '\033[92m',
	'WARNING': '\033[93m',
	'FAIL': '\033[91m',
	'ENDC': '\033[0m',
	'BOLD': '\033[1m',
	'UNDERLINE': '\033[4m'
}
def print_msg(msg, type):
	print(f"{B_COLORS[type.upper()]}{msg}{B_COLORS['ENDC']}")

def update_namelist(namelist_path, options):
	namelist_file = open(namelist_path)
	content = namelist_file.read()
	namelist_file.close()

	namelist_file = open(namelist_path, 'w')
	for (key, value) in options.items():
		content = re.sub(r'(' + key + r'\s*\=).*,', r'\g<1> ' + str(value) + ',', content)
	namelist_file.write(content)
	namelist_file.close()

def update_env_variables(file_path, env_vars):
	f = open(file_path)
	content = f.read()
	f.close()

	f = open(file_path, 'w')
	for (key, value) in env_vars.items():
		content = re.sub(r'(export ' + key + r'=)\S+(.*)', r'\g<1>' + str(value) + r'\g<2>', content)
	f.write(content)
	f.close()
