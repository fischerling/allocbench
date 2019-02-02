import re
import matplotlib.pyplot as plt

ptr = "(?:0x)?(?P<ptr>(?:\w+)|(?:\(nil\)))"
size = "(?P<size>\d+)"

malloc_re = re.compile("^m {} {}$".format(size, ptr))
free_re = re.compile("^f {}$".format(ptr))
calloc_re = re.compile("^c (?P<nmemb>\d+) {} {}$".format(size, ptr))
realloc_re = re.compile("^r {} {} {}$".format(ptr, size, ptr.replace("ptr", "nptr")))
memalign_re = re.compile("^mm (?P<alignment>\d+) {} {}$".format(size, ptr))


def record_allocation(hist, total_size, allocations, ptr, size, coll_size,
                      req_size, nohist, optr=None, add=True):
    size = int(size)
    if add:
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

    elif ptr != "(nil)" and ptr in allocations:
        size = allocations[ptr]
        if coll_size:
            if not req_size or size == req_size:
                total_size.append(total_size[-1] - size)
            elif req_size:
                total_size.append(total_size[-1])

        del(allocations[ptr])
    elif coll_size:
        total_size.append(total_size[-1])


def parse(path="chattymalloc.data", coll_size=True, req_size=None, nohist=False):
    tmalloc, tcalloc, trealloc, tfree, tmemalign = 0, 0, 0, 0, 0
    allocations = {}
    requested_size = [0]
    hist = {}
    ln = 0

    with open(path, "r") as f:
        for i, l in enumerate(f.readlines()):
            ln += 1
            res = malloc_re.match(l)
            if res is not None:
                res = res.groupdict()
                record_allocation(hist, requested_size, allocations, res["ptr"],
                                  res["size"], coll_size, req_size, nohist)
                tmalloc += 1
                continue

            res = free_re.match(l)
            if res is not None:
                res = res.groupdict()
                record_allocation(hist, requested_size, allocations, res["ptr"],
                                  0, coll_size, req_size, nohist, add=False)
                tfree += 1
                continue

            res = calloc_re.match(l)
            if res is not None:
                res = res.groupdict()
                size = int(res["nmemb"]) * int(res["size"])
                record_allocation(hist, requested_size, allocations, res["ptr"],
                                  size, coll_size, req_size, nohist)
                tcalloc += 1
                continue

            res = realloc_re.match(l)
            if res is not None:
                res = res.groupdict()
                record_allocation(hist, requested_size, allocations, res["nptr"],
                                  res["size"], coll_size, req_size, nohist,
                                  optr=res["ptr"])
                trealloc += 1
                continue

            res = memalign_re.match(l)
            if res is not None:
                res = res.groupdict()
                record_allocation(hist, requested_size, allocations, res["ptr"],
                                  res["size"], coll_size, req_size, nohist)
                tmemalign += 1
                continue

            print("\ninvalid line at", ln, ":", l)
    calls = {"malloc": tmalloc, "free": tfree, "calloc": tcalloc,
             "realloc": trealloc, "memalign": tmemalign}
    return hist, calls, requested_size


def plot(path):
    hist, calls, _ = parse(req_size=None)
    plot_hist_ascii(path+".hist", hist, calls)
    top5 = [t[1] for t in sorted([(n, s) for s, n in hist.items()])[-5:]]

    del(hist)
    del(calls)
    plot_profile(path+".profile.png", top5)


def plot_profile(path, top5):
    _, calls, total_size = parse(nohist=True)
    x_vals = range(0, sum(calls.values()) + 1)

    plt.plot(x_vals, total_size, marker='',
             linestyle='-', label="Total requested")

    for s in top5:
        _, calls, total_size = parse(nohist=True, req_size=s)
        plt.plot(x_vals, total_size, label=s)

    plt.legend()
    plt.xlabel("Allocations")
    plt.ylabel("mem in kb")
    plt.title("Memusage profile")
    plt.savefig(path)
    plt.clf()


def plot_hist_ascii(path, hist, calls):
    bins = {}
    for size in sorted(hist):
        bin = int(size / 16)
        bins[bin] = bins.get(bin, 0) + hist[size]

    total = sum(calls.values()) - calls["free"]
    with open(path, "w") as f:
        print("Total function calls:", total, file=f)
        print("malloc:", calls["malloc"], file=f)
        print("calloc:", calls["calloc"], file=f)
        print("realloc:", calls["realloc"], file=f)
        print("free:", calls["free"], file=f)
        print("memalign:", calls["memalign"], file=f)
        print(file=f)

        print("< 1024", sum([n for s, n in hist.items() if s < 1024]), file=f)
        print("< 4096", sum([n for s, n in hist.items() if s < 4096]), file=f)
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
