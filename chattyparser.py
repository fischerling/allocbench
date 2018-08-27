import re

rss_re = re.compile("^VmRSS:\s+(\d+) kB$")

ptr = "(?:0x)?(?P<ptr>(?:\w+)|(?:\(nil\)))"
size = "(?P<size>\d+)"
time = "(?P<time>\d+)"
tid = "(?P<tid>\d+)"

malloc_re = re.compile("^{} {} ma {} {}$".format(time, tid, size, ptr))
free_re = re.compile("^{} {} f {}$".format(time, tid, ptr))
calloc_re = re.compile("^{} {} c (?P<nmemb>\d+) {} {}$".format(time, tid, size, ptr))
realloc_re = re.compile("^{} {} r {} {} {}$".format(time, tid, ptr, size, ptr.replace("ptr", "nptr")))
memalign_re = re.compile("^{} {} mm (?P<alignment>\d+) {} {}$".format(time, tid, size, ptr))

def analyse(path="chattymalloc.data"):
    allocations = {}
    requested_size = [0]
    hist = {}
    ln = 0

    with open(path, "r") as f:
        #Skip first empty line. See chattymalloc.c why it is there.
        # for bl in f.readlines()[1:]:
        for l in f.readlines():
            ln += 1
            res = malloc_re.match(l)
            if res != None:
                res = res.groupdict()
                size = int(res["size"])
                allocations[res["ptr"]] = size
                requested_size.append(requested_size[-1] + size)

                hist[size] = hist.get(size, 0)
                continue

            res = free_re.match(l)
            if res != None:
                res = res.groupdict()
                ptr = res["ptr"]
                if ptr == "(nil)" or len(ptr) != 12:
                    continue
                requested_size.append(requested_size[-1] - allocations[ptr])
                del(allocations[ptr])
                continue

            res = calloc_re.match(l)
            if res != None:
                res = res.groupdict()
                size = int(res["nmemb"]) * int(res["size"])
                allocations[res["ptr"]] = size
                requested_size.append(requested_size[-1] + size)

                hist[size] = hist.get(size, 0)
                continue

            res = realloc_re.match(l)
            if res != None:
                res = res.groupdict()
                optr, size, nptr = res["ptr"], int(res["size"]), res["nptr"]
                if optr == nptr:
                    requested_size.append(requested_size[-1] + size - allocations[nptr])
                    allocations[nptr] = size
                else:
                    if optr in allocations:
                        requested_size.append(requested_size[-1] + size - allocations[optr])
                        del(allocations[optr])
                    else:
                        requested_size.append(requested_size[-1] + size)
                        
                    allocations[nptr] = size
                continue

            res = memalign_re.match(l)
            if res != None:
                res = res.groupdict()
                size, ptr = int(res["size"]), res["ptr"]
                allocations[ptr] = size
                requested_size.append(requested_size[-1] + size)

                hist[size] = hist.get(size, 0)
                continue

            print("\ninvalid line at", ln, ":", l)
    return requested_size, hist

def hist(path="chattymalloc.data"):
    return analyse(path=path)[1]
