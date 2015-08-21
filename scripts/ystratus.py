#!/usr/bin/env python
"""
Script or converting YAML formatted files to JSON. Specifically,
YAML incorporating the YAML Stratus format is handled.
"""
import os

import argparse

import yamlstratus

desc = "Convert YAML Stratus format to json"

parser = argparse.ArgumentParser(description=desc)

parser.add_argument("src",
                    metavar="src",
                    nargs='+',
                    help="the name of the source file")

parser.add_argument("-i",
                    "--include-dirs",
                    help="the search path of include files")

parser.add_argument("-r",
                    "--root-tag",
                    help="the source tag that forms the root of the " +
                         "returned document")

parser.add_argument("-o",
                    "--output-dir",
                    help="the destination directory of generated file")

parser.add_argument('-P',
                    "--param",
                    nargs=1,
                    action="append",
                    help="Parameter to set. Ex -P LoadBalancerDnsWeight=5")

args = parser.parse_args()

incdirs = (args.include_dirs or ".").split(os.pathsep)
outdir = args.output_dir or "target"
params = args.param or []
root_tag = args.root_tag or "main"

params_dict = dict()
for param in params:
    param_name, param_value = param[0].split('=')
    params_dict[param_name] = param_value

if not os.path.exists(outdir):
    os.makedirs(outdir)

for filename in args.src:
    output_file_name = os.path.splitext(os.path.basename(filename))[0] + '.json'
    if outdir is not None:
        output_file_name = os.path.join(outdir, output_file_name)

    with open(output_file_name, 'w') as out:
        with open(filename, 'r') as f:
            file_incdirs = incdirs + [os.path.dirname(filename)]
            for json_part in yamlstratus.load_all_as_json(
                    f,
                    include_dirs=file_incdirs,
                    params=params_dict,
                    root_tag=root_tag):
                out.write(json_part)
