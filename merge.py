#!/usr/bin/env python3

# Copyright 2018-2020 Florian Fischer <florian.fl.fischer@fau.de>
#
# This file is part of allocbench.
#
# allocbench is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# allocbench is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with allocbench.  If not, see <http://www.gnu.org/licenses/>.

"""Merge two compatible results of an allocbench run"""

import argparse
import json
import os
import pickle
import sys

import allocbench.facter as facter
from allocbench.util import print_license_and_exit

def load_file(filename):
    if filename.endswith("json"):
        with open(filename, "r") as json_file:
            return json.load(json_file)
    else:
        with open(filename, "rb") as pickle_file:
            return pickle.load(pickle_file)


def main():
    if "--license" in sys.argv:
        print_license_and_exit()

    parser = argparse.ArgumentParser(description="Merge to allocbench results")
    parser.add_argument("src", help="results which should be merged into dest", type=str)
    parser.add_argument("dest", help="results in which src should be merged", type=str)
    parser.add_argument("--license", help="print license info and exit", action='store_true')
    parser.add_argument("--version", help="print version info and exit", action='version',
                        version=f"allocbench {facter.allocbench_version()}")
    parser.add_argument("-b", "--benchmarks", help="benchmarks to summarize", nargs='+')
    parser.add_argument("-x", "--exclude-benchmarks", help="benchmarks to exclude", nargs='+')

    args = parser.parse_args()

    for src_save in os.listdir(args.src):
        if not os.path.splitext(src_save)[1] in [".json", ".save"]:
            continue
        if src_save in ["facts.save", "facts.json"]:
            continue
        if args.benchmarks and not src_save[:-5] in args.benchmarks:
            continue
        if args.exclude_benchmarks and src_save[:-5] in args.exclude_benchmarks:
            continue

        src_save = os.path.join(args.src, src_save)
        dest_save = os.path.join(args.dest, os.path.basename(src_save))

        if not os.path.isfile(dest_save):
            print(f"Can't merge {src_save} because {os.path.basename(src_save)} not in {args.dest}")
            continue

        src_results = load_file(src_save)

        dest_results = load_file(dest_save)

        for alloc in src_results["allocators"]:
            if alloc in dest_results["allocators"]:
                print(alloc, "already in", dest_save)
                continue

            print("merging", alloc, "from", src_save, "into", dest_save)
            dest_results["allocators"][alloc] = src_results["allocators"][alloc]
            dest_results[alloc] = src_results[alloc]
            dest_results["stats"][alloc] = src_results["stats"][alloc]

        with open(os.path.splitext(dest_save)[0] + ".json", "w") as result_file:
            json.dump(dest_results, result_file)


if __name__ == "__main__":
    main()
