import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
from urllib.request import urlretrieve
import sys
import re
import shutil

from benchmark import Benchmark

comma_sep_number_re = "(?:\d*(?:,\d*)?)*"
rss_re = "(?P<rss>" + comma_sep_number_re + ")"
time_re = "(?P<time>" + comma_sep_number_re + ")"
calls_re = "(?P<calls>" + comma_sep_number_re + ")"

max_rss_re = re.compile("^{} Kb Max RSS".format(rss_re))
ideal_rss_re = re.compile("^{} Kb Max Ideal RSS".format(rss_re))

malloc_re = re.compile("^Avg malloc time:\s*{} in\s*{} calls$".format(time_re, calls_re))
calloc_re = re.compile("^Avg calloc time:\s*{} in\s*{} calls$".format(time_re, calls_re))
realloc_re = re.compile("^Avg realloc time:\s*{} in\s*{} calls$".format(time_re, calls_re))
free_re = re.compile("^Avg free time:\s*{} in\s*{} calls$".format(time_re, calls_re))

class Benchmark_DJ_Trace( Benchmark ):
    def __init__(self):
        self.name = "dj_trace"
        self.descrition = """This benchmark uses the workload simulator written
                             by DJ Delorie to simulate workloads provided by him
                             under https://delorie.com/malloc. Those workloads
                             are generated from traces of real aaplications and are
                             also used by delorie to measure improvements in the
                             glibc allocator.""",

        self.cmd = "build/trace_run{binary_suffix} dj_workloads/{workload}.wl"

        self.args = {
                        "workload" : [
                                        "389-ds-2",
                                        "dj",
                                        "dj2",
                                        "mt_test_one_alloc",
                                        "oocalc",
                                        "qemu-virtio",
                                        "qemu-win7",
                                        "proprietary-1",
                                        "proprietary-2",
                                      ]
                    }

        self.requirements = ["build/trace_run"]
        super().__init__()

    def prepare(self, verbose=False):
        super().prepare(verbose=verbose)

        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                s = "\r%5.1f%% %*d / %d" % (
                percent, len(str(totalsize)), readsofar, totalsize)
                sys.stderr.write(s)
            else: # total size is unknown
                sys.stderr.write("\rdownloaded %d" % (readsofar,))

        if not os.path.isdir("dj_workloads"):
            os.mkdir("dj_workloads")

        for wl in self.args["workload"]:
            file_name = wl + ".wl"
            file_path = os.path.join("dj_workloads", file_name)
            if not os.path.isfile(file_path):
                if input("want to download " + wl + " [Y/n] ") in ["", "Y", "y"]:
                    url = "http://www.delorie.com/malloc/" + file_name
                    urlretrieve(url, file_path, reporthook)
                    sys.stderr.write("\n")
        return True

    def process_output(self, result, stdout, stderr, target, perm, verbose):
        def to_int(s):
            return int(s.replace(',', ""))

        regexs = {7:malloc_re ,8:calloc_re, 9:realloc_re, 10:free_re}
        functions = {7:"malloc", 8:"calloc", 9:"realloc", 10:"free"}
        for i, l in enumerate(stdout.splitlines()):
            if i == 3:
                result["Max_RSS"] = to_int(max_rss_re.match(l).group("rss"))
            elif i == 4:
                result["Ideal_RSS"] = to_int(ideal_rss_re.match(l).group("rss"))
            elif i in [7, 8, 9, 10]:
                res = regexs[i].match(l)
                fname = functions[i]
                result["avg_" + fname] = to_int(res.group("time"))
                if not perm.workload in self.results:
                    self.results[perm.workload] = {"malloc_calls":0, "calloc_calls":0,
                                            "realloc_calls":0, "free_calls":0}
                self.results[perm.workload][fname + "_calls"] = res.group("calls")

    def summary(self, sd=None):
        args = self.results["args"]
        targets = self.results["targets"]

        sd = sd or ""

        # Total times
        for perm in self.iterate_args():
            for i, target in enumerate(targets):
                d = [float(x["task-clock"]) for x in self.results[target][perm]]
                y_val = np.mean(d)
                plt.bar([i], y_val, label=target, color=targets[target]["color"])

            plt.legend(loc="lower right")
            plt.ylabel("Time in ms")
            plt.title("Runtime of " + perm.workload + ":")
            plt.savefig(os.path.join(sd, ".".join([self.name, perm.workload, "runtime", "png"])))
            plt.clf()

        # Function Times
        xa = np.arange(0, 6, 1.5)
        for perm in self.iterate_args():
            for i, target in enumerate(targets):
                x_vals = [x-i/len(targets) for x in xa]
                y_vals = [0] * 4
                y_vals[0] = np.mean([x["avg_malloc"] for x in self.results[target][perm]])
                y_vals[1] = np.mean([x["avg_calloc"] for x in self.results[target][perm]])
                y_vals[2] = np.mean([x["avg_realloc"] for x in self.results[target][perm]])
                y_vals[3] = np.mean([x["avg_free"] for x in self.results[target][perm]])
                plt.bar(x_vals, y_vals, width=0.25, align="center",
                        label=target, color=targets[target]["color"])

            plt.legend(loc="best")
            plt.xticks(xa, ["malloc\n" + str(self.results[perm.workload]["malloc_calls"]) + "\ncalls",
                            "calloc\n" + str(self.results[perm.workload]["calloc_calls"]) + "\ncalls",
                            "realloc\n" + str(self.results[perm.workload]["realloc_calls"]) + "\ncalls",
                            "free\n" + str(self.results[perm.workload]["free_calls"]) + "\ncalls"])
            plt.ylabel("Avg ticks per function")
            plt.title("Avg API call times " + perm.workload + ":")
            plt.savefig(os.path.join(sd, ".".join([self.name, perm.workload, "apitimes", "png"])))
            plt.clf()

        # Memusage
        for perm in self.iterate_args():
            for i, target in enumerate(targets):
                d = [x["Max_RSS"] for x in self.results[target][perm]]
                y_val = np.mean(d)
                plt.bar([i], y_val, label=target, color=targets[target]["color"])

            # add ideal rss
            y_val = self.results[list(targets.keys())[0]][perm][0]["Ideal_RSS"]
            plt.bar([len(targets)], y_val, label="Ideal RSS")

            plt.legend(loc="best")
            plt.ylabel("Max RSS in Kb")
            plt.title("Max RSS " + perm.workload + ":")
            plt.savefig(os.path.join(sd, ".".join([self.name, perm.workload, "rss", "png"])))
            plt.clf()

dj_trace = Benchmark_DJ_Trace()
