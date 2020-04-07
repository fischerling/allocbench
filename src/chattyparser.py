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
"""Parser and Plotter for the traces produced by chattymalloc"""

import argparse
from enum import Enum
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

CHECK_ALIGNMENT = None
EXPORT_TXT = False


class Function(Enum):
    """Enum holding all trace events of chattymalloc"""
    malloc = 0
    free = 1
    realloc = 2
    calloc = 3
    memalign = 4
    posix_memalign = 5
    valloc = 6
    pvalloc = 7
    aligned_alloc = 8


class Trace:
    """Class representing the chattymalloc trace_t struct"""

    size = 29

    def __init__(self, line):
        self.tid = int.from_bytes(line[0:4], "little")
        self.ptr = int.from_bytes(line[4:12], "little")
        self.size = int.from_bytes(line[12:20], "little")
        self.var_arg = int.from_bytes(line[20:28], "little")
        self.func = Function(line[28])


def update_cache_lines(cache_lines, trace, size):
    """mark or unmark all cache lines spanned by this allocation"""
    if cache_lines is None:
        return ""

    start = trace.ptr
    end = start + abs(size)
    msg = ""

    cache_line = start & ~(64 - 1)
    assert cache_line % 64 == 0
    while cache_line < end:
        if trace.func != Function.free:
            if cache_line not in cache_lines or cache_lines[cache_line] == []:
                cache_lines[cache_line] = [trace.tid]
            # false sharing
            else:
                if trace.tid not in cache_lines[cache_line]:
                    msg += (f"WARNING: cache line {hex(cache_line)} is shared "
                            f"between {set(cache_lines[cache_line] + [trace.tid])}\n")
                cache_lines[cache_line].append(trace.tid)
        else:
            if trace.tid in cache_lines[cache_line]:
                cache_lines[cache_line].remove(trace.tid)
            else:
                #If cache line is only owned by one thread it should be save to remove it
                if len(cache_lines[cache_line]) == 1:
                    del cache_lines[cache_line]
                elif len(cache_lines[cache_line]) == 0:
                    msg += f"INTERNAL ERROR: freeing not owned cache line\n"
                #TODO fix passed allocations
                else:
                    pass

        # print(hex(cache_line), cache_lines[cache_line], end=" ")
        cache_line += 64

    # print()
    return msg


def record_allocation(trace, context):
    """add allocation to histogram or total requested memory

       trace - Trace object ro record
       context - dict holding all data structures used for parsing
           allocations - dict of life allocations mapping their pointer to their size
           hist - dict mapping allocation sizes to their occurrence
           realloc_hist - dict mapping the two realloc sizes to their occurence
           total_size - list of total requested memory till last recorded function call
           cache_lines - dict of cache lines mapped to the owning tids
           req_size - dict mapping sizes to their individual total requested memory
    """

    # mandatory
    allocations = context.setdefault("allocations", [])

    # optional
    hist = context.get("hist", None)
    realloc_hist = context.get("realloc_hist", None)
    total_size = context.get("total_size", None)
    cache_lines = context.get("cache_lines", None)
    req_sizes = context.get("req_sizes", {})

    size = 0
    msg = ""

    # get size
    if trace.func == Function.free:
        # get size and delete old pointer
        if trace.ptr != 0:
            if trace.ptr not in allocations:
                msg = f"WARNING: free of invalid pointer {trace.ptr:x}\n"
            else:
                size = allocations.pop(trace.ptr) * -1
                msg = update_cache_lines(cache_lines, trace, size)

    else:
        # check for alignment
        if CHECK_ALIGNMENT:
            if (trace.ptr - CHECK_ALIGNMENT[1]) % CHECK_ALIGNMENT[0] != 0:
                msg += (f"WARNING: ptr: {trace.ptr:x} is not aligned to"
                        f" {CHECK_ALIGNMENT[0]} with offset {CHECK_ALIGNMENT[1]}\n")

        if trace.func == Function.calloc:
            size = trace.var_arg * trace.size
        else:
            size = trace.size

        allocations[trace.ptr] = size

        msg += update_cache_lines(cache_lines, trace, size)

        # update hist
        if hist is not None and trace.func != Function.free:
            hist[size] = hist.get(size, 0) + 1

        # special case realloc
        if trace.func == Function.realloc:
            # free old pointer
            old_size = allocations.pop(trace.var_arg, 0)

            if realloc_hist is not None:
                realloc_hist[(old_size, size)] = realloc_hist.get(
                    (old_size, size), 0)

            # size delta after realloc
            size -= old_size

    # update total size
    if total_size is not None:
        total_size.append(total_size[-1] + size)

    for req_size in req_sizes:
        if size == req_size:
            req_sizes[req_size].append(req_sizes[req_size][-1] + size)
        else:
            req_sizes[req_size].append(req_sizes[req_size][-1])

    return msg


def parse(path="chattymalloc.txt",
          hist=True,
          track_total=True,
          track_calls=True,
          realloc_hist=True,
          cache_lines=True,
          req_sizes=None):
    """parse a chattymalloc trace

    :returns: a context dict containing the histogram, a realloc histogram,
              a function call histogram, total live memory per function call,
              a dict mapping cache_lines to their owning TIDs
    """
    # context dictionary holding our parsed information
    context = {}

    # Dictionary to track all live allocations
    context["allocations"] = {}

    if track_calls:
        # function call histogram
        context["calls"] = {f: 0 for f in Function}

    if track_total:
        # List of total live memory per operation
        context["total_size"] = [0]

    if req_sizes:
        # allocation sizes to track
        context["req_sizes"] = req_sizes

    if hist:
        # Dictionary mapping allocation sizes to the count
        context["hist"] = {}

    if realloc_hist:
        # Dictionary mapping realloc sizes to their count
        context["realloc_hist"] = {}

    if cache_lines:
        # Dictionary mapping cache lines to their owning TIDs
        context["cache_lines"] = {}

    if EXPORT_TXT:
        plain_file = open(path+".txt", "w")

    with open(path, "rb") as trace_file:
        total_entries = os.stat(trace_file.fileno()).st_size // Trace.size
        update_interval = int(total_entries * 0.0005)
        if update_interval == 0:
            update_interval = 1

        i = 0
        entry = trace_file.read(Trace.size)
        while entry != b'':
            # print process
            if i % update_interval == 0:
                print(f"\r[{i} / {total_entries}] {(i/total_entries)*100:.2f}% parsed ...", end="")

            try:
                trace = Trace(entry)

                context["calls"][trace.func] += 1
                msg = record_allocation(trace, context)
                if msg:
                    print(f"entry {i}: {msg}", file=sys.stderr, end="")

            except ValueError as err:
                print(f"ERROR: {err} in entry {i}: {entry}", file=sys.stderr)

            if EXPORT_TXT:
                print((f"{trace.tid}: {trace.func.name} "
                       f"{hex(trace.ptr)} {trace.size} {trace.var_arg}"),
                      file=plain_file)

            i += 1
            entry = trace_file.read(Trace.size)

    print(f"\r[{i} / {total_entries}] {(i / total_entries) * 100:.2f}% parsed ...")
    if EXPORT_TXT:
        plain_file.close()
    return context


def plot(path):
    """Plot a histogram and a memory profile of the given chattymalloc trace"""
    result = parse(path=path)
    hist = result["hist"]

    plot_hist_ascii(f"{path}.hist", hist, result["calls"])

    top5 = [t[1] for t in sorted([(n, s) for s, n in hist.items()])[-5:]]

    plot_profile(path, path + ".profile.png", top5)


def plot_profile(trace_path, plot_path, sizes):
    """Plot a memory profile of the total memory and the top 5 sizes"""

    res = parse(path=trace_path,
                hist=False,
                realloc_hist=False,
                cache_lines=False,
                req_sizes={s: [0] for s in sizes})

    total_size = np.array(res["total_size"])
    del res["total_size"]

    x_vals = range(0, len(total_size))

    plt.plot(x_vals,
             total_size / 1000,
             marker='',
             linestyle='-',
             label="Total requested")

    for size in sizes:
        req_size = np.array(res["req_sizes"][size])
        del res["req_sizes"][size]
        plt.plot(x_vals, req_size / 1000, label=size)

    plt.legend(loc="lower center")
    plt.xlabel("Allocations")
    plt.ylabel("mem in kb")
    plt.title("Memusage profile")
    plt.savefig(plot_path)
    plt.clf()


def plot_hist_ascii(path, hist, calls):
    """Plot an ascii histogram"""
    bins = {}
    for size in sorted(hist):
        size_class = size // 16
        bins[size_class] = bins.get(size_class, 0) + hist[size]

    with open(path, "w") as hist_file:
        print("Total function calls:", sum(calls.values()), file=hist_file)
        for func, func_calls in calls.items():
            print(func.name, func_calls, file=hist_file)

        print(file=hist_file)

        total = sum(hist.values())
        top10 = [t[1] for t in sorted([(n, s) for s, n in hist.items()])[-10:]]
        top10_total = sum([hist[size] for size in top10])

        print(
            f"Top 10 allocation sizes {(top10_total/total)*100:.2f}% of all allocations",
            file=hist_file)
        for i, size in enumerate(reversed(top10)):
            print(f"{i+1}. {size} B occurred {hist[size]} times",
                  file=hist_file)
        print(file=hist_file)

        for i in [64, 1024, 4096]:
            allocations = sum([n for s, n in hist.items() if s <= i])
            print(
                f"allocations <= {i}: {allocations} {(allocations/total)*100:.2f}%",
                file=hist_file)
        print(file=hist_file)

        print("Histogram of sizes:", file=hist_file)
        sbins = sorted(bins)
        binmaxlength = len(str(sbins[-1])) + 1
        amountmaxlength = str(len(str(sorted(bins.values())[-1])))
        for current_bin in sbins:
            perc = bins[current_bin] / total * 100
            binsize = f"{{:<{binmaxlength}}} - {{:>{binmaxlength}}}"
            print(binsize.format(current_bin * 16, (current_bin + 1) * 16 - 1),
                  end=" ",
                  file=hist_file)
            amount = "{:<" + amountmaxlength + "} {:.2f}% {}"
            print(amount.format(bins[current_bin], perc, '*' * int(perc / 2)),
                  file=hist_file)


if __name__ == "__main__":
    # Code duplication with src.util.print_license_and_exit
    # to keep chattyparser independent from allocbench
    if "--license" in sys.argv:
        print("Copyright (C) 2018-2019 Florian Fischer")
        print(
            "License GPLv3: GNU GPL version 3 <http://gnu.org/licenses/gpl.html>"
        )
        sys.exit(0)

    parser = argparse.ArgumentParser(description="parse and analyse chattymalloc traces")
    parser.add_argument("trace",
                        help="binary trace file created by chattymalloc")
    parser.add_argument("--alignment",
                        nargs=2,
                        help="export to plain text format")
    parser.add_argument("--txt",
                        help="export to plain text format",
                        action="store_true")
    parser.add_argument("-v", "--verbose", help="more output", action='count')
    parser.add_argument("--license",
                        help="print license info and exit",
                        action='store_true')

    args = parser.parse_args()

    if args.alignment:
        CHECK_ALIGNMENT = [int(x) for x in args.alignment]
    EXPORT_TXT = args.txt
    plot(args.trace)
