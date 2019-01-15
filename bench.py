#!/usr/bin/env python3

import argparse
import importlib
import os

benchmarks = ["loop", "mysql", "falsesharing", "dj_trace", "larson"]

parser = argparse.ArgumentParser(description="benchmark memory allocators")
parser.add_argument("-s", "--save", help="save benchmark results to disk", action='store_true')
parser.add_argument("-l", "--load", help="load benchmark results from disk", action='store_true')
parser.add_argument("-r", "--runs", help="how often the benchmarks run", default=3, type=int)
parser.add_argument("-v", "--verbose", help="more output", action='store_true')
parser.add_argument("-b", "--benchmarks", help="benchmarks to run", nargs='+')
parser.add_argument("-ns", "--nosum", help="don't produce plots", action='store_true')
parser.add_argument("-sd", "--summarydir", help="directory where all plots and the summary go", type=str)
parser.add_argument("-a", "--analyse", help="collect allocation sizes", action='store_true')
parser.add_argument("--nolibmemusage", help="don't use libmemusage to analyse", action='store_true')
parser.add_argument("--license", help="print license info and exit", action='store_true')

def main():
    args = parser.parse_args()
    if args.license:
        print("Copyright (C) 2018-1029 Florian Fischer")
        print("License GPLv3: GNU GPL version 3 <http://gnu.org/licenses/gpl.html>")
        return
    if args.verbose:
        print(args)

    if args.summarydir and not os.path.isdir(args.summarydir):
        os.makedirs(args.summarydir)

    for bench in benchmarks:
        bench = eval("importlib.import_module('src.{0}').{0}".format(bench))
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
            analyse_args = {"nolibmemusage": args.nolibmemusage, "verbose": args.verbose}
            bench.analyse(**analyse_args)

        if not bench.run(runs=args.runs, verbose=args.verbose):
            continue

        if args.save:
            bench.save()

        if not args.nosum and not (args.runs < 1 and not args.load):
            print("Summarizing", bench.name, "...")
            bench.summary(args.summarydir or "")

        if (args.runs > 0 or args.analyse) and hasattr(bench, "cleanup"):
            print("Cleaning up", bench.name, "...")
            bench.cleanup()

if __name__ == "__main__":
    main()
