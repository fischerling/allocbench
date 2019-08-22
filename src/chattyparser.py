#!/usr/bin/env python3

import re
import matplotlib.pyplot as plt
import numpy as np
import sys

ptr = "(?:0x)?(?P<ptr>(?:\w+)|(?:\(nil\)))"
size = "(?P<size>\d+)"
alignment = "(?P<alignment>\d+)"

malloc_re = re.compile(f"^m {size} {ptr}$")
free_re = re.compile(f"^f {ptr}$")
calloc_re = re.compile(f"^c (?P<nmemb>\d+) {size} {ptr}$")
realloc_re = re.compile(f"^r {ptr} {size} {ptr.replace('ptr', 'nptr')}$")
memalign_re = re.compile(f"^ma {alignment} {size} {ptr}$")
posix_memalign_re = re.compile(f"^p_ma {ptr} {alignment} {size} (?P<ret>\d+)$")
valloc_re = re.compile(f"^v {size} {ptr}$")
pvalloc_re = re.compile(f"^pv {size} {ptr}$")
aligned_alloc_re = re.compile(f"^a_m {alignment} {size} {ptr}$")

trace_regex = {"malloc": malloc_re, "free": free_re, "calloc": calloc_re,
               "realloc": realloc_re, "memalign": memalign_re,
               "posix_memalign": posix_memalign_re, "valloc": valloc_re,
               "pvalloc": pvalloc_re, "aligned_alloc": aligned_alloc_re}


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
            del(allocations[optr])

        allocations[ptr] = size
        if not nohist:
            hist[size] = hist.get(size, 0) + 1

        if type(total_size[-1]) != int or type(size) != int:
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

        del(allocations[ptr])
    # free of invalid pointer
    elif coll_size:
        total_size.append(total_size[-1])


def parse(path="chattymalloc.txt", coll_size=True, req_size=None, nohist=False):
    # count function calls
    calls = {"malloc": 0, "free": 0, "calloc": 0, "realloc": 0, "memalign": 0,
             "posix_memalign": 0, "valloc": 0, "pvalloc": 0, "aligned_alloc": 0}
    # Dictionary to track all live allocations
    allocations = {}
    # List of total live memory per operation
    requested_size = [0]
    # Dictionary mapping allocation sizes to the count of their appearance
    hist = {}
    ln = 0

    def record(ptr, size, optr=None, free=False):
        """Wrapper around record_allocation using local variables from parse"""
        record_allocation(hist, requested_size, allocations, ptr, size,
                          coll_size, req_size, nohist, optr, free)

    with open(path, "r") as f:
        for i, l in enumerate(f.readlines()):
            ln += 1
            valid_line = False
            for func, func_regex in trace_regex.items():
                res = func_regex.match(l)
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
                print("\ninvalid line at", ln, ":", l)

    return hist, calls, np.array(requested_size)


def plot(path):
    hist, calls, total_sizes = parse(path=path, req_size=None)

    plot_hist_ascii(path+".hist", hist, calls)

    top5 = [t[1] for t in sorted([(n, s) for s, n in hist.items()])[-5:]]
    del hist
    del calls

    plot_profile(total_sizes, path, path + ".profile.png", top5)


def plot_profile(total_sizes, trace_path, plot_path, sizes):
    x_vals = range(0, len(total_sizes))

    plt.plot(x_vals, total_sizes / 1000, marker='',
             linestyle='-', label="Total requested")

    for s in sizes:
        _, _, total_size = parse(path=trace_path, nohist=True, req_size=s)
        plt.plot(x_vals, total_size / 1000, label=s)

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
    with open(path, "w") as f:
        print("Total function calls:", total, file=f)
        for func in trace_regex:
            print(func, calls[func], file=f)

        print(file=f)

        print("allocations <= 64", sum([n for s, n in hist.items() if s <= 64]), file=f)
        print("allocations <= 1024", sum([n for s, n in hist.items() if s <= 1024]), file=f)
        print("allocations <= 4096", sum([n for s, n in hist.items() if s <= 4096]), file=f)
        print(file=f)

        print("Histogram of sizes:", file=f)
        sbins = sorted(bins)
        binmaxlength = str(len(str(sbins[-1])) + 1)
        amountmaxlength = str(len(str(sorted(bins.values())[-1])))
        for b in sbins:
            perc = bins[b]/total*100
            binsize = "{:<" + binmaxlength + "} - {:>" + binmaxlength + "}"
            print(binsize.format((b)*16, (b+1)*16-1), end=" ", file=f)
            amount = "{:<" + amountmaxlength + "} {:.2f}% {}"
            print(amount.format(bins[b], perc, '*'*int(perc/2)), file=f)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("chattyparser: parse chattymalloc output and create size histogram and memory profile", file=sys.stderr)
        print(f"Usage: {sys.argv[0]} chattymalloc-file", file=sys.stderr)
        exit(1)

    plot(sys.argv[1])
