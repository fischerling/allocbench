import re
import matplotlib.pyplot as plt
import numpy as np

ptr = "(?:0x)?(?P<ptr>(?:\w+)|(?:\(nil\)))"
size = "(?P<size>\d+)"

malloc_re = re.compile("^m {} {}$".format(size, ptr))
free_re = re.compile("^f {}$".format(ptr))
calloc_re = re.compile("^c (?P<nmemb>\d+) {} {}$".format(size, ptr))
realloc_re = re.compile("^r {} {} {}$".format(ptr, size, ptr.replace("ptr", "nptr")))
memalign_re = re.compile("^mm (?P<alignment>\d+) {} {}$".format(size, ptr))

def record_allocation(hist, total_size, top5, top5_sizes, allocations, ptr, size, optr=None, add=True):
    size = int(size)
    if add:
        if optr and optr in allocations:
            size -= allocations[optr]
            del(allocations[optr])

        allocations[ptr] = size
        hist[size] = hist.get(size, 0) + 1

        if type(total_size[-1]) != int or type(size) != int:
            print("invalid type", type(total_size[-1]), type(size))
            return
        total_size.append(total_size[-1] + size)
        for s in top5:
            if s == size:
                top5_sizes[s].append(top5_sizes[s][-1] + s)
            else:
                top5_sizes[s].append(top5_sizes[s][-1])

    elif ptr != "(nil)" and ptr in allocations:
        size = allocations[ptr]
        total_size.append(total_size[-1] - size)
        for s in top5:
            if s == size:
                top5_sizes[s].append(top5_sizes[s][-1] - s)
            else:
                top5_sizes[s].append(top5_sizes[s][-1])
        del(allocations[ptr])

def parse(path="chattymalloc.data", track_top5=[]):
    tmalloc, tcalloc, trealloc, tfree, tmemalign= 0, 0, 0, 0, 0
    allocations = {}
    requested_size = [0]
    requested_size_top5 = {s: [0] for s in track_top5}
    hist = {}
    ln = 0

    with open(path, "r") as f:
        for i, l in enumerate(f.readlines()):
            ln += 1
            res = malloc_re.match(l)
            if res != None:
                res = res.groupdict()
                record_allocation(hist, requested_size, track_top5, requested_size_top5,
                    allocations, res["ptr"], res["size"])
                tmalloc += 1
                continue

            res = free_re.match(l)
            if res != None:
                res = res.groupdict()
                record_allocation(hist, requested_size, track_top5, requested_size_top5,
                    allocations, res["ptr"], 0, add=False)
                tfree +=1
                continue

            res = calloc_re.match(l)
            if res != None:
                res = res.groupdict()
                size = int(res["nmemb"]) * int(res["size"])
                record_allocation(hist, requested_size, track_top5, requested_size_top5,
                    allocations, res["ptr"], size)
                tcalloc += 1
                continue

            res = realloc_re.match(l)
            if res != None:
                res = res.groupdict()
                record_allocation(hist, requested_size, track_top5, requested_size_top5,
                    allocations, res["nptr"], res["size"], optr=res["ptr"])
                trealloc += 1
                continue

            res = memalign_re.match(l)
            if res != None:
                res = res.groupdict()
                record_allocation(hist, requested_size, track_top5, requested_size_top5,
                    allocations, res["ptr"], res["size"])
                tmemalign += 1
                continue

            print("\ninvalid line at", ln, ":", l)
    calls = {"malloc": tmalloc, "free": tfree, "calloc": tcalloc, "realloc": trealloc, "memalign": tmemalign}
    return hist, calls, requested_size, requested_size_top5

def hist(path="chattymalloc.data"):
    return parse(path=path)[0]

def plot_profile(total_size, total_top5, path):
    x_vals = list(range(0, len(total_size)))

    plt.plot(x_vals, total_size, marker='', linestyle='-', label="Total requested")

    for top5 in total_top5:
        plt.plot(x_vals, total_top5[top5], label=top5)

    plt.legend()
    plt.xlabel("Allocations")
    plt.ylabel("mem in kb")
    plt.title("Memusage profile")
    plt.savefig(path)
    plt.clf()


def plot_hist_ascii(hist, calls, path):
    bins = {}
    bin = 1
    for size in sorted(hist):
        if int(size) > bin * 16:
            bin += 1
        bins[bin] = bins.get(bin, 0) + hist[size]

    total = sum(calls.values())
    with open(path, "w") as f:
        print("Total function calls:", total, file=f)
        print("malloc:", calls["malloc"], file=f)
        print("calloc:", calls["calloc"], file=f)
        print("realloc:", calls["realloc"], file=f)
        print("free:", calls["free"], file=f)
        print("memalign:", calls["memalign"], file=f)

        print("Histogram of sizes:", file=f)
        for b in sorted(bins):
            perc = bins[b]/total*100
            hist_line = "{} - {}\t{}\t{:.2}% {}"
            print(hist_line.format((b-1)*16, b*16-1, bins[b], perc, '*'*int(perc/2)), file=f)
