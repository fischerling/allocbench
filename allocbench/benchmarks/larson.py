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
"""Larson server benchmark

This benchmark was build by Paul Larson at Microsoft Research. It
simulates a server: each thread has a set of allocations. From which it selects
a random slot. The allocation in this slot is freed, a new one with a random size
allocated, written to and stored in the selected slot. When a thread finished its
allocations it will pass its objects to a new thread.

Larson benchmark usage: ./larson sleep min-size max-size chunks malloc_frees seed threads

In the paper "Memory Allocation for Long-Running Server Applications" the authors
use 1000 chunks per thread and 50000 malloc and free pairs per thread which
correspond to a "bleeding rate" of 2% which they observed in real world systems.
The allocations are uniformly distributed between min-size and max-size.

allocbench runs larson with different distributions and thread counts.
The other arguments are the same as the original authors used in their paper.

mimalloc-bench uses 1000 chunks per thread and 10000 malloc and free pairs
simulating 10% bleeding. I don't know why they use different values than the
original paper.


Interpretation:

This benchmark is intended to model a real world server workload.
But the use of a uniformly distribution of allocation sizes clearly differs from
real applications. Although the results can be a metric of scalability and
false sharing because it uses multiple threads, which pass memory around.
"""

import re

from allocbench.benchmark import Benchmark

THROUGHPUT_RE = re.compile(
    "^Throughput =\\s*(?P<throughput>\\d+) operations per second.$")


class BenchmarkLarson(Benchmark):
    """Definition of the larson benchmark"""
    def __init__(self):
        name = "larson"

        # Parameters taken from the paper "Memory Allocation for Long-Running Server
        # Applications" from Larson and Krishnan
        self.cmd = "larson{binary_suffix} 5 8 {maxsize} 1000 50000 1 {threads}"

        self.args = {
            "maxsize": [64, 512, 1024],
            "threads": Benchmark.scale_threads_for_cpus(2)
        }

        self.requirements = ["larson"]
        super().__init__(name)

    @staticmethod
    def process_output(result, stdout, stderr, target, perm):  # pylint: disable=too-many-arguments, unused-argument
        """Extract and store throughput from larson's output"""
        for line in stdout.splitlines():
            res = THROUGHPUT_RE.match(line)
            if res:
                result["throughput"] = int(res.group("throughput"))
                return

    def summary(self):
        """Create plots showing throughput and L1 data chache miss rate"""
        import allocbench.plots as plt  # pylint: disable=import-outside-toplevel

        # Plot threads->throughput and maxsize->throughput
        plt.plot(self,
                 "{throughput}/1000000",
                 fig_options={
                     'ylabel': "MOPS/s",
                     'title': "Larson: {fixed_part_str}",
                 },
                 file_postfix="throughput")

        plt.plot(self,
                 "({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                 fig_options={
                     'ylabel': "l1 cache misses in %",
                     'title': "Larson cache misses: {fixed_part_str}",
                 },
                 file_postfix="cachemisses")
