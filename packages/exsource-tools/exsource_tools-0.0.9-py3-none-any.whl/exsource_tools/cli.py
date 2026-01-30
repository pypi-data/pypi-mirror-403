"""
All of the functions called by the CLI
"""

from os import path
import argparse

from exsource_tools.tools import load_exsource_file, ExSourceProcessor

DEF_HELP = "Path to ExSource definition file. Default is exsource-def.yml or exsource-def.json"
OUT_HELP = "Path to ExSource output file. Default is exsource-out.yml or exsource-out.json"


def make_parser():
    """
    Create the argument parser for the exsource-make command
    """
    description = "Process exsource file to create inputs."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--exsource-def", help=DEF_HELP)
    parser.add_argument("-o", "--exsource-out", help=OUT_HELP)
    headless_help = ("Set this flag on machines without an X server running. Commands "
                     "requring X will be run with xvfb. Ensure xvfb is installed.")
    parser.add_argument("-H", "--headless", action='store_true', help=headless_help)
    return parser

def check_parser():
    """
    Create the argument parser for the exsource-check command
    """
    description = "Check status of file listed in exsource files"
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--exsource-def", help=DEF_HELP)
    parser.add_argument("-o", "--exsource-out", help=OUT_HELP)
    return parser

def find_def_file():
    """
    Find the exsource definition file in the current directory.
    """
    default_names = ["exsource-def.yml", "exsource-def.yaml", "exsource-def.json"]
    for def_name in default_names:
        if path.isfile(def_name):
            return def_name
    return None

def find_out_file():
    """
    Find the exsource output file in the current directory.
    """
    default_names = ["exsource-out.yml", "exsource-out.yaml", "exsource-out.json"]
    for def_name in default_names:
        if path.isfile(def_name):
            return def_name
    return None

def process_file_args(args):
    """
    Process the args for exsource-make or exsource-check to return
    the correct loaded exsource-files and the ouput file name.
    """
    def_filepath = args.exsource_def
    if def_filepath is None:
        def_filepath = find_def_file()
    if def_filepath is None:
        #If still is None then error
        raise RuntimeError("Couldn't find ExSource definition file.")
    def_file = load_exsource_file(def_filepath)

    out_filepath = args.exsource_out
    if out_filepath is None:
        out_filepath = find_out_file()

    out_file = None
    if out_filepath is not None and path.exists(out_filepath):
        out_file = load_exsource_file(out_filepath)

    return def_file, out_file, out_filepath

def make():
    """
    This is the function run by the entrypoint exsource-make
    """
    parser = make_parser()
    args = parser.parse_args()

    def_file, out_file, out_filepath = process_file_args(args)

    processor = ExSourceProcessor(def_file, out_file, out_filepath, args.headless)
    processor.make()

def check():
    """
    This is the function run by the entrypoint exsource-check
    """
    parser = check_parser()
    args = parser.parse_args()

    def_file, out_file, _ = process_file_args(args)

    processor = ExSourceProcessor(def_file, out_file)
    processor.check()
