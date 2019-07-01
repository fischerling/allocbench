#!/usr/bin/env python3

import argparse
import importlib
import inspect
import os
import sys
import _thread
import threading

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from src.globalvars import benchmarks

def specific_summary(bench, set_name, allocators):
    os.mkdir(set_name)
    os.chdir(set_name)

    if bench.name == "loop":
        allocators["bumpptr"] = {"color": "C9"}

    old_allocs = bench.results["allocators"]
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
parser.add_argument("-t", "--threads", help="Summarize using multiple threads", action="store_true")

def main():
    args = parser.parse_args()
    os.chdir(args.results)

    active_threads = []

    for b in benchmarks:
        if args.benchmarks and not b in args.benchmarks:
            continue
        if args.exclude_benchmarks and b in args.exclude_benchmarks:
            continue

        bench = eval("importlib.import_module('src.benchmarks.{0}').{0}".format(b))
        try:
            bench.load()
        except FileNotFoundError as e:
            print("No data available")
            continue
        
        if args.threads:
            active_threads.append(_thread.start_new_thread(bench_sum, (bench, sets)))

            for thread in threading.enumerate():
                if thread is not threading.main_thread():
                    thread.join()
        else:
            try:
                bench_sum(bench, sets)
            except FileExistsError as e:
                print(e)


if __name__ == "__main__":
    main()
