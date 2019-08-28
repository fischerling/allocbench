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

"""Definition of the larson benchmark"""

import re

from src.benchmark import Benchmark

THROUGHPUT_RE = re.compile("^Throughput =\\s*(?P<throughput>\\d+) operations per second.$")


class BenchmarkLarson(Benchmark):
    """Larson server benchmark

    This benchmark is courtesy of Paul Larson at Microsoft Research. It
    simulates a server: each thread allocates and deallocates objects, and then
    transfers some objects (randomly selected) to other threads to be freed.
    """

    def __init__(self):
        self.name = "larson"

        # Parameters taken from the paper "Memory Allocation for Long-Running Server
        # Applications" from Larson and Krishnan
        self.cmd = "larson{binary_suffix} 1 8 {maxsize} 1000 50000 1 {threads}"

        self.args = {"maxsize": [64, 512, 1024],
                     "threads": Benchmark.scale_threads_for_cpus(2)}

        self.requirements = ["larson"]
        super().__init__()

    @staticmethod
    def process_output(result, stdout, stderr, target, perm):
        for line in stdout.splitlines():
            res = THROUGHPUT_RE.match(line)
            if res:
                result["throughput"] = int(res.group("throughput"))
                return

    def summary(self):
        # Plot threads->throughput and maxsize->throughput
        self.plot_fixed_arg("{throughput}/1000000",
                            ylabel="'MOPS/s'",
                            title="'Larson: ' + arg + ' ' + str(arg_value)",
                            filepostfix="throughput")

        self.plot_fixed_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                            ylabel="'l1 cache misses in %'",
                            title="'Larson cache misses: ' + arg + ' ' + str(arg_value)",
                            filepostfix="cachemisses")


larson = BenchmarkLarson()
