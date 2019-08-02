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

def specific_summary(bench, set_name, allocators):
    os.mkdir(set_name)
    os.chdir(set_name)

    if bench.name == "loop":
        allocators["bumpptr"] = {"color": "C9"}

    old_allocs = bench.results["allocators"]

    if bench.name == "mysql" and "Hoard" in allocators:
        del(allocators["Hoard"])
    bench.results["allocators"] = allocators
    bench.summary()
    bench.results["allocators"] = old_allocs

    if bench.name == "loop":
        del(allocators["bumpptr"])


    os.chdir("..")

def bench_sum(bench, sets):
    os.makedirs(bench.name)
    os.chdir(bench.name)
    os.mkdir("all")
    os.chdir("all")
    bench.summary()
    os.chdir("..")
    for s in sets:
        specific_summary(bench, s, sets[s])
    os.chdir("..")

sets = {"glibcs": ["glibc", "glibc-noThreadCache", "glibc-noFalsesharing",
                   "glibc-noFalsesharingClever"],
        "tcmalloc": ["TCMalloc", "TCMalloc-NoFalsesharing"],
        "nofs": ["glibc", "glibc-noFalsesharing", "glibc-noFalsesharingClever",
                 "TCMalloc", "TCMalloc-NoFalsesharing"],
        "ba" : ["glibc", "TCMalloc", "jemalloc", "Hoard"],
        "industry" : ["glibc", "llalloc", "TCMalloc", "jemalloc", "tbbmalloc", "mimalloc"],
        "science" : ["scalloc", "SuperMalloc", "Mesh", "Hoard"]}

# colorize allocs
new_sets = {}
for s in sets:
    new_allocs = {}
    for i, a in enumerate(sets[s]):
        new_allocs[a] = {"color": "C"+str(i)}
    new_sets[s] = new_allocs

sets = new_sets

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

    print(src.globalvars.facts)
    for b in src.globalvars.benchmarks:
        if args.benchmarks and not b in args.benchmarks:
            continue
        if args.exclude_benchmarks and b in args.exclude_benchmarks:
            continue

        bench = eval("importlib.import_module('src.benchmarks.{0}').{0}".format(b))
        try:
            bench.load()
        except FileNotFoundError as e:
            print(bench.name, "No data available")
            continue
        
        try:
            bench_sum(bench, sets)
        except FileExistsError as e:
            print(e)


if __name__ == "__main__":
    main()
