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
"""Benchmark definition using the traces collected by DJ Delorie"""

import re
import numpy as np

from allocbench.artifact import ArchiveArtifact
from allocbench.benchmark import Benchmark
import allocbench.plots as abplt

COMMA_SEP_NUMBER_RE = "(?:\\d*(?:,\\d*)?)*"
RSS_RE = f"(?P<rss>{COMMA_SEP_NUMBER_RE})"
TIME_RE = f"(?P<time>{COMMA_SEP_NUMBER_RE})"

CYCLES_RE = re.compile(f"^{TIME_RE} cycles$")
CPU_TIME_RE = re.compile(f"^{TIME_RE} usec across.*threads$")

MAX_RSS_RE = re.compile(f"^{RSS_RE} Kb Max RSS")
IDEAL_RSS_RE = re.compile(f"^{RSS_RE} Kb Max Ideal RSS")

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
        name = "dj_trace"

        self.cmd = "trace_run{binary_suffix} {workload_dir}/dj_workloads/{workload}.wl"
        self.measure_cmd = ""

        self.args = {
            "workload": [
                "389-ds-2", "dj", "dj2", "mt_test_one_alloc", "oocalc",
                "qemu-virtio", "qemu-win7", "proprietary-1", "proprietary-2"
            ]
        }

        self.results = {
            "389-ds-2": {
                "malloc": 170500018,
                "calloc": 161787184,
                "realloc": 404134,
                "free": 314856324,
                "threads": 41
            },
            "dj": {
                "malloc": 2000000,
                "calloc": 200,
                "realloc": 0,
                "free": 2003140,
                "threads": 201
            },
            "dj2": {
                "malloc": 29263321,
                "calloc": 3798404,
                "realloc": 122956,
                "free": 32709054,
                "threads": 36
            },
            "mt_test_one_alloc": {
                "malloc": 524290,
                "calloc": 1,
                "realloc": 0,
                "free": 594788,
                "threads": 2
            },
            "oocalc": {
                "malloc": 6731734,
                "calloc": 38421,
                "realloc": 14108,
                "free": 6826686,
                "threads": 88
            },
            "qemu-virtio": {
                "malloc": 1772163,
                "calloc": 146634,
                "realloc": 59813,
                "free": 1954732,
                "threads": 3
            },
            "qemu-win7": {
                "malloc": 980904,
                "calloc": 225420,
                "realloc": 89880,
                "free": 1347825,
                "threads": 6
            },
            "proprietary-1": {
                "malloc": 316032131,
                "calloc": 5642,
                "realloc": 84,
                "free": 319919727,
                "threads": 20
            },
            "proprietary-2": {
                "malloc": 9753948,
                "calloc": 4693,
                "realloc": 117,
                "free": 10099261,
                "threads": 19
            }
        }

        for workload in self.results:
            self.results[workload]["ideal_rss"] = 0

        self.requirements = ["trace_run"]
        super().__init__(name)

        self.workloads = ArchiveArtifact(
            "dj_workloads",
            "https://www4.cs.fau.de/~flow/allocbench/dj_workloads.tar.xz",
            "tar", "c9bc499eeba8023bca28a755fffbaf9200a335ad")

        self.workload_dir = None

    def prepare(self):
        """Download and extract workload files"""
        self.workload_dir = self.workloads.provide()

    def process_output(self, result, stdout, stderr, allocator, perm):  # pylint: disable=too-many-arguments, unused-argument
        """parse and store function times and rss usage"""
        def to_int(string):
            return int(string.replace(',', ""))

        regexs = {7: MALLOC_RE, 8: CALLOC_RE, 9: REALLOC_RE, 10: FREE_RE}
        functions = {7: "malloc", 8: "calloc", 9: "realloc", 10: "free"}
        for i, line in enumerate(stdout.splitlines()):
            if i == 0:
                result["cycles"] = to_int(CYCLES_RE.match(line).group("time"))
            elif i == 2:
                result["cputime"] = to_int(
                    CPU_TIME_RE.match(line).group("time"))
            elif i == 3:
                result["Max_RSS"] = to_int(MAX_RSS_RE.match(line).group("rss"))
            elif i == 4:
                self.results[perm.workload]["ideal_rss"] = to_int(
                    IDEAL_RSS_RE.match(line).group("rss"))
            elif i in [7, 8, 9, 10]:
                res = regexs[i].match(line)
                fname = functions[i]
                result["avg_" + fname] = to_int(res.group("time"))

    def summary(self):
        """Create time, rss usage plots and a plain text summary like the one from DJ Delorie"""

        import matplotlib.pyplot as plt  # pylint: disable=import-outside-toplevel
        from allocbench.plots import SUMMARY_FILE_EXT  # pylint: disable=import-outside-toplevel

        args = self.results["args"]
        allocators = self.results["allocators"]

        abplt.plot(self,
                   "{cputime}/1000",
                   plot_type='bar',
                   fig_options={
                       'ylabel': "time in ms",
                       'title': "total runtime",
                   },
                   file_postfix="runtime")

        # Function Times
        func_times_means = {allocator: {} for allocator in allocators}
        xval_start_array = np.arange(0, 6, 1.5)
        for perm in self.iterate_args(args=args):
            for i, allocator in enumerate(allocators):
                x_vals = [
                    x_start + i / len(allocators)
                    for x_start in xval_start_array
                ]

                func_times_means[allocator][perm] = []

                func_times_means[allocator][perm].extend(
                    abplt.get_y_data(self, "{avg_malloc}", allocator, perm))
                func_times_means[allocator][perm].extend(
                    abplt.get_y_data(self, "{avg_calloc}", allocator, perm))
                func_times_means[allocator][perm].extend(
                    abplt.get_y_data(self, "{avg_realloc}", allocator, perm))
                func_times_means[allocator][perm].extend(
                    abplt.get_y_data(self, "{avg_free}", allocator, perm))

                plt.bar(x_vals,
                        func_times_means[allocator][perm],
                        width=0.25,
                        align="center",
                        label=allocator,
                        color=allocators[allocator]["color"])

            plt.legend(loc="best")
            plt.xticks(xval_start_array + 1 / len(allocators) * 2, [
                "malloc\n" + str(self.results[perm.workload]["malloc"]) +
                "\ncalls", "calloc\n" +
                str(self.results[perm.workload]["calloc"]) + "\ncalls",
                "realloc\n" + str(self.results[perm.workload]["realloc"]) +
                "\ncalls",
                "free\n" + str(self.results[perm.workload]["free"]) + "\ncalls"
            ])
            plt.ylabel("cycles")
            plt.title(f"Avg. runtime of API functions {perm.workload}")
            plt.savefig(".".join(
                [self.name, perm.workload, "apitimes", SUMMARY_FILE_EXT]))
            plt.clf()

        # Memusage
        # hack ideal rss in data set
        allocators["Ideal_RSS"] = {"color": "xkcd:gold"}
        self.results["stats"]["Ideal_RSS"] = {}
        for perm in self.iterate_args(args=args):
            ideal_rss = self.results[perm.workload]["ideal_rss"] / 1000
            self.results["stats"]["Ideal_RSS"][perm] = {
                "mean": {
                    "Max_RSS": ideal_rss
                },
                "std": {
                    "Max_RSS": 0
                }
            }

        abplt.plot(self,
                   "{Max_RSS}/1000",
                   plot_type='bar',
                   fig_options={
                       'ylabel': "Max RSS in MB",
                       'title': "Max RSS (VmHWM)",
                   },
                   file_postfix="newrss")

        del allocators["Ideal_RSS"]
        del self.results["stats"]["Ideal_RSS"]

        rss_means = {allocator: {} for allocator in allocators}
        for perm in self.iterate_args(args=args):
            for i, allocator in enumerate(allocators):
                # data is in kB
                rss_means[allocator][perm] = abplt.get_y_data(
                    self, "{Max_RSS} / 1000", allocator, perm)[0]

                plt.bar([i],
                        rss_means[allocator][perm],
                        label=allocator,
                        color=allocators[allocator]["color"])

            # add ideal rss
            y_val = self.results[perm.workload]['ideal_rss'] / 1000
            plt.bar([len(allocators)], y_val, label="Ideal RSS")

            plt.legend(loc="best")
            plt.ylabel("Max RSS in MB")
            plt.title(f"Maximal RSS (VmHWM) {perm.workload}")
            plt.savefig(".".join(
                [self.name, perm.workload, "rss", SUMMARY_FILE_EXT]))
            plt.clf()

        abplt.export_stats_to_csv(self, "Max_RSS")
        abplt.export_stats_to_csv(self, "cputime")

        abplt.export_stats_to_dataref(self, "Max_RSS")
        abplt.export_stats_to_dataref(self, "cputime")

        # Big table
        abplt.write_tex_table(self, [{
            "label": "Runtime [ms]",
            "expression": "{cputime}/1000",
            "sort": "<"
        }, {
            "label": "Max RSS [MB]",
            "expression": "{Max_RSS}/1000",
            "sort": "<"
        }],
                              file_postfix="table")

        # Create summary similar to DJ's at
        # https://sourceware.org/ml/libc-alpha/2017-01/msg00452.html
        cycles_means = {
            allocator: {
                perm: self.results["stats"][allocator][perm]["mean"]
                for perm in self.iterate_args(args=args)
            }
            for allocator in allocators
        }

        with open(self.name + "_plain.txt", "w") as summary_file:
            # Absolutes
            fmt = "{:<20} {:>15} {:>7} {:>7} {:>7} {:>7} {:>7}"
            for i, allocator in enumerate(allocators):
                print("{0} {1} {0}".format("-" * 10, allocator),
                      file=summary_file)
                print(fmt.format("Workload", "Total", "malloc", "calloc",
                                 "realloc", "free", "RSS"),
                      file=summary_file)

                for perm in self.iterate_args(args=args):
                    cycles = abplt.get_y_data(self, "{cycles}", allocator,
                                              perm)[0]
                    times = func_times_means[allocator][perm]
                    rss = rss_means[allocator][perm]
                    print(fmt.format(perm.workload, cycles, times[0], times[1],
                                     times[2], times[3], rss),
                          file=summary_file)

                print(file=summary_file)

            # Changes. First allocator in allocators is the reference
            fmt_changes = "{:<20} {:>14.0f}% {:>6.0f}% {:>6.0f}% {:>6.0f}% {:>6.0f}% {:>6.0f}%"
            for allocator in list(allocators)[1:]:
                print("{0} Changes {1} {0}".format("-" * 10, allocator),
                      file=summary_file)
                print(fmt.format("Workload", "Total", "malloc", "calloc",
                                 "realloc", "free", "RSS"),
                      file=summary_file)

                ref_alloc = list(allocators)[0]
                cycles_change_means = []
                times_change_means = []
                rss_change_means = []
                for perm in self.iterate_args(args=args):

                    normal_cycles = cycles_means[ref_alloc][perm]
                    if normal_cycles:
                        cycles = np.round(cycles_means[allocator][perm] /
                                          normal_cycles * 100)
                    else:
                        cycles = 0
                    cycles_change_means.append(cycles)

                    normal_times = func_times_means[ref_alloc][perm]
                    times = [0, 0, 0, 0]
                    for i in range(0, len(times)):
                        func_time = func_times_means[allocator][perm][i]
                        normalized_func_time = normal_times[i]
                        if normalized_func_time != 0:
                            times[i] = np.round(func_time /
                                                normalized_func_time * 100)
                    times_change_means.append(times)

                    normal_rss = rss_means[ref_alloc][perm]
                    if normal_rss:
                        rss = np.round(rss_means[allocator][perm] /
                                       normal_rss * 100)
                    else:
                        rss = 0
                    rss_change_means.append(rss)

                    print(fmt_changes.format(perm.workload, cycles, times[0],
                                             times[1], times[2], times[3],
                                             rss),
                          file=summary_file)
                print(file=summary_file)
                tmeans = [0, 0, 0, 0]
                for i in range(0, len(times)):
                    tmeans[i] = np.mean(
                        [times[i] for times in times_change_means])
                print(fmt_changes.format("Mean:", np.mean(cycles_change_means),
                                         tmeans[0], tmeans[1], tmeans[2],
                                         tmeans[3], np.mean(rss_change_means)),
                      '\n',
                      file=summary_file)
