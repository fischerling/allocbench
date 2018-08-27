#!/usr/bin/env python3

import argparse
import os

import common_targets

from falsesharing import falsesharing
from loop import loop
# from bench_conprod import conprod
from mysql import mysql

parser = argparse.ArgumentParser(description="benchmark memory allocators")
parser.add_argument("-s", "--save", help="save benchmark results to disk", action='store_true')
parser.add_argument("-l", "--load", help="load benchmark results from disk", action='store_true')
parser.add_argument("-r", "--runs", help="how often the benchmarks run", default=3, type=int)
parser.add_argument("-v", "--verbose", help="more output", action='store_true')
parser.add_argument("-b", "--benchmarks", help="benchmarks to run", nargs='+')
parser.add_argument("-ns", "--nosum", help="don't produce plots", action='store_true')
parser.add_argument("-sd", "--summarydir", help="directory where all plots and the summary go", type=str)
parser.add_argument("-a", "--analyse", help="collect allocation sizes", action='store_true')


benchmarks = [loop, mysql, falsesharing]

def main():
    args = parser.parse_args()
    print (args)

    if args.summarydir and not os.path.isdir(args.summarydir):
        os.makedirs(args.summarydir)

    for bench in benchmarks:
        if args.benchmarks and not bench.name in args.benchmarks:
            continue
        if args.load:
            bench.load()

        if args.runs > 0 or args.analyse:
            print("Preparing", bench.name, "...")
            if not bench.prepare():
                print("Preparing", bench.name, "failed!")
                return

        if args.analyse and hasattr(bench, "analyse") and callable(bench.analyse):
            print("Analysing", bench.name, "...")
            bench.analyse(verbose=args.verbose)

        print("Running", bench.name, "...")
        if not bench.run(runs=args.runs, verbose=args.verbose):
            continue

        if args.save:
            bench.save()

        if not args.nosum:
            print("Summarizing", bench.name, "...")
            bench.summary(args.summarydir)

        if (args.runs > 0 or args.analyse) and hasattr(bench, "cleanup"):
            print("Cleaning up", bench.name, "...")
            bench.cleanup()

if __name__ == "__main__":
    main()
