#!/usr/bin/env python3

import argparse
import os
import pickle


def main():
    parser = argparse.ArgumentParser(description="Merge to allocbench results")
    parser.add_argument("src", help="results which should be merged into dest", type=str)
    parser.add_argument("dest", help="results in which src should be merged", type=str)
    parser.add_argument("-b", "--benchmarks", help="benchmarks to summarize", nargs='+')
    parser.add_argument("-x", "--exclude-benchmarks", help="benchmarks to exclude", nargs='+')

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

        with open(src_save, "rb") as src_file:
            src_results = pickle.load(src_file)

        with open(dest_save, "rb") as dest_file:
            dest_results = pickle.load(dest_file)

        for alloc in src_results["allocators"]:
            if alloc in dest_results["allocators"]:
                print(alloc, "already in", dest_save)
                continue

            print("merging", alloc, "from", src_save, "into", dest_save)
            dest_results["allocators"][alloc] = src_results["allocators"][alloc]
            dest_results[alloc] = src_results[alloc]
            dest_results["stats"][alloc] = src_results["stats"][alloc]

        with open(dest_save, "wb") as result_file:
            pickle.dump(dest_results, result_file)


if __name__ == "__main__":
    main()
