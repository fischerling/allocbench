#!/usr/bin/env python3

import argparse
import inspect
import json
import matplotlib.pyplot as plt
import os
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import src.chattyparser as cp


parser = argparse.ArgumentParser(description="Plot histograms using a chattymalloc output file")
parser.add_argument("chattymalloc_file", help="path to chattymalloc.txt output file", type=str)
parser.add_argument("-e", "--export", help="export to csv", action="store_true")

def main():
    args = parser.parse_args()

    hist, calls, total_sizes = cp.parse(args.chattymalloc_file)

    if args.export:
        with open(args.chattymalloc_file.replace("json", "csv"), "w") as f:
            print("Size", "Amount", file=f)
            for size, amount in hist.items():
                print(size, amount, file=f)
    
    else:
        sizes = []
        sizes_smaller_4K = []
        sizes_smaller_32K = []
        sizes_bigger_32K = []
        for size, amount in hist.items():
            size = int(size)
            sizes += [int(size)] * amount
            if size < 4096:
                sizes_smaller_4K += [int(size)] * amount
            if size < 32000:
                sizes_smaller_32K += [int(size)] * amount
            else:
                sizes_bigger_32K += [int(size)] * amount


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
