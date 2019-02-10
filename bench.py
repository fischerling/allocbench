#!/usr/bin/env python3

import argparse
import datetime
import importlib
import os
import subprocess

import src.facter
import src.allocators

benchmarks = ["loop", "mysql", "falsesharing", "dj_trace", "larson"]

parser = argparse.ArgumentParser(description="benchmark memory allocators")
parser.add_argument("-s", "--save", help="save benchmark results in RESULTDIR", action='store_true')
parser.add_argument("-l", "--load", help="load benchmark results from directory", type=str)
parser.add_argument("-a", "--allocators", help="load allocator definitions from file", type=str)
parser.add_argument("-r", "--runs", help="how often the benchmarks run", default=3, type=int)
parser.add_argument("-v", "--verbose", help="more output", action='store_true')
parser.add_argument("-b", "--benchmarks", help="benchmarks to run", nargs='+')
parser.add_argument("-ns", "--nosum", help="don't produce plots", action='store_true')
parser.add_argument("-rd", "--resultdir", help="directory where all results go", type=str)
parser.add_argument("--license", help="print license info and exit", action='store_true')


def main():
    args = parser.parse_args()
    if args.license:
        print("Copyright (C) 2018-2019 Florian Fischer")
        print("License GPLv3: GNU GPL version 3 <http://gnu.org/licenses/gpl.html>")
        return

    if args.verbose:
        print(args)

    # Prepare allocbench
    print("Building allocbench")
    make_cmd = ["make"]
    if not args.verbose:
        make_cmd.append("-s")

    subprocess.run(make_cmd)

    allocators_file = os.path.join("build", "allocators", "allocators.py")

    if args.allocators or os.path.isfile(allocators_file):
        allocators_files = args.allocators or allocators_file

        with open(allocators_files, "r") as f:
            g = {"verbose": args.verbose}
            exec(f.read(), g)
        src.allocators.allocators = g["allocators"]

    if args.verbose:
        print("Allocators:", *src.allocators.allocators.keys())

    if args.save or not args.nosum and not (args.runs < 1 and not args.load):
        if args.resultdir:
            resdir = os.path.join(args.resultdir)
        else:
            resdir = os.path.join("results", src.facter.get_hostname(),
                                    datetime.datetime.now().strftime("%Y-%m-%dT%H:%M"))
        try:
            os.makedirs(resdir)
        except FileExistsError:
            pass

    for bench in benchmarks:
        bench = eval("importlib.import_module('src.{0}').{0}".format(bench))
        if args.benchmarks and not bench.name in args.benchmarks:
            continue
        if args.load:
            bench.load(path=args.load)

        if args.runs > 0:
            print("Preparing", bench.name, "...")
            if not bench.prepare():
                print("Preparing", bench.name, "failed!")
                return

        if not bench.run(runs=args.runs, verbose=args.verbose):
            continue

        if args.save or not args.nosum and not (args.runs < 1 and not args.load):
            old_cwd = os.getcwd()
            os.chdir(resdir)

            if args.save:
                bench.save()

            if not args.nosum and not (args.runs < 1 and not args.load):
                try:
                    os.mkdir(bench.name)
                except FileExistsError:
                    pass
                os.chdir(bench.name)
                print("Summarizing", bench.name, "...")
                bench.summary()

            os.chdir(old_cwd)

        if args.runs > 0 and hasattr(bench, "cleanup"):
            print("Cleaning up", bench.name, "...")
            bench.cleanup()

if __name__ == "__main__":
    main()
