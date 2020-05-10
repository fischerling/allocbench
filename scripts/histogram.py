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

"""Plot an interactive histogram from malt or chattymalloc output file"""

import argparse
import importlib
import inspect
import json
import os
import sys

import matplotlib.pyplot as plt

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


def main():
    parser = argparse.ArgumentParser(description="Plot histograms using a malt or chattymalloc output file")
    parser.add_argument("input_file", help="path to malt or chattymalloc output file", type=str)
    parser.add_argument("-e", "--export", help="export to csv", action="store_true")
    parser.add_argument("-n", "--no-ascii", help="don't output a ascii histogram", action="store_true")
    parser.add_argument("-i", "--interactive", help="open interactive matplotlib histogram plots",
                        action="store_true")
    args = parser.parse_args()

    fpath, fext = os.path.splitext(args.input_file)
    fname = os.path.basename(fpath)
    # chattymalloc
    if fname.startswith("chatty") and fext == ".txt":
        try:
            chattyparser = importlib.import_module("chattyparser")
        except ModuleNotFoundError:
            print("Can't import chattyparser")
            sys.exit(1)
        hist, calls, _ = chattyparser.parse(args.input_file, coll_size=False)
    # malt
    else:
        with open(args.input_file, "r") as json_file:
            malt_res = json.load(json_file)

        hist = malt_res["memStats"]["sizeMap"]
        calls = {}
        for thread in malt_res["threads"]:
            for func, data in thread["stats"].items():
                calls[func] = calls.get(func, 0) + data["count"]

    if args.export:
        with open(f"{fpath}.csv", "w") as csv_file:
            print("Size", "Amount", file=csv_file)
            for size, amount in hist.items():
                print(size, amount, file=csv_file)

    if not args.no_ascii:
        chattyparser.plot_hist_ascii(f"{fpath}.hist.txt", hist, calls)

    if args.interactive:
        sizes = []
        sizes_smaller_4K = []
        sizes_smaller_32K = []
        sizes_bigger_32K = []
        for size, amount in hist.items():
            size = int(size)
            sizes.append(size * amount)
            if size < 4096:
                sizes_smaller_4K.append(size * amount)
            if size < 32000:
                sizes_smaller_32K.append(size * amount)
            else:
                sizes_bigger_32K.append(size * amount)


        plt.figure(0)
        plt.hist(sizes_smaller_4K, 200)
        plt.title("Sizes smaller than 4K")

        plt.figure(1)
        plt.hist(sizes_smaller_32K, 200)
        plt.title("Sizes smaller than 32K")

        plt.figure(2)
        plt.hist(sizes_bigger_32K, 200)
        plt.title("Sizes bigger than 32K")

        plt.figure(3)
        plt.hist(sizes, 200)
        plt.title("All sizes")
        plt.show()

if __name__ == "__main__":
    main()
