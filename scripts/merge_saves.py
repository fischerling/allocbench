#!/usr/bin/env python3

import argparse
import inspect
import os
import pickle
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

parser = argparse.ArgumentParser(description="Summarize allocbench results in allocator sets")
parser.add_argument("src", help="path to results which should be merged into dest", type=str)
parser.add_argument("dest", help="path to results in which src should be merged", type=str)
parser.add_argument("-b", "--benchmarks", help="benchmarks to summarize", nargs='+')
parser.add_argument("-x", "--exclude-benchmarks", help="benchmarks to exclude", nargs='+')


def main():
    args = parser.parse_args()

    for src_save in os.listdir(args.src):
        if not src_save.endswith(".save"):
            continue
        if src_save == "facts.save":
            continue
        if args.benchmarks and not src_save[:-5] in args.benchmarks:
            continue
        if args.exclude_benchmarks and src_save[:-5] in args.exclude_benchmarks:
            continue

        src_save = os.path.join(args.src, src_save)
        dest_save = os.path.join(args.dest, os.path.basename(src_save))

        if not os.path.isfile(dest_save):
            print("Can't merge", src_save, "because", os.path.basename(src_save), "not in", args.dest)
            continue

        with open(src_save, "rb") as f:
            src_results = pickle.load(f)

        with open(dest_save, "rb") as f:
            dest_results = pickle.load(f)

        for alloc in src_results["allocators"]:
            if alloc in dest_results["allocators"]:
                print(alloc, "already in", dest_save)
                continue

            print("merging", alloc, "from", src_save, "into", dest_save)
            dest_results["allocators"][alloc] = src_results["allocators"][alloc]
            dest_results[alloc] = src_results[alloc]
            dest_results["stats"][alloc] = src_results["stats"][alloc]

        with open(dest_save, "wb") as f:
            pickle.dump(dest_results, f)


if __name__ == "__main__":
    main()
