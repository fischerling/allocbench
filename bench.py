#!/usr/bin/env python3

import argparse

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


benchmarks = [loop, mysql, falsesharing]

def main():
    args = parser.parse_args()
    print (args)

    for bench in benchmarks:
        if args.benchmarks and not bench.name in args.benchmarks:
            continue
        if args.load:
            bench.load()

        print("Preparing", bench.name)
        if not bench.prepare():
            continue

        print("Running", bench.name)
        if not bench.run(runs=args.runs):
            continue

        if args.save:
            bench.save()

        print("Summarizing", bench.name)
        bench.summary()

        if hasattr(bench, "cleanup"):
            print("Cleaning after", bench.name)
            bench.cleanup()

if __name__ == "__main__":
    main()
