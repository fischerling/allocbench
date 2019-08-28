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

"""Summarize the results of an allocbench run"""

import argparse
import importlib
import os
import pickle
import sys

import src.globalvars
from src.util import print_status, print_debug, print_error
from src.util import print_license_and_exit


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
    explicit_colors = [v["color"] for k, v in allocs_in_set.items()
                       if v["color"] is not None]
    print_debug("Explicit colors:", explicit_colors)

    cycle_list = ["C" + str(i) for i in range(0, 16)]
    avail_colors = [color for color in cycle_list
                    if color not in explicit_colors]
    print_debug("available colors:", avail_colors)

    for _, value in allocs_in_set.items():
        if value["color"] is None:
            value["color"] = avail_colors.pop()

    src.globalvars.allocators = allocators

    bench.summary()
    bench.results["allocators"] = old_allocs
    os.chdir("..")


def bench_sum(bench):
    """Create a summary of bench for each set of allocators"""
    sets = {"glibcs": ["glibc", "glibc-noThreadCache", "glibc-noFalsesharing",
                       "glibc-noFalsesharingClever"],
            "tcmalloc": ["TCMalloc", "TCMalloc-NoFalsesharing"],
            "nofs": ["glibc", "glibc-noFalsesharing", "glibc-noFalsesharingClever",
                     "TCMalloc", "TCMalloc-NoFalsesharing"],
            "ba" : ["glibc", "TCMalloc", "jemalloc", "Hoard"],
            "industry" : ["glibc", "llalloc", "TCMalloc", "jemalloc", "tbbmalloc", "mimalloc"],
            "research" : ["scalloc", "SuperMalloc", "Mesh", "Hoard", "snmalloc"]}

    os.makedirs(bench.name)
    os.chdir(bench.name)

    os.mkdir("all")
    os.chdir("all")
    bench.summary()
    os.chdir("..")

    for set_name in sets:
        specific_summary(bench, set_name, sets[set_name])

    os.chdir("..")


def main():
    if "--license" in sys.argv:
        print_license_and_exit()

    parser = argparse.ArgumentParser(description="Summarize allocbench results in allocator sets")
    parser.add_argument("results", help="path to results", type=str)
    parser.add_argument("--license", help="print license info and exit", action='store_true')
    parser.add_argument("-b", "--benchmarks", help="benchmarks to summarize", nargs='+')
    parser.add_argument("-x", "--exclude-benchmarks", help="benchmarks to exclude", nargs='+')

    args = parser.parse_args()

    if not os.path.isdir(args.results):
        print_error(f"{args.results} is no directory")
        exit(1)

    if not os.path.isfile(os.path.join(args.results, "facts.save")):
        print_error(f"{args.results} is no valid allocbench result it misses facts.save")
        exit(1)

    src.globalvars.resdir = args.results
    os.chdir(args.results)

    # Load facts
    with open("facts.save", "rb") as f:
        src.globalvars.facts = pickle.load(f)

    for benchmark in src.globalvars.benchmarks:
        if args.benchmarks and not benchmark in args.benchmarks:
            continue
        if args.exclude_benchmarks and benchmark in args.exclude_benchmarks:
            continue

        bench_module = importlib.import_module(f"src.benchmarks.{benchmark}")

        if not hasattr(bench_module, benchmark):
            print_error(f"{benchmark} has no member {benchmark}")
            print_error(f"Skipping {benchmark}.")

        bench = getattr(bench_module, benchmark)

        try:
            bench.load()
        except FileNotFoundError:
            continue

        print_status(f"Summarizing {bench.name} ...")
        try:
            bench_sum(bench)
        except FileExistsError as e:
            print(e)


if __name__ == "__main__":
    main()
