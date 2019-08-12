#!/usr/bin/env python3

import argparse
import atexit
import datetime
import importlib
import os
import pickle
import subprocess
import sys
import traceback

import src.facter
import src.globalvars
from src.util import *


parser = argparse.ArgumentParser(description="benchmark memory allocators")
parser.add_argument("-ds, --dont-save", action='store_true', dest="dont_save",
                    help="don't save benchmark results in RESULTDIR")
parser.add_argument("-l", "--load", help="load benchmark results from directory", type=str)
parser.add_argument("--analyse", help="analyse benchmark behaviour using malt", action="store_true")
parser.add_argument("-r", "--runs", help="how often the benchmarks run", default=3, type=int)
parser.add_argument("-v", "--verbose", help="more output", action='count')
parser.add_argument("-vdebug", "--verbose-debug", help="debug output",
                    action='store_true', dest="verbose_debug")
parser.add_argument("-b", "--benchmarks", help="benchmarks to run", nargs='+')
parser.add_argument("-xb", "--exclude-benchmarks", help="explicitly excluded benchmarks", nargs='+')
parser.add_argument("-a", "--allocators", help="allocators to test", type=str, nargs='+')
parser.add_argument("-ns", "--nosum", help="don't produce plots", action='store_true')
parser.add_argument("-rd", "--resultdir", help="directory where all results go", type=str)
parser.add_argument("--license", help="print license info and exit", action='store_true')


def epilog():
    """Run tasks on exit"""
    # After early errors resdir may not be set
    if src.globalvars.resdir is not None:
        if os.listdir(src.globalvars.resdir) == []:
            print_warn("Remove empty resultdir")
            os.removedirs(src.globalvars.resdir)
        else:
            endtime = datetime.datetime.now().isoformat()
            endtime = endtime[:endtime.rfind(':')]
            src.globalvars.facts["endtime"] = endtime
            with open(os.path.join(src.globalvars.resdir, "facts.save"), "wb") as f:
                pickle.dump(src.globalvars.facts, f)


def check_dependencies():
    """Check if known requirements of allocbench are met"""
    # used python 3.6 features: f-strings
    if sys.version_info[0] < 3 or sys.version_info[1] < 6:
        logger.critical("At least python version 3.6 is required.")
        exit(1)

    # matplotlib is needed by Benchmark.plot_*
    try:
        import matplotlib
    except ModuleNotFoundError:
        logger.critical("matplotlib not found.")
        exit(1)
    # TODO mariadb


def main():
    check_dependencies()

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

    print_info2("Arguments:", args)

    # Prepare allocbench
    print_status("Building allocbench ...")
    make_cmd = ["make"]
    if src.globalvars.verbosity < 1:
        make_cmd.append("-s")
    else:
        # Flush stdout so the color reset from print_status works
        print("", end="", flush=True)
    subprocess.run(make_cmd)

    # collect facts about benchmark environment
    src.facter.collect_facts()

    # allocators to benchmark
    allocators = {}
    # Default allocators definition file
    default_allocators_file = "build/allocators/allocators.py"

    if args.allocators is None and os.path.isfile(default_allocators_file):
        # TODO: fix default allocator file
        # allocators.append(default_allocators_file)
        pass

    elif args.allocators is not None:
        for name in args.allocators:
            # file exists -> interpret as python file with a global variable allocators
            if os.path.isfile(name):
                with open(name, "r") as f:
                    print_status("Sourcing allocators definitions at", name, "...")
                    g = {}
                    exec(f.read(), g)

                if "allocators" in g:
                    allocators.update(g["allocators"])
                else:
                    print_error("No global dictionary 'allocators' in", name)

            # file is one of our allocator definitions import it
            elif os.path.isfile("src/allocators/" + name + ".py"):
                module = importlib.import_module('src.allocators.' + name)
                # name is collection
                if hasattr(module, "allocators"):
                    for alloc in module.allocators:
                        allocators[alloc.name] = alloc.build()
                # name is single allocator
                elif issubclass(getattr(module, name).__class__, src.allocator.Allocator):
                    allocators[name] = getattr(module, name).build()
            else:
                print_error(name, "is neither a python file or a known allocator definition.")
    else:
        print_status("Using system-wide installed allocators ...")
        importlib.import_module('src.allocators.installed_allocators')
        allocators = src.allocators.installed_allocators.allocators

    # set colors
    explicit_colors = [v["color"] for k, v in allocators.items() if v["color"] is not None]
    print_debug("Explicit colors:", explicit_colors)
    avail_colors = [color for color in ["C" + str(i) for i in range(0,16)] if color not in explicit_colors]
    print_debug("available colors:", avail_colors)

    for k, v in allocators.items():
        if v["color"] is None:
            v["color"] = avail_colors.pop()

    src.globalvars.allocators = allocators
    print_info("Allocators:", *src.globalvars.allocators.keys())
    print_debug("Allocators:", *src.globalvars.allocators.items())

    # Load old results
    if args.load:
        with open(os.path.join(args.load, "facts.save"), "rb") as f:
            old_facts = pickle.load(f)

        if old_facts != src.globalvars.facts and args.runs > 0:
            print_error("Can't combine benchmarks with different facts")
            print_error("Aborting.")
            exit(1)
        # We are just summarizing old results -> use their facts
        else:
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
        # Make resdir globally available
        src.globalvars.resdir = resdir

        print_info2("Creating result dir:", resdir)
        os.makedirs(resdir, exist_ok=True)

    # Run actual benchmarks
    cwd = os.getcwd()
    for bench in src.globalvars.benchmarks:
        if args.benchmarks and bench not in args.benchmarks:
            continue

        if args.exclude_benchmarks and bench in args.exclude_benchmarks:
            continue

        # Create result dir for this benchmark
        if args.analyse or not args.nosum:
            bench_res_dir = os.path.join(resdir, bench)
            print_info2("Creating benchmark result dir:", bench_res_dir)
            os.makedirs(bench_res_dir, exist_ok=True)

        try:
            bench_module = importlib.import_module(f"src.benchmarks.{bench}")
            if not hasattr(bench_module, bench):
                continue

            bench = getattr(bench_module, bench)

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
                    bench.allocators = {"malt": {"cmd_prefix":    malt_cmd,
                                                 "binary_suffix": "",
                                                 "LD_PRELOAD":    ""}}
                    try:
                        bench.run(runs=1)
                    except Exception:
                        print_error(traceback.format_exc())
                        print_error("Skipping analysis of", bench, "!")

                    # Remove malt from results
                    if "malt" in bench.results:
                        del(bench.results["malt"])
                    if "stats" in bench.results and "malt" in bench.results["stats"]:
                        del(bench.results["stats"]["malt"])

                    # restore allocs
                    bench.allocators = old_allocs

                else:
                    print_error("malt not found. Skipping analyse.")

            if args.runs > 1:
                print_status("Running", bench.name, "...")
            bench.run(runs=args.runs)

            if need_resultdir:
                print_info2("Changing cwd to:", resdir)
                os.chdir(resdir)

                # Save results in resultdir
                if not args.dont_save:
                    bench.save()

                # Summarize benchmark in benchmark specific resultdir
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
