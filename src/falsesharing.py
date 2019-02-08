import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import re

from src.benchmark import Benchmark

time_re = re.compile("^Time elapsed = (?P<time>\d*\.\d*) seconds.$")


class Benchmark_Falsesharing(Benchmark):
    def __init__(self):
        self.name = "falsesharing"
        self.descrition = """This benchmarks makes small allocations and writes
                             to them multiple times. If the allocated objects
                             are on the same cache line the writes will be
                             expensive because of cache thrashing."""

        self.cmd = "cache-{bench}{binary_suffix} {threads} 100 8 1000000"

        self.args = {
                        "bench": ["thrash", "scratch"],
                        "threads": range(1, multiprocessing.cpu_count() * 2 + 1)
                    }

        self.requirements = ["cache-thrash", "cache-scratch"]
        super().__init__()

    def process_output(self, result, stdout, stderr, allocator, perm, verbose):
        result["time"] = time_re.match(stdout).group("time")

    def summary(self):
        # Speedup thrash
        args = self.results["args"]
        nthreads = args["threads"]
        allocators = self.results["allocators"]

        for bench in self.results["args"]["bench"]:
            for allocator in allocators:
                y_vals = []

                single_threaded_perm = self.Perm(bench=bench, threads=1)
                single_threaded = np.mean([float(m["time"])
                                          for m in self.results[allocator][single_threaded_perm]])

                for perm in self.iterate_args_fixed({"bench": bench}, args=args):

                    d = [float(m["time"]) for m in self.results[allocator][perm]]

                    y_vals.append(single_threaded / np.mean(d))

                plt.plot(nthreads, y_vals, marker='.', linestyle='-',
                         label=allocator, color=allocators[allocator]["color"])

            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("speedup")
            plt.title(bench + " speedup")
            plt.savefig(self.name + "." + bench + ".png")
            plt.clf()

        self.plot_fixed_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                            ylabel="'l1 cache misses in %'",
                            title="'cache misses: ' + arg + ' ' + str(arg_value)",
                            filepostfix="l1-misses",
                            fixed=["bench"])

        self.plot_fixed_arg("({LLC-load-misses}/{LLC-loads})*100",
                            ylabel="'l1 cache misses in %'",
                            title="'LLC misses: ' + arg + ' ' + str(arg_value)",
                            filepostfix="llc-misses",
                            fixed=["bench"])


falsesharing = Benchmark_Falsesharing()
