#!/usr/bin/env python3

# Copyright 2018-2019 Florian Fischer <florian.fl.fischer@fau.de>
#
# This file is part of allocbench.
#
# allocbench is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# allocbench is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with allocbench.  If not, see <http://www.gnu.org/licenses/>.

"""Start an allocbench run"""

import argparse
import atexit
import datetime
import importlib
import os
import pickle
import subprocess
import sys
import traceback

from src.allocator import collect_allocators
import src.chattyparser
import src.facter
import src.globalvars
from src.util import find_cmd
from src.util import print_status, print_warn, print_error
from src.util import print_info, print_info2, print_debug
from src.util import print_license_and_exit


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
            with open(os.path.join(src.globalvars.resdir, "facts.save"), "wb") as facts_file:
                pickle.dump(src.globalvars.facts, facts_file)


def check_dependencies():
    """Check if known requirements of allocbench are met"""
    # used python 3.6 features: f-strings
    if sys.version_info[0] < 3 or sys.version_info[1] < 6:
        print_error("At least python version 3.6 is required.")
        exit(1)

    # matplotlib is needed by Benchmark.plot_*
    try:
        importlib.import_module("matplotlib")
    except ModuleNotFoundError:
        print_error("matplotlib not found.")
        exit(1)
    # TODO mariadb


def main():
    check_dependencies()

    parser = argparse.ArgumentParser(description="benchmark memory allocators")
    parser.add_argument("--analyze", help="analyze benchmark behavior using malt", action="store_true")
    parser.add_argument("-r", "--runs", help="how often the benchmarks run", default=3, type=int)
    parser.add_argument("-v", "--verbose", help="more output", action='count')
    parser.add_argument("-b", "--benchmarks", help="benchmarks to run", nargs='+')
    parser.add_argument("-xb", "--exclude-benchmarks", help="explicitly excluded benchmarks", nargs='+')
    parser.add_argument("-a", "--allocators", help="allocators to test", type=str, nargs='+',
                        default=["all"])
    parser.add_argument("-rd", "--resultdir", help="directory where all results go", type=str)
    parser.add_argument("--license", help="print license info and exit", action='store_true')

    args = parser.parse_args()
    if args.license:
        print_license_and_exit()

    atexit.register(epilog)

    # Set global verbosity
    # quiet | -1: Don't output to stdout
    # default | 0: Only print status and errors
    # 1: Print warnings and some infos
    # 2: Print all infos
    # 3: Print all awailable infos
    if args.verbose:
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

    # allocators to benchmark
    src.globalvars.allocators = collect_allocators(args.allocators)

    print_info("Allocators:", *src.globalvars.allocators.keys())
    print_debug("Allocators:", *src.globalvars.allocators.items())

    # collect facts about benchmark environment
    src.facter.collect_facts()

    # Create result directory
    if args.resultdir:
        src.globalvars.resdir = os.path.join(args.resultdir)
    else:
        src.globalvars.resdir = os.path.join("results",
                                             src.globalvars.facts["hostname"],
                                             src.globalvars.facts["starttime"])

    print_info2("Creating result dir:", src.globalvars.resdir)
    os.makedirs(src.globalvars.resdir, exist_ok=True)

    cwd = os.getcwd()

    # Run actual benchmarks
    for bench in src.globalvars.benchmarks:
        if args.benchmarks and bench not in args.benchmarks:
            continue

        if args.exclude_benchmarks and bench in args.exclude_benchmarks:
            continue

        bench_module = importlib.import_module(f"src.benchmarks.{bench}")

        if not hasattr(bench_module, bench):
            print_error(f"{bench_module} has no member {bench}.")
            print_error(f"Skipping {bench_module}")
            continue

        bench = getattr(bench_module, bench)

        print_status("Preparing", bench.name, "...")
        bench.prepare()

        if args.analyze:
            print_status("Analysing {} ...".format(bench))

            # Create benchmark result directory
            if not os.path.isdir(bench.result_dir):
                print_info2("Creating benchmark result dir:", bench.result_dir)
                os.makedirs(bench.result_dir, exist_ok=True)

            if find_cmd("malt") is not None:
                analyze_alloc = "malt"
            else:
                print_warn("malt not found. Using chattymalloc.")
                analyze_alloc = "chattymalloc"

            old_allocs = bench.allocators
            analyze_alloc_module = importlib.import_module(f"src.allocators.{analyze_alloc}")
            bench.allocators = {analyze_alloc: getattr(analyze_alloc_module, analyze_alloc).build()}

            try:
                bench.run(runs=1)
            except Exception:
                print_error(traceback.format_exc())
                print_error("Skipping analysis of", bench, "!")

            # Remove results for analyze_alloc
            if analyze_alloc in bench.results:
                del bench.results[analyze_alloc]
            if "stats" in bench.results and analyze_alloc in bench.results["stats"]:
                del bench.results["stats"][analyze_alloc]

            # restore allocs
            bench.allocators = old_allocs

        if args.runs > 0:
            print_status("Running", bench.name, "...")
            try:
                bench.run(runs=args.runs)
            except Exception:
                # Reset cwd
                os.chdir(cwd)

                print_error(traceback.format_exc())
                print_error("Skipping", bench, "!")

                continue

        # Save results in resultdir
        bench.save(os.path.join(src.globalvars.resdir, f"{bench.name}.save"))

        if hasattr(bench, "cleanup"):
            print_status("Cleaning up", bench.name, "...")
            bench.cleanup()


if __name__ == "__main__":
    main()
