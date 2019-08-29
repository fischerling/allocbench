#!/usr/bin/env python3

"""Plot an interactive histogram from malt or chattymalloc output file"""

import argparse
import importlib
import inspect
import json
import os
import sys

import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description="Plot histograms using a malt or chattymalloc output file")
    parser.add_argument("input_file", help="path to malt or chattymalloc output file", type=str)
    parser.add_argument("-e", "--export", help="export to csv", action="store_true")
    args = parser.parse_args()

    fname, fext = os.path.splitext(args.input_file)
    fname = os.path.basename(fname)
    # chattymalloc
    if fname.startswith("chatty") and fext == ".txt":
        # import chattyparser
        currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        sys.path.insert(0, parentdir)

        chattyparser = importlib.import_module("src.chattyparser")

        hist, _, _ = chattyparser.parse(args.input_file, coll_size=False)
    # malt
    else:
        with open(args.input_file, "r") as json_file:
            hist = json.load(json_file)["memStats"]["sizeMap"]

    if args.export:
        with open(f"{fname}.csv", "w") as csv_file:
            print("Size", "Amount", file=csv_file)
            for size, amount in hist.items():
                print(size, amount, file=csv_file)

    else:
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
