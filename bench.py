#!/usr/bin/env python3

# Copyright 2018-2020 Florian Fischer <florian.fl.fischer@fau.de>
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
import os
import sys
import traceback

from allocbench.allocator import collect_allocators
from allocbench.analyse import analyze_bench, analyze_allocators
from allocbench.benchmark import get_benchmark_object
from allocbench.directories import get_current_result_dir, set_current_result_dir
import allocbench.facter as facter
import allocbench.globalvars
from allocbench.util import run_cmd
from allocbench.util import print_status, print_warn, print_error
from allocbench.util import print_info, print_info2, print_debug
from allocbench.util import print_license_and_exit

from summarize import summarize


def epilog():
    """Run tasks on exit"""
    # remove a left over status file if some is present
    if os.path.exists("status"):
        os.remove("status")

    res_dir = get_current_result_dir()
    # After early errors resdir may not be set
    if not res_dir:
        return

    if not res_dir.iterdir():
        print_warn("Remove empty resultdir")
        res_dir.rmdir()
    else:
        endtime = datetime.datetime.now().isoformat()
        endtime = endtime[:endtime.rfind(':')]
        facter.FACTS["endtime"] = endtime
        facter.store_facts(res_dir)


def check_dependencies():
    """Check if known requirements of allocbench are met"""
    # used python 3.6 features: f-strings
    if sys.version_info[0] < 3 or sys.version_info[1] < 6:
        print_error("At least python version 3.6 is required.")
        sys.exit(1)


def main():
    check_dependencies()

    parser = argparse.ArgumentParser(description="benchmark memory allocators")
    parser.add_argument("--analyze",
                        help="analyze benchmark behavior",
                        action="store_true")
    parser.add_argument("--analyze-allocators",
                        help="analyze allocator behavior",
                        action="store_true")
    parser.add_argument("-r",
                        "--runs",
                        help="how often the benchmarks run",
                        default=3,
                        type=int)
    parser.add_argument("-v", "--verbose", help="more output", action='count')
    parser.add_argument("-b",
                        "--benchmarks",
                        help="benchmarks to run",
                        nargs='+')
    parser.add_argument("-xb",
                        "--exclude-benchmarks",
                        help="explicitly excluded benchmarks",
                        nargs='+')
    parser.add_argument("-a",
                        "--allocators",
                        help="allocators to test",
                        type=str,
                        nargs='+',
                        default=["all"])
    parser.add_argument("-rd",
                        "--resultdir",
                        help="directory where all results go",
                        type=str)
    parser.add_argument("-s",
                        "--summarize",
                        help="create a summary of this run",
                        action='store_true')
    parser.add_argument("--license",
                        help="print license info and exit",
                        action='store_true')
    parser.add_argument("--version",
                        help="print version info and exit",
                        action='version',
                        version=f"allocbench {facter.allocbench_version()}")

    args = parser.parse_args()
    if args.license:
        print_license_and_exit()

    atexit.register(epilog)

    # Set global verbosity
    # quiet | -1: Don't output to stdout
    # default | 0: Only print status and errors
    # 1: Print warnings and some infos
    # 2: Print all infos
    # 3: Print everything
    if args.verbose:
        allocbench.globalvars.VERBOSITY = args.verbose

    print_info2("Arguments:", args)

    # Prepare allocbench
    print_status("Building allocbench ...")
    make_cmd = ["make"]
    if allocbench.globalvars.VERBOSITY < 2:
        make_cmd.append("-s")
    run_cmd(make_cmd, output_verbosity=1)

    # allocators to benchmark
    allocbench.globalvars.ALLOCATORS = collect_allocators(args.allocators)

    print_info("Allocators:", *allocbench.globalvars.ALLOCATORS.keys())
    print_debug("Allocators:", *allocbench.globalvars.ALLOCATORS.items())

    if allocbench.globalvars.ALLOCATORS == {}:
        print_error("Abort because there are no allocators to benchmark")
        sys.exit(1)

    # collect facts about benchmark environment
    facter.collect_facts()

    # Create result directory
    if args.resultdir:
        set_current_result_dir(args.resultdir)
    else:
        set_current_result_dir(
            os.path.join("results", facter.FACTS["hostname"],
                         facter.FACTS["starttime"]))

    print_status("Writing results to:", get_current_result_dir())

    cwd = os.getcwd()

    # warn about unknown benchmarks
    for bench in (args.benchmarks or []) + (args.exclude_benchmarks or []):
        if bench not in allocbench.globalvars.BENCHMARKS:
            print_error(f'Benchmark "{bench}" unknown!')

    # Run actual benchmarks
    for bench in allocbench.globalvars.BENCHMARKS:
        if args.benchmarks and bench not in args.benchmarks:
            continue

        if args.exclude_benchmarks and bench in args.exclude_benchmarks:
            continue

        try:
            print_status("Loading", bench, "...")
            bench = get_benchmark_object(bench)
        except Exception:  #pylint: disable=broad-except
            print_error(traceback.format_exc())
            print_error(f"Skipping {bench}! Loading failed.")
            continue

        try:
            print_status("Preparing", bench, "...")
            bench.prepare()
        except Exception:  #pylint: disable=broad-except
            print_error(traceback.format_exc())
            print_error(f"Skipping {bench}! Preparing failed.")
            continue

        if args.analyze:
            analyze_bench(bench)

        if args.analyze_allocators:
            analyze_allocators(bench, allocbench.globalvars.ALLOCATORS)

        if args.runs > 0:
            print_status("Running", bench.name, "...")
            start_time = datetime.datetime.now()
            bench.results['facts']['start-time'] = start_time.isoformat()
            try:
                bench.run(runs=args.runs)
            except Exception:  #pylint: disable=broad-except
                # Reset cwd
                os.chdir(cwd)
                print_error(traceback.format_exc())
                print_error("Skipping", bench, "!")
                continue

            end_time = datetime.datetime.now()
            bench.results['facts']['end-time'] = end_time.isoformat()
            bench.results['facts']['duration'] = (end_time -
                                                  start_time).total_seconds()

        # Save results in resultdir
        bench.save(get_current_result_dir())

        if hasattr(bench, "cleanup"):
            print_status("Cleaning up", bench.name, "...")
            bench.cleanup()

        if args.summarize:
            summarize()


if __name__ == "__main__":
    main()
