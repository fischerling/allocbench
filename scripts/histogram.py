#!/usr/bin/env python3

import argparse
import json
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(description="Plot interactive histogram using a malt json output file")
parser.add_argument("malt_output_file", help="path to malt output file", type=str)
parser.add_argument("-e", "--export", help="export to csv", action="store_true")

def main():
    args = parser.parse_args()

    with open(args.malt_output_file, "r") as f:
        res = json.load(f)

    if args.export:
        with open(args.malt_output_file.replace("json", "csv"), "w") as f:
            print("Size", "Amount", file=f)
            for size, amount in res["memStats"]["sizeMap"].items():
                print(size, amount, file=f)
    
    else:
        sizes = []
        sizes_smaller_4K = []
        sizes_smaller_32K = []
        sizes_bigger_32K = []
        for size, amount in res["memStats"]["sizeMap"].items():
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
