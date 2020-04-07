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
"""Definition of the loop micro benchmark

This benchmark allocates and immediately deallocates a pseudo random sized allocation
N times in T threads. The acquired memory is neither read nor written. Not using the
allocations at all maybe seems odd but this micro benchmark should only measure
the allocators fast paths, scalability and management overhead.
Using the allocations will add cache effects to our results which are
measured for example in the false sharing or larson benchmarks.

Observations:
* Glibc's factor two faster for allocations <= 1024B
* TCMalloc suffers when allocating only small chunks

Interpretation:
* A significant higher cache miss rate than other allocators could mean that
  internals suffer from false sharing (TCMalloc).
* Speed changes with constant threads but changing sizes may show performance
  differences in differing strategies for seperate sizes (glibc thread caches < 1032B)
"""

from src.benchmark import Benchmark
import src.plots as plt


class BenchmarkLoop(Benchmark):
    """Loop micro benchmark

    This benchmark allocates and frees n blocks in t concurrent threads.
    """
    def __init__(self):
        name = "loop"

        self.cmd = "loop{binary_suffix} {threads} 1000000 {maxsize}"

        self.args = {
            "maxsize": [2**x for x in range(6, 16)],
            "threads": Benchmark.scale_threads_for_cpus(2)
        }

        self.requirements = ["loop"]
        super().__init__(name)

    def process_output(self, result, stdout, stderr, alloc, perm):
        result["mops"] = perm.threads / float(result["task-clock"])

    def summary(self):
        # Speed
        plt.plot(
            self,
            "{mops}",
            fig_options={
                'ylabel': 'MOPS/cpu-second',
                'title': 'Loop: {fixed_part_str}',
                'autoticks': False,
            },
            file_postfix="time")

        # L1 cache misses
        plt.plot(
            self,
            "({L1-dcache-load-misses}/{L1-dcache-loads})*100",
            fig_options={
                'ylabel': "L1 misses in %",
                'title': "Loop l1 cache misses: {fixed_part_str}",
                'autoticks': False,
            },
            file_postfix="l1misses")

        # Speed Matrix
        plt.write_best_doublearg_tex_table(
            self,
            "{mops}",
            file_postfix="time.matrix")

        plt.write_tex_table(
            self, 
            [{
                "label": "MOPS/s",
                "expression": "{mops}",
                "sort": ">"
            }],
            file_postfix="mops.table")

        plt.export_stats_to_csv(self, "task-clock")
        plt.export_stats_to_dataref(self, "task-clock")

        # pgfplot test
        plt.pgfplot(self,
                    self.iterate_args(fixed={"maxsize": 1024}, args=self.results["args"]),
                    "int(perm.threads)",
                    "{mops}",
                    xlabel="Threads",
                    ylabel="MOPS/cpu-second",
                    title="Loop: 1024B",
                    postfix='mops_1024B')

        # create pgfplot legend
        plt.pgfplot_legend(self)


loop = BenchmarkLoop()
