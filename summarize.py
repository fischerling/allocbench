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
"""Summarize the results of an allocbench run"""

import argparse
import os
import sys

from allocbench.directories import set_current_result_dir, get_current_result_dir
import allocbench.facter as facter
import allocbench.globalvars
import allocbench.benchmark
import allocbench.util
from allocbench.util import print_status, print_debug, print_error
from allocbench.util import print_license_and_exit


def specific_summary(bench, sum_dir, allocators):
    """Summarize bench in sum_dir for allocators"""
    old_allocs = bench.results["allocators"]
    allocs_in_set = {k: v for k, v in old_allocs.items() if k in allocators}

    if not allocs_in_set:
        return

    # create and change to sum_dir
    os.mkdir(sum_dir)
    os.chdir(sum_dir)

    bench.results["allocators"] = allocs_in_set

    # set colors
    explicit_colors = [
        v["color"] for k, v in allocs_in_set.items() if v["color"] is not None
    ]
    print_debug("Explicit colors:", explicit_colors)

    cycle_list = ["C" + str(i) for i in range(0, 10)]
    avail_colors = [
        color for color in cycle_list if color not in explicit_colors
    ]
    print_debug("available colors:", avail_colors)

    for _, value in allocs_in_set.items():
        if value["color"] is None:
            value["color"] = avail_colors.pop()

    allocbench.globalvars.ALLOCATORS = allocators

    bench.summary()
    bench.results["allocators"] = old_allocs
    os.chdir("..")


def bench_sum(bench, exclude_allocators=None, sets=False):
    """Create a summary of bench for each set of allocators"""

    new_allocs = {
        an: a
        for an, a in bench.results["allocators"].items()
        if an not in (exclude_allocators or {})
    }
    bench.results["allocators"] = new_allocs

    os.makedirs(bench.name)
    os.chdir(bench.name)

    os.mkdir("all")
    os.chdir("all")
    bench.summary()
    os.chdir("..")

    if sets:
        sets = {
            "glibcs": [
                "glibc", "glibc-noThreadCache", "glibc-noFalsesharing",
                "glibc-noFalsesharingClever"
            ],
            "tcmalloc": ["TCMalloc", "TCMalloc-NoFalsesharing"],
            "nofs": [
                "glibc", "glibc-noFalsesharing", "glibc-noFalsesharingClever",
                "TCMalloc", "TCMalloc-NoFalsesharing"
            ],
            "ba": ["glibc", "TCMalloc", "jemalloc", "Hoard"],
            "industry": [
                "glibc", "llalloc", "TCMalloc", "jemalloc", "tbbmalloc",
                "mimalloc"
            ],
            "research":
            ["scalloc", "SuperMalloc", "Mesh", "Hoard", "snmalloc"]
        }
    else:
        sets = {}

    for set_name, set_allocators in sets.items():
        specific_summary(bench, set_name, set_allocators)

    os.chdir("..")


def summarize(benchmarks=None,
              exclude_benchmarks=None,
              exclude_allocators=None,
              sets=False):
    """summarize the benchmarks in the resdir"""

    cwd = os.getcwd()
    os.chdir(get_current_result_dir())

    for benchmark in allocbench.benchmark.AVAIL_BENCHMARKS:
        if benchmarks and not benchmark in benchmarks:
            continue
        if exclude_benchmarks and benchmark in exclude_benchmarks:
            continue

        try:
            bench = allocbench.benchmark.get_benchmark_object(benchmark)
        except Exception:  #pylint: disable=broad-except
            print_error(f"Skipping {benchmark}. Loading failed")
            continue

        try:
            bench.load()
        except FileNotFoundError:
            continue

        print_status(f"Summarizing {bench.name} ...")
        try:
            bench_sum(bench, exclude_allocators=exclude_allocators, sets=sets)
        except FileExistsError as err:
            print(err)

    os.chdir(cwd)


def main():
    """Summarize the results of an allocbench run"""
    parser = argparse.ArgumentParser(
        description="Summarize allocbench results in allocator sets")
    parser.add_argument("results", help="path to results", type=str)
    parser.add_argument("-t",
                        "--file-ext",
                        help="file extension used for plots",
                        type=str)
    parser.add_argument("--license",
                        help="print license info and exit",
                        action='store_true')
    parser.add_argument("--version",
                        help="print version info and exit",
                        action='version',
                        version=f"allocbench {facter.allocbench_version()}")
    parser.add_argument("-v", "--verbose", help="more output", action='count')
    parser.add_argument("-b",
                        "--benchmarks",
                        help="benchmarks to summarize",
                        nargs='+')
    parser.add_argument("-x",
                        "--exclude-benchmarks",
                        help="benchmarks to exclude",
                        nargs='+')
    parser.add_argument("-xa",
                        "--exclude-allocators",
                        help="allocators to exclude",
                        nargs='+')
    parser.add_argument(
        "--latex-preamble",
        help="latex code to include in the preamble of generated standalones",
        type=str)
    parser.add_argument("-i",
                        "--interactive",
                        help="drop into repl after summarizing the results",
                        action='store_true')
    parser.add_argument("-s",
                        "--sets",
                        help="create summary for sets of allocators",
                        action='store_true')

    args = parser.parse_args()

    if args.verbose:
        allocbench.util.VERBOSITY = args.verbose

    if args.file_ext:
        allocbench.plots.summary_file_ext = args.file_ext

    if args.latex_preamble:
        allocbench.plots.latex_custom_preamble = args.latex_preamble

    if not os.path.isdir(args.results):
        print_error(f"{args.results} is no directory")
        sys.exit(1)

    set_current_result_dir(args.results)

    # Load facts
    facter.load_facts(get_current_result_dir())

    summarize(benchmarks=args.benchmarks,
              exclude_benchmarks=args.exclude_benchmarks,
              exclude_allocators=args.exclude_allocators,
              sets=args.sets)

    if args.interactive:
        try:
            import IPython  # pylint: disable=import-outside-toplevel
            IPython.embed()
        except ModuleNotFoundError:
            import code  # pylint: disable=import-outside-toplevel
            code.InteractiveConsole(locals=globals()).interact()


if __name__ == "__main__":
    if "--license" in sys.argv:
        print_license_and_exit()

    main()
