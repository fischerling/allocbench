# Copyright 2018-2019 Florian Fischer <florian.fl.fischer@fau.de>
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

"""Definition of the falsesahring benchmark"""

import re

import matplotlib.pyplot as plt
import numpy as np

from src.benchmark import Benchmark

TIME_RE = re.compile("^Time elapsed = (?P<time>\\d*\\.\\d*) seconds.$")


class BenchmarkFalsesharing(Benchmark):
    """Falsesharing benchmark.

    This benchmarks makes small allocations and writes to them multiple
    times. If the allocated objects are on the same cache line the writes
    will be expensive because of cache thrashing.
    """

    def __init__(self):
        name = "falsesharing"

        self.cmd = "cache-{bench}{binary_suffix} {threads} 100 8 10000000"

        self.args = {"bench": ["thrash", "scratch"],
                     "threads": Benchmark.scale_threads_for_cpus(1)}

        self.requirements = ["cache-thrash", "cache-scratch"]
        super().__init__(name)

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):
        result["time"] = TIME_RE.match(stdout).group("time")

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

                    data = [float(m["time"]) for m in self.results[allocator][perm]]

                    y_vals.append(single_threaded / np.mean(data))

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
                            autoticks=False,
                            fixed=["bench"])

        self.plot_fixed_arg("({LLC-load-misses}/{LLC-loads})*100",
                            ylabel="'llc cache misses in %'",
                            title="'LLC misses: ' + arg + ' ' + str(arg_value)",
                            filepostfix="llc-misses",
                            autoticks=False,
                            fixed=["bench"])


falsesharing = BenchmarkFalsesharing()
