#!/usr/bin/env python3

import argparse
import datetime
import importlib
import os
import subprocess

import src.allocators
import src.facter
import src.globalvars
from src.util import *


benchmarks = ["loop", "mysql", "falsesharing", "dj_trace", "larson"]

parser = argparse.ArgumentParser(description="benchmark memory allocators")
parser.add_argument("-ds, --dont-save", action='store_true', dest="dont_save",
                    help="don't save benchmark results in RESULTDIR")
parser.add_argument("-l", "--load", help="load benchmark results from directory", type=str)
parser.add_argument("-a", "--allocators", help="load allocator definitions from file", type=str)
parser.add_argument("-r", "--runs", help="how often the benchmarks run", default=3, type=int)
parser.add_argument("-v", "--verbose", help="more output", action='count')
parser.add_argument("-vdebug", "--verbose-debug", help="debug output",
                    action='store_true', dest="verbose_debug")
parser.add_argument("-b", "--benchmarks", help="benchmarks to run", nargs='+')
parser.add_argument("-ns", "--nosum", help="don't produce plots", action='store_true')
parser.add_argument("-rd", "--resultdir", help="directory where all results go", type=str)
parser.add_argument("--license", help="print license info and exit", action='store_true')


def main():
    args = parser.parse_args()
    if args.license:
        print("Copyright (C) 2018-2019 Florian Fischer")
        print("License GPLv3: GNU GPL version 3 <http://gnu.org/licenses/gpl.html>")
        return

    # Set global verbosity
    # quiet | -1: Don't output to stdout
    # default | 0: Only print status and errors
    # 1: Print warnings and some infos
    # 2: Print all infos
    # debug | 99: Print all awailable infos
    if args.verbose_debug:
        src.globalvars.verbosity = 99
    elif args.verbose:
        src.globalvars.verbosity = args.verbose

    verbosity = src.globalvars.verbosity

    print_info2("Arguments:", args)

    # Prepare allocbench
    print_status("Building allocbench ...")
    make_cmd = ["make"]
    if verbosity < 1:
        make_cmd.append("-s")
    else:
        # Flush stdout so the color reset from print_status works
        print("", end="", flush=True)

    subprocess.run(make_cmd)

    allocators_file = os.path.join("build", "allocators", "allocators.py")

    if args.allocators or os.path.isfile(allocators_file):
        allocators_file = args.allocators or allocators_file
        src.globalvars.allocators_file = allocators_file

        with open(allocators_file, "r") as f:
            print_status("Sourcing allocators definition ...")
            g = {}
            exec(f.read(), g)
        src.allocators.allocators = g["allocators"]

    print_info("Allocators:", *src.allocators.allocators.keys())

    # Create result directory if we save or summarize results
    need_resultdir = not (args.nosum and args.dont_save)
    if need_resultdir:
        if args.resultdir:
            resdir = os.path.join(args.resultdir)
        else:
            hostname = src.facter.get_hostname()
            # TODO use saved hostname
            if args.load and args.runs < 2:
                pass
            resdir = os.path.join("results", hostname,
                                    datetime.datetime.now().strftime("%Y-%m-%dT%H:%M"))
        try:
            print_info2("Creating result dir:", resdir)
            os.makedirs(resdir)
        except FileExistsError:
            pass

    # TODO load all results at once

    for bench in benchmarks:
        if args.benchmarks and not bench in args.benchmarks:
            continue

        bench = eval("importlib.import_module('src.{0}').{0}".format(bench))

        if args.load:
            bench.load(path=args.load)

        if args.runs > 0:
            print_status("Preparing", bench.name, "...")
            if not bench.prepare():
                print_error("Preparing", bench.name, "failed!")
                continue

        print_status("Running", bench.name, "...")
        if not bench.run(runs=args.runs):
            continue

        if need_resultdir:
            print_info2("Changing cwd to:", resdir)
            old_cwd = os.getcwd()
            os.chdir(resdir)

            if not args.dont_save:
                bench.save()

            if not args.nosum:
                try:
                    os.mkdir(bench.name)
                except FileExistsError:
                    pass
                os.chdir(bench.name)
                print_status("Summarizing", bench.name, "...")
                bench.summary()

            os.chdir(old_cwd)

        if args.runs > 0 and hasattr(bench, "cleanup"):
            print_status("Cleaning up", bench.name, "...")
            bench.cleanup()

if __name__ == "__main__":
    main()
