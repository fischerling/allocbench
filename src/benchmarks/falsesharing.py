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
from src.globalvars import summary_file_ext


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
        args = self.results["args"]
        nthreads = args["threads"]
        allocators = self.results["allocators"]

        # calculate relevant datapoints: speedup, l1-cache-misses
        for bench in self.results["args"]["bench"]:
            for allocator in allocators:

                sequential_perm = self.Perm(bench=bench, threads=1)
                for perm in self.iterate_args_fixed({"bench": bench}, args=args):
                    speedup = []
                    l1chache_misses = []
                    for i, measure in enumerate(self.results[allocator][perm]):
                        sequential_time =  float(self.results[allocator][sequential_perm][i]["time"])
                        measure["speedup"] = sequential_time / float(measure["time"])
                        measure["l1chache_misses"] = eval("({L1-dcache-load-misses}/{L1-dcache-loads})*100".format(**measure))

        # delete and recalculate stats
        del self.results["stats"]
        self.calc_desc_statistics()

        self.plot_fixed_arg("{speedup}",
                            ylabel="'Speedup'",
                            title="'Speedup: ' + arg + ' ' + str(arg_value)",
                            filepostfix="speedup",
                            autoticks=False,
                            fixed=["bench"])

        self.plot_fixed_arg("{l1chache_misses}",
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

        self.write_tex_table([{"label": "Speedup",
                               "expression": "{speedup}",
                               "sort":">"}],
                             filepostfix="speedup.table")

        self.export_stats_to_csv("speedup", "time")
        self.export_stats_to_csv("l1chache_misses", "l1-misses")


falsesharing = BenchmarkFalsesharing()
