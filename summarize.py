#!/usr/bin/env python3

import argparse
import importlib
import os
import pickle

import src.globalvars
from src.util import print_status, print_debug, print_error


def specific_summary(bench, allocators):
    """Summarize bench in PWD for allocators"""
    old_allocs = bench.results["allocators"]
    new_allocs = {k: v for k, v in old_allocs.items() if k in allocators}

    bench.results["allocators"] = new_allocs

    # set colors
    explicit_colors = [v["color"] for k, v in allocators.items()
                       if v["color"] is not None]
    print_debug("Explicit colors:", explicit_colors)

    cycle_list = ["C" + str(i) for i in range(0, 16)]
    avail_colors = [color for color in cycle_list
                    if color not in explicit_colors]
    print_debug("available colors:", avail_colors)

    for _, value in allocators.items():
        if value["color"] is None:
            value["color"] = avail_colors.pop()

    src.globalvars.allocators = allocators

    bench.summary()
    bench.results["allocators"] = old_allocs


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
        os.mkdir(set_name)
        os.chdir(set_name)
        specific_summary(bench, sets[set_name])
        os.chdir("..")

    os.chdir("..")


def main():
    parser = argparse.ArgumentParser(description="Summarize allocbench results in allocator sets")
    parser.add_argument("results", help="path to results", type=str)
    parser.add_argument("-b", "--benchmarks", help="benchmarks to summarize", nargs='+')
    parser.add_argument("-x", "--exclude-benchmarks", help="benchmarks to exclude", nargs='+')

    args = parser.parse_args()
    os.chdir(args.results)

    # Load facts
    with open("facts.save", "rb") as f:
        src.globalvars.facts = pickle.load(f)

    for benchmark in src.globalvars.benchmarks:
        if args.benchmarks and not benchmark in args.benchmarks:
            continue
        if args.exclude_benchmarks and benchmark in args.exclude_benchmarks:
            continue

        try:
            bench = importlib.import_module(f"src.benchmarks.{benchmark}")
        except ModuleNotFoundError:
            print_error(f"Could not import {benchmark}")
            print_error(f"Skipping {benchmark}.")

        if not hasattr(bench, benchmark):
            print_error(f"{benchmark} has no member {benchmark}")
            print_error(f"Skipping {benchmark}.")

        bench = getattr(bench, benchmark)

        try:
            bench.load()
        except FileNotFoundError:
            print_error(f"Could not load {benchmark}")
            print_error(f"Skipping {benchmark}.")
            continue

        print_status(f"Summarizing {bench.name} ...")
        try:
            bench_sum(bench)
        except FileExistsError as e:
            print(e)


if __name__ == "__main__":
    main()
