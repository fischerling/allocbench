#!/usr/bin/env python3

import argparse
import importlib
import inspect
import os
import pickle
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import src.globalvars

sets = {"glibcs": ["glibc", "glibc-noThreadCache", "glibc-noFalsesharing",
                   "glibc-noFalsesharingClever"],
        "tcmalloc": ["TCMalloc", "TCMalloc-NoFalsesharing"],
        "nofs": ["glibc", "glibc-noFalsesharing", "glibc-noFalsesharingClever",
                 "TCMalloc", "TCMalloc-NoFalsesharing"],
        "ba" : ["glibc", "TCMalloc", "jemalloc", "Hoard"],
        "industry" : ["glibc", "llalloc", "TCMalloc", "jemalloc", "tbbmalloc", "mimalloc"],
        "research" : ["scalloc", "SuperMalloc", "Mesh", "Hoard", "snmalloc"]}


def specific_summary(bench, allocators):
    old_allocs = bench.results["allocators"]
    new_allocs = {k: v for k, v in old_allocs.items() if k in allocators}

    bench.results["allocators"] = new_allocs
    bench.summary()
    bench.results["allocators"] = old_allocs


def bench_sum(bench, sets):
    os.makedirs(bench.name)
    os.chdir(bench.name)

    os.mkdir("all")
    os.chdir("all")
    bench.summary()
    os.chdir("..")

    for s in sets:
        os.mkdir(s)
        os.chdir(s)
        specific_summary(bench, sets[s])
        os.chdir("..")

    os.chdir("..")


parser = argparse.ArgumentParser(description="Summarize allocbench results in allocator sets")
parser.add_argument("results", help="path to results", type=str)
parser.add_argument("-b", "--benchmarks", help="benchmarks to summarize", nargs='+')
parser.add_argument("-x", "--exclude-benchmarks", help="benchmarks to exclude", nargs='+')

def main():
    args = parser.parse_args()
    os.chdir(args.results)

    # Load facts
    with open("facts.save", "rb") as f:
        src.globalvars.facts = pickle.load(f)

    for b in src.globalvars.benchmarks:
        if args.benchmarks and not b in args.benchmarks:
            continue
        if args.exclude_benchmarks and b in args.exclude_benchmarks:
            continue

        bench = eval("importlib.import_module('src.benchmarks.{0}').{0}".format(b))
        try:
            print(f"{bench.name} ...", end="", flush=True)
            bench.load()
        except FileNotFoundError as e:
            print(" No data available")
            continue

        try:
            bench_sum(bench, sets)
        except FileExistsError as e:
            print(e, end="")

        print()


if __name__ == "__main__":
    main()
