#!/usr/bin/env python3

"""Parser and Plotter for the traces produced by chattymalloc"""

import re
import sys

import matplotlib.pyplot as plt
import numpy as np

PTR = "(?:0x)?(?P<ptr>(?:\\w+)|(?:\\(nil\\)))"
SIZE = "(?P<size>\\d+)"
ALIGNMENT = "(?P<alignment>\\d+)"

MALLOC_RE = re.compile(f"^m {SIZE} {PTR}$")
FREE_RE = re.compile(f"^f {PTR}$")
CALLOC_RE = re.compile(f"^c (?P<nmemb>\\d+) {SIZE} {PTR}$")
REALLOC_RE = re.compile(f"^r {PTR} {SIZE} {PTR.replace('ptr', 'nptr')}$")
MEMALIGN_RE = re.compile(f"^ma {ALIGNMENT} {SIZE} {PTR}$")
POSIX_MEMALIGN_RE = re.compile(f"^p_ma {PTR} {ALIGNMENT} {SIZE} (?P<ret>\\d+)$")
VALLOC_RE = re.compile(f"^v {SIZE} {PTR}$")
PVALLOC_RE = re.compile(f"^pv {SIZE} {PTR}$")
ALIGNED_ALLOC_RE = re.compile(f"^a_m {ALIGNMENT} {SIZE} {PTR}$")

TRACE_REGEX = {"malloc": MALLOC_RE, "free": FREE_RE, "calloc": CALLOC_RE,
               "realloc": REALLOC_RE, "memalign": MEMALIGN_RE,
               "posix_memalign": POSIX_MEMALIGN_RE, "valloc": VALLOC_RE,
               "pvalloc": PVALLOC_RE, "aligned_alloc": ALIGNED_ALLOC_RE}


def record_allocation(hist, total_size, allocations, ptr, size, coll_size,
                      req_size, nohist, optr=None, free=False):
    """add allocation to histogram or total requested memory

       hist - dict mapping allocation sizes to their occurrence
       total_size - list of total requested memory till last recorded function call
       allocations - dict of life allocations mapping their pointer to their size
       ptr - pointer returned from function to record
       size - size passed to function to record
       coll_size - should the total memory be tracked
       req_size - track only allocations of requested size
       nohist - don't create a histogram
       optr - pointer passed to funtion to record
       free - is recorded function free(ptr)"""

    if not free:
        size = int(size)

        # realloc returns new pointer
        if optr and optr in allocations:
            size -= allocations[optr]
            del allocations[optr]

        allocations[ptr] = size
        if not nohist:
            hist[size] = hist.get(size, 0) + 1

        if not isinstance(total_size[-1], int) or not isinstance(size, int):
            print("invalid type", type(total_size[-1]), type(size))
            return

        if coll_size:
            if not req_size or size == req_size:
                total_size.append(total_size[-1] + size)
            elif req_size:
                total_size.append(total_size[-1])

    # free of a valid pointer
    elif ptr != "(nil)" and ptr in allocations:
        size = allocations[ptr]
        if coll_size:
            if not req_size or size == req_size:
                total_size.append(total_size[-1] - size)
            elif req_size:
                total_size.append(total_size[-1])

        del allocations[ptr]
    # free of invalid pointer
    elif coll_size:
        total_size.append(total_size[-1])


def parse(path="chattymalloc.txt", coll_size=True, req_size=None, nohist=False):
    """parse a chattymalloc trace

    :returns: a histogram dict, a dict of occurred function calls, list of total requested memory
    """
    # count function calls
    calls = {"malloc": 0, "free": 0, "calloc": 0, "realloc": 0, "memalign": 0,
             "posix_memalign": 0, "valloc": 0, "pvalloc": 0, "aligned_alloc": 0}
    # Dictionary to track all live allocations
    allocations = {}
    # List of total live memory per operation
    requested_size = [0]
    # Dictionary mapping allocation sizes to the count of their appearance
    hist = {}
    line_count = 0

    def record(ptr, size, optr=None, free=False):
        """Wrapper around record_allocation using local variables from parse"""
        record_allocation(hist, requested_size, allocations, ptr, size,
                          coll_size, req_size, nohist, optr, free)

    with open(path, "r") as trace_file:
        for line in trace_file.readlines():
            line_count += 1
            valid_line = False
            for func, func_regex in TRACE_REGEX.items():
                res = func_regex.match(line)
                if res is not None:
                    calls[func] += 1
                    res = res.groupdict()

                    if func == "free":
                        record(res["ptr"], 0, free=True)
                    elif func == "calloc":
                        record(res["ptr"], int(res["nmemb"]) * int(res["size"]))
                    elif func == "realloc":
                        record(res["nptr"], res["size"], optr=res["ptr"])
                    else:
                        record(res["ptr"], res["size"])

                    valid_line = True
                    break

            if not valid_line:
                print("\ninvalid line at", line_count, ":", line)

    return hist, calls, np.array(requested_size)


def plot(path):
    hist, calls, total_sizes = parse(path=path, req_size=None)

    plot_hist_ascii(f"{path}.hist", hist, calls)

    top5 = [t[1] for t in sorted([(n, s) for s, n in hist.items()])[-5:]]
    del hist
    del calls

    plot_profile(total_sizes, path, path + ".profile.png", top5)


def plot_profile(total_sizes, trace_path, plot_path, sizes):
    x_vals = range(0, len(total_sizes))

    plt.plot(x_vals, total_sizes / 1000, marker='',
             linestyle='-', label="Total requested")

    for size in sizes:
        _, _, total_size = parse(path=trace_path, nohist=True, req_size=size)
        plt.plot(x_vals, total_size / 1000, label=size)

    plt.legend(loc="lower center")
    plt.xlabel("Allocations")
    plt.ylabel("mem in kb")
    plt.title("Memusage profile")
    plt.savefig(plot_path)
    plt.clf()

def plot_hist_ascii(path, hist, calls):
    bins = {}
    for size in sorted(hist):
        bin = int(size / 16)
        bins[bin] = bins.get(bin, 0) + hist[size]


    total = sum(calls.values()) - calls["free"]
    with open(path, "w") as hist_file:
        print("Total function calls:", total, file=hist_file)
        for func in TRACE_REGEX:
            print(func, calls[func], file=hist_file)

        print(file=hist_file)

        print("allocations <= 64", sum([n for s, n in hist.items() if s <= 64]), file=hist_file)
        print("allocations <= 1024", sum([n for s, n in hist.items() if s <= 1024]), file=hist_file)
        print("allocations <= 4096", sum([n for s, n in hist.items() if s <= 4096]), file=hist_file)
        print(file=hist_file)

        print("Histogram of sizes:", file=hist_file)
        sbins = sorted(bins)
        binmaxlength = str(len(str(sbins[-1])) + 1)
        amountmaxlength = str(len(str(sorted(bins.values())[-1])))
        for current_bin in sbins:
            perc = bins[current_bin]/total*100
            binsize = "{:<" + binmaxlength + "} - {:>" + binmaxlength + "}"
            print(binsize.format((current_bin)*16, (current_bin+1)*16-1), end=" ", file=hist_file)
            amount = "{:<" + amountmaxlength + "} {:.2f}% {}"
            print(amount.format(bins[current_bin], perc, '*'*int(perc/2)), file=hist_file)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("chattyparser: parse chattymalloc output and",
              "create size histogram and memory profile", file=sys.stderr)
        print(f"Usage: {sys.argv[0]} chattymalloc-file", file=sys.stderr)
        exit(1)

    plot(sys.argv[1])
