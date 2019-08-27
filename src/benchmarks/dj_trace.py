"""Benchmark definition using the traces collected by DJ Delorie"""

import os
import sys
import re
from urllib.request import urlretrieve
import matplotlib.pyplot as plt
import numpy as np

from src.benchmark import Benchmark
from src.util import print_status


COMMA_SEP_NUMBER_RE = "(?:\\d*(?:,\\d*)?)*"
RSS_RE = f"(?P<rss>{COMMA_SEP_NUMBER_RE})"
TIME_RE = f"(?P<time>{COMMA_SEP_NUMBER_RE})"

CYCLES_RE = re.compile(f"^{TIME_RE} cycles$")
CPU_TIME_RE = re.compile(f"^{TIME_RE} usec across.*threads$")

MAX_RSS_RE = re.compile(f"^{RSS_RE} Kb Max RSS")
IDEAL_RSS_RE = re.compile("^{RSS_RE} Kb Max Ideal RSS")

MALLOC_RE = re.compile(f"^Avg malloc time:\\s*{TIME_RE} in.*calls$")
CALLOC_RE = re.compile(f"^Avg calloc time:\\s*{TIME_RE} in.*calls$")
REALLOC_RE = re.compile(f"^Avg realloc time:\\s*{TIME_RE} in.*calls$")
FREE_RE = re.compile(f"^Avg free time:\\s*{TIME_RE} in.*calls$")


class BenchmarkDJTrace(Benchmark):
    """DJ Trace Benchmark

    This benchmark uses the workload simulator written by DJ Delorie to
    simulate workloads provided by him under https://delorie.com/malloc. Those
    workloads are generated from traces of real aplications and are also used
    by delorie to measure improvements in the glibc allocator.
    """

    def __init__(self):
        self.name = "dj_trace"

        self.cmd = "trace_run{binary_suffix} dj_workloads/{workload}.wl"
        self.measure_cmd = ""

        self.args = {"workload": ["389-ds-2",
                                  "dj",
                                  "dj2",
                                  "mt_test_one_alloc",
                                  "oocalc",
                                  "qemu-virtio",
                                  "qemu-win7",
                                  "proprietary-1",
                                  "proprietary-2"]}
        self.results = {"389-ds-2": {
                            "malloc": 170500018, "calloc": 161787184,
                            "realloc": 404134, "free": 314856324,
                            "threads": 41},
                        "dj": {
                            "malloc": 2000000, "calloc": 200, "realloc": 0,
                            "free": 2003140, "threads": 201},
                        "dj2": {
                            "malloc": 29263321, "calloc": 3798404,
                            "realloc": 122956, "free": 32709054,
                            "threads": 36},
                        "mt_test_one_alloc": {
                            "malloc": 524290, "calloc": 1, "realloc": 0,
                            "free": 594788, "threads": 2},
                        "oocalc": {
                            "malloc": 6731734, "calloc": 38421,
                            "realloc": 14108, "free": 6826686, "threads": 88},
                        "qemu-virtio": {
                            "malloc": 1772163, "calloc": 146634,
                            "realloc": 59813, "free": 1954732, "threads": 3},
                        "qemu-win7": {
                            "malloc": 980904, "calloc": 225420,
                            "realloc": 89880, "free": 1347825, "threads": 6},
                        "proprietary-1": {
                            "malloc": 316032131, "calloc": 5642, "realloc": 84,
                            "free": 319919727, "threads": 20},
                        "proprietary-2": {
                            "malloc": 9753948, "calloc": 4693,
                            "realloc": 117, "free": 10099261, "threads": 19}}

        self.requirements = ["trace_run"]
        super().__init__()

    def prepare(self):
        super().prepare()

        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                status = "\r%5.1f%% %*d / %d" % (
                    percent, len(str(totalsize)), readsofar, totalsize)
                sys.stderr.write(status)
            else:  # total size is unknown
                sys.stderr.write(f"\rdownloaded {readsofar}")

        if not os.path.isdir("dj_workloads"):
            os.mkdir("dj_workloads")

        download_all = None
        wl_sizes = {"dj": "14M", "oocalc": "65M", "mt_test_one_alloc": "5.7M",
                    "proprietary-1": "2.8G", "qemu-virtio": "34M",
                    "proprietary-2": "92M", "qemu-win7": "23M",
                    "389-ds-2": "3.4G", "dj2": "294M"}

        for workload in self.args["workload"]:
            file_name = workload + ".wl"
            file_path = os.path.join("dj_workloads", file_name)
            if not os.path.isfile(file_path):
                if download_all is None:
                    choice = input(("Download all missing workloads"
                                    " (upto 6.7GB) [Y/n/x] "))
                    if choice == "x":
                        break
                    else:
                        download_all = choice in ['', 'Y', 'y']

                if not download_all:
                    choice = input(f"want to download {workload} ({wl_sizes[workload]}) [Y/n] ")
                    if choice not in ['', 'Y', 'y']:
                        continue

                else:
                    print_status(f"downloading {workload} ({wl_sizes[workload]}) ...")

                url = "http://www.delorie.com/malloc/" + file_name
                urlretrieve(url, file_path, reporthook)
                sys.stderr.write("\n")

        available_workloads = []
        for workload in self.args["workload"]:
            file_name = workload + ".wl"
            file_path = os.path.join("dj_workloads", file_name)
            if os.path.isfile(file_path):
                available_workloads.append(workload)

        if available_workloads:
            self.args["workload"] = available_workloads
            return True

        return False

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):
        def to_int(string):
            return int(string.replace(',', ""))


        regexs = {7: MALLOC_RE, 8: CALLOC_RE, 9: REALLOC_RE, 10: FREE_RE}
        functions = {7: "malloc", 8: "calloc", 9: "realloc", 10: "free"}
        for i, line in enumerate(stdout.splitlines()):
            if i == 0:
                result["cycles"] = to_int(CYCLES_RE.match(line).group("time"))
            elif i == 2:
                result["cputime"] = to_int(CPU_TIME_RE.match(line).group("time"))
            elif i == 3:
                result["Max_RSS"] = to_int(MAX_RSS_RE.match(line).group("rss"))
            elif i == 4:
                result["Ideal_RSS"] = to_int(IDEAL_RSS_RE.match(line).group("rss"))
            elif i in [7, 8, 9, 10]:
                res = regexs[i].match(line)
                fname = functions[i]
                result["avg_" + fname] = to_int(res.group("time"))

    def summary(self):
        args = self.results["args"]
        allocators = self.results["allocators"]

        cpu_time_means = {allocator: {} for allocator in allocators}
        cycles_means = {allocator: {} for allocator in allocators}
        for perm in self.iterate_args(args=args):
            for i, allocator in enumerate(allocators):
                data = [x["cputime"] for x in self.results[allocator][perm]]
                # data is in milliseconds
                cpu_time_means[allocator][perm] = np.mean(data)/1000

                data = [x["cycles"] for x in self.results[allocator][perm]]
                cycles_means[allocator][perm] = np.mean(data)

                plt.bar([i], cpu_time_means[allocator][perm], label=allocator,
                        color=allocators[allocator]["color"])

            plt.legend(loc="best")
            plt.ylabel("Zeit in ms")
            plt.title("Gesamte Laufzeit")
            plt.savefig(".".join([self.name, perm.workload, "runtime", "png"]))
            plt.clf()

        self.barplot_single_arg("{cputime}/1000",
                                ylabel='"time in ms"',
                                title='"total runtime"',
                                filepostfix="runtime")

        # Function Times
        func_times_means = {allocator: {} for allocator in allocators}
        xa = np.arange(0, 6, 1.5)
        for perm in self.iterate_args(args=args):
            for i, allocator in enumerate(allocators):
                x_vals = [x+i/len(allocators) for x in xa]

                func_times_means[allocator][perm] = [0, 0, 0, 0]

                func_times_means[allocator][perm][0] = np.mean([x["avg_malloc"] for x in self.results[allocator][perm]])
                func_times_means[allocator][perm][1] = np.mean([x["avg_calloc"] for x in self.results[allocator][perm]])
                func_times_means[allocator][perm][2] = np.mean([x["avg_realloc"] for x in self.results[allocator][perm]])
                func_times_means[allocator][perm][3] = np.mean([x["avg_free"] for x in self.results[allocator][perm]])

                plt.bar(x_vals, func_times_means[allocator][perm], width=0.25,
                        align="center", label=allocator,
                        color=allocators[allocator]["color"])

            plt.legend(loc="best")
            plt.xticks(xa + 1/len(allocators)*2,
                       ["malloc\n" + str(self.results[perm.workload]["malloc"]) + "\ncalls",
                        "calloc\n" + str(self.results[perm.workload]["calloc"]) + "\ncalls",
                        "realloc\n" + str(self.results[perm.workload]["realloc"]) + "\ncalls",
                        "free\n" + str(self.results[perm.workload]["free"]) + "\ncalls"])
            plt.ylabel("Durchschnittliche Zeit in cycles")
            plt.title("Durchscnittliche Laufzeiten der API Funktionen")
            plt.savefig(".".join([self.name, perm.workload, "apitimes", "png"]))
            plt.clf()

        # Memusage
        # hack ideal rss in data set
        allocators["Ideal_RSS"] = {"color": "C" + str(len(allocators) + 1)}
        self.results["stats"]["Ideal_RSS"] = {}
        for perm in self.iterate_args(args=args):
            ideal_rss = self.results[list(allocators.keys())[0]][perm][0]["Ideal_RSS"]/1000
            self.results["stats"]["Ideal_RSS"][perm] = {"mean": {"Max_RSS": ideal_rss}}

        self.barplot_single_arg("{Max_RSS}/1000",
                                ylabel='"Max RSS in MB"',
                                title='"Highwatermark of Vm (VmHWM)"',
                                filepostfix="newrss")

        del allocators["Ideal_RSS"]
        del self.results["stats"]["Ideal_RSS"]

        rss_means = {allocator: {} for allocator in allocators}
        for perm in self.iterate_args(args=args):
            for i, allocator in enumerate(allocators):
                d = [x["Max_RSS"] for x in self.results[allocator][perm]]
                # data is in kB
                rss_means[allocator][perm] = np.mean(d)/1000

                plt.bar([i], rss_means[allocator][perm], label=allocator,
                        color=allocators[allocator]["color"])

            # add ideal rss
            y_val = self.results[list(allocators.keys())[0]][perm][0]["Ideal_RSS"]/1000
            plt.bar([len(allocators)], y_val, label="Ideal RSS")

            plt.legend(loc="best")
            plt.ylabel("Max RSS in MB")
            plt.title("Maximal benötigter Speicher (VmHWM)")
            plt.savefig(".".join([self.name, perm.workload, "rss", "png"]))
            plt.clf()

        self.export_stats_to_csv("Max_RSS")
        self.export_stats_to_csv("cputime")

        self.export_stats_to_dataref("Max_RSS")
        self.export_stats_to_dataref("cputime")

        # Tables
        for perm in self.iterate_args(args=args):
            # collect data
            d = {allocator: {} for allocator in allocators}
            for i, allocator in enumerate(allocators):
                d[allocator]["time"] = [x["cputime"] for x in self.results[allocator][perm]]
                d[allocator]["rss"] = [x["Max_RSS"] for x in self.results[allocator][perm]]

            times = {allocator: np.mean(d[allocator]["time"]) for allocator in allocators}
            tmin = min(times)
            tmax = max(times)

            rss = {allocator: np.mean(d[allocator]["rss"]) for allocator in allocators}
            rssmin = min(rss)
            rssmax = max(rss)

            fname = ".".join([self.name, perm.workload, "table.tex"])
            with open(fname, "w") as f:
                print("\\documentclass{standalone}", file=f)
                print("\\usepackage{xcolor}", file=f)
                print("\\begin{document}", file=f)
                print("\\begin{tabular}{| l | l | l |}", file=f)
                print("& Zeit (ms) / $\\sigma$ (\\%) & VmHWM (KB) / $\\sigma$ (\\%) \\\\", file=f)
                print("\\hline", file=f)

                for allocator in allocators:
                    print(allocator.replace("_", "\\_"), end=" & ", file=f)

                    s = "\\textcolor{{{}}}{{{}}} / {}"

                    t = d[allocator]["time"]
                    m = times[allocator]
                    if m == tmin:
                        color = "green"
                    elif m == tmax:
                        color = "red"
                    else:
                        color = "black"
                    print(s.format(color, m, np.std(t)/m), end=" & ", file=f)

                    t = d[allocator]["rss"]
                    m = rss[allocator]
                    if m == rssmin:
                        color = "green"
                    elif m == rssmax:
                        color = "red"
                    else:
                        color = "black"
                    print(s.format(color, m, np.std(t)/m if m else 0), "\\\\", file=f)

                print("\\end{tabular}", file=f)
                print("\\end{document}", file=f)

        # Create summary similar to DJ's at
        # https://sourceware.org/ml/libc-alpha/2017-01/msg00452.html
        with open(self.name + "_plain.txt", "w") as f:
            # Absolutes
            fmt = "{:<20} {:>15} {:>7} {:>7} {:>7} {:>7} {:>7}"
            for i, allocator in enumerate(allocators):
                print("{0} {1} {0}".format("-" * 10, allocator), file=f)
                print(fmt.format("Workload", "Total", "malloc", "calloc",
                                 "realloc", "free", "RSS"), file=f)

                for perm in self.iterate_args(args=args):
                    cycles = cycles_means[allocator][perm]
                    times = [t for t in func_times_means[allocator][perm]]
                    rss = rss_means[allocator][perm]
                    print(fmt.format(perm.workload, cycles, times[0], times[1],
                                     times[2], times[3], rss), file=f)

                print(file=f)

            # Changes. First allocator in allocators is the reference
            fmt_changes = "{:<20} {:>14.0f}% {:>6.0f}% {:>6.0f}% {:>6.0f}% {:>6.0f}% {:>6.0f}%"
            for allocator in list(allocators)[1:]:
                print("{0} Changes {1} {0}".format("-" * 10, allocator), file=f)
                print(fmt.format("Workload", "Total", "malloc", "calloc",
                                 "realloc", "free", "RSS"), file=f)

                ref_alloc = list(allocators)[0]
                cycles_change_means = []
                times_change_means = []
                rss_change_means = []
                for perm in self.iterate_args(args=args):

                    normal_cycles = cycles_means[ref_alloc][perm]
                    if normal_cycles:
                        cycles = np.round(cycles_means[allocator][perm] / normal_cycles * 100)
                    else:
                        cycles = 0
                    cycles_change_means.append(cycles)

                    normal_times = func_times_means[ref_alloc][perm]
                    times = [0, 0, 0, 0]
                    for i in range(0, len(times)):
                        t = func_times_means[allocator][perm][i]
                        nt = normal_times[i]
                        if nt != 0:
                            times[i] = np.round(t/nt * 100)
                    times_change_means.append(times)

                    normal_rss = rss_means[ref_alloc][perm]
                    if normal_rss:
                        rss = np.round(rss_means[allocator][perm] / normal_rss * 100)
                    else:
                        rss = 0
                    rss_change_means.append(rss)

                    print(fmt_changes.format(perm.workload, cycles, times[0],
                                             times[1], times[2], times[3], rss),
                          file=f)
                print(file=f)
                tmeans = [0, 0, 0, 0]
                for i in range(0, len(times)):
                    tmeans[i] = np.mean([times[i] for times in times_change_means])
                print(fmt_changes.format("Mean:", np.mean(cycles_change_means),
                                         tmeans[0], tmeans[1], tmeans[2],
                                         tmeans[3], np.mean(rss_change_means)),
                      '\n', file=f)


dj_trace = BenchmarkDJTrace()
