import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import re

from benchmark import Benchmark

time_re = re.compile("^Time elapsed = (?P<time>\d*\.\d*) seconds.$")

class Benchmark_Falsesharing( Benchmark ):
    def __init__(self):
        self.name = "falsesharing"
        self.descrition = """This benchmarks makes small allocations and writes
                            to them multiple times. If the allocated objects are
                            on the same cache line the writes will be expensive because
                            of cache thrashing."""

        self.cmd = "build/cache-{bench}{binary_suffix} {threads} 100 8 1000000"

        self.args = {
                        "bench" : ["thrash", "scratch"],
                        "threads" : range(1, multiprocessing.cpu_count() * 2 + 1)
                    }

        self.requirements = ["build/cache-thrash", "build/cache-scratch"]
        super().__init__()

    def process_output(self, result, stdout, stderr, target, perm, verbose):
        result["time"] = time_re.match(stdout).group("time")

    def summary(self, sd=None):
        # Speedup thrash
        args = self.results["args"]
        nthreads = args["threads"]
        targets = self.results["targets"]

        sd = sd or ""

        for bench in self.results["args"]["bench"]:
            for target in targets:
                y_vals = []

                single_threaded_perm = self.Perm(bench=bench, threads=1)
                single_threaded = np.mean([float(m["time"])
                                                    for m in self.results[target][single_threaded_perm]])

                for perm in self.iterate_args_fixed({"bench" : bench}, args=args):

                    d = [float(m["time"]) for m in self.results[target][perm]]

                    y_vals.append(single_threaded / np.mean(d))

                plt.plot(nthreads, y_vals, marker='.', linestyle='-', label=target,
                            color=targets[target]["color"])

            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("speedup")
            plt.title(bench + " speedup" )
            plt.savefig(os.path.join(sd, self.name + "." + bench + ".png"))
            plt.clf()

            for target in targets:
                y_vals = []

                for perm in self.iterate_args_fixed({"bench" : bench}, args=args):
                    l1_load_misses = []

                    for m in self.results[target][perm]:
                        misses = 0
                        loads = 0
                        for e in m:
                            if "L1-dcache-load-misses" in e:
                                misses = float(m[e])
                            elif "L1-dcache-loads" in e:
                                loads = float(m[e])
                        l1_load_misses.append(misses/loads)

                    y_vals.append(np.mean(l1_load_misses) * 100)

                plt.plot(nthreads, y_vals, marker='.', linestyle='-', label=target, color=targets[target]["color"])
            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("l1-cache-misses in %")
            plt.title(bench + " cache-misses")
            plt.savefig(os.path.join(sd, self.name + "." + bench + ".l1misses.png"))
            plt.clf()

falsesharing = Benchmark_Falsesharing()
