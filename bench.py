#!/usr/bin/env python3

import argparse
import atexit
import datetime
import importlib
import os
import pickle
import subprocess
import traceback

import src.facter
import src.globalvars
from src.util import *


bench_dir = "src/benchmarks"
benchmarks = [e[:-3] for e in os.listdir(bench_dir)
                     if e[-3:] == ".py" and e != "__init__.py"]

parser = argparse.ArgumentParser(description="benchmark memory allocators")
parser.add_argument("-ds, --dont-save", action='store_true', dest="dont_save",
                    help="don't save benchmark results in RESULTDIR")
parser.add_argument("-l", "--load", help="load benchmark results from directory", type=str)
parser.add_argument("-a", "--allocators", help="load allocator definitions from file", type=str)
parser.add_argument("--analyse", help="analyse benchmark behaviour using malt", action="store_true")
parser.add_argument("-r", "--runs", help="how often the benchmarks run", default=3, type=int)
parser.add_argument("-v", "--verbose", help="more output", action='count')
parser.add_argument("-vdebug", "--verbose-debug", help="debug output",
                    action='store_true', dest="verbose_debug")
parser.add_argument("-b", "--benchmarks", help="benchmarks to run", nargs='+')
parser.add_argument("-ns", "--nosum", help="don't produce plots", action='store_true')
parser.add_argument("-rd", "--resultdir", help="directory where all results go", type=str)
parser.add_argument("--license", help="print license info and exit", action='store_true')


"""Run tasks on exit"""
def epilog():
    # After early errors resdir may not be set
    if src.globalvars.resdir != None:
        if os.listdir(src.globalvars.resdir) == []:
            print_warn("Remove empty resultdir")
            os.removedirs(src.globalvars.resdir)
        else:
            endtime = datetime.datetime.now().isoformat()
            endtime = endtime[:endtime.rfind(':')]
            src.globalvars.facts["endtime"] = endtime
            with open(os.path.join(src.globalvars.resdir, "facts.save"), "wb") as f:
                pickle.dump(src.globalvars.facts, f)

def main():
    args = parser.parse_args()
    if args.license:
        print("Copyright (C) 2018-2019 Florian Fischer")
        print("License GPLv3: GNU GPL version 3 <http://gnu.org/licenses/gpl.html>")
        return

    atexit.register(epilog)

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

    # collect facts
    src.facter.collect_facts()

    # Default allocator definition file
    allocators_file = os.path.join("build", "allocators", "allocators.py")

    if args.allocators or os.path.isfile(allocators_file):
        allocators_file = args.allocators or allocators_file
        src.globalvars.allocators_file = allocators_file

        with open(allocators_file, "r") as f:
            print_status("Sourcing allocators definitions at", allocators_file,
                         "...")
            g = {}
            exec(f.read(), g)
        src.globalvars.allocators = g["allocators"]
    else:
        print_status("Using system-wide installed allocators ...")
        # Normal import fails
        importlib.import_module('src.allocators.installed_allocators')

    print_info("Allocators:", *src.globalvars.allocators.keys())

    # Load facts
    if args.load:
        with open(os.path.join(args.load, "facts.save"), "rb") as f:
            old_facts = pickle.load(f)

        if old_facts != src.globalvars.facts and args.runs > 0:
            print_error("Can't combine benchmarks with different facts")
            print_error("Aborting.")
            exit(1)
        # We are just summarizing old results -> use their facts
        elif args.runs == 0:
            src.globalvars.facts = old_facts
    else:
        starttime = datetime.datetime.now().isoformat()
        # strip seconds from string
        starttime = starttime[:starttime.rfind(':')]
        src.globalvars.facts["starttime"] = starttime

    # Create result directory if we analyse, save or summarize
    need_resultdir = not (args.nosum and args.dont_save and not args.analyse)
    if need_resultdir:
        if args.resultdir:
            resdir = os.path.join(args.resultdir)
        else:
            resdir = os.path.join("results", src.globalvars.facts["hostname"],
                                    src.globalvars.facts["starttime"])
        # make resdir globally available
        src.globalvars.resdir = resdir

        print_info2("Creating result dir:", resdir)
        os.makedirs(resdir, exist_ok=True)

    # TODO load all results at once

    cwd = os.getcwd()
    for bench in benchmarks:
        if args.benchmarks and not bench in args.benchmarks:
            continue

        if args.analyse or not args.nosum:
            bench_res_dir = os.path.join(resdir, bench)
            print_info2("Creating benchmark result dir:", bench_res_dir)
            os.makedirs(bench_res_dir, exist_ok=True)

        try:
            bench = eval("importlib.import_module('src.benchmarks.{0}').{0}".format(bench))

            if args.load:
                bench.load(path=args.load)

            if args.runs > 0 or args.analyse:
                print_status("Preparing", bench.name, "...")
                bench.prepare()

            if args.analyse:
                if find_cmd("malt") is not None:
                    print_status("Analysing {} ...".format(bench))


                    malt_cmd = "malt -o output:name={}/malt.{}.%3"
                    malt_cmd = malt_cmd.format(bench_res_dir, "{perm}")

                    old_allocs = bench.allocators
                    # use malt as allocator
                    src.globalvars.allocators = {"malt": {"cmd_prefix"    : malt_cmd,
                                                          "binary_suffix" : "",
                                                          "LD_PRELOAD"    : ""}}
                    try:
                        bench.run(runs=1)
                    except Exception:
                        print_error(traceback.format_exc())
                        print_error("Skipping analysis of", bench, "!")

                    if "malt" in bench.results:
                        del(bench.results["malt"])
                    if "malt" in bench.results["stats"]
                        del(bench.results["stats"]["malt"])
                    # restore allocs
                    bench.allocators = old_allocs

                else:
                    print_error("malt not found. Skipping analyse.")

            bench.run(runs=args.runs)

            if need_resultdir:
                print_info2("Changing cwd to:", resdir)
                os.chdir(resdir)

                if not args.dont_save:
                    bench.save()

                if not args.nosum:
                    os.chdir(bench.name)
                    print_status("Summarizing", bench.name, "...")
                    bench.summary()

                os.chdir(cwd)

            if args.runs > 0 and hasattr(bench, "cleanup"):
                print_status("Cleaning up", bench.name, "...")
                bench.cleanup()

        except Exception:
            # Reset cwd
            os.chdir(cwd)

            print_error(traceback.format_exc())
            print_error("Skipping", bench, "!")

            continue


if __name__ == "__main__":
    main()
