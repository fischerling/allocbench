# Copyright 2020 Florian Fischer <florian.fl.fischer@fau.de>
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
"""Definition of the rdtsc micro benchmark

This benchmark measures the clock cycles used by malloc.
It tries to spread the spawned thread on all cores exept the first one.
Inspired by DJ Delorie's blog post:
https://developers.redhat.com/blog/2016/03/11/practical-micro-benchmarking-with-ltrace-and-sched/
"""

import numpy as np

from allocbench.benchmark import Benchmark


class BenchmarkRdtsc(Benchmark):
    """rdtsc micro benchmark

    This benchmark allocates and frees n blocks in t concurrent threads measuring the used cycles.
    """
    def __init__(self):
        name = "rdtsc"

        self.cmd = "rdtsc {mode} 100000 64 {threads}"
        self.measure_cmd = ""

        self.args = {"threads": [1], "mode": ['fresh', 'cached']}

        self.requirements = ["rdtsc"]
        super().__init__(name)

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):  # pylint: disable=too-many-arguments, unused-argument
        """Collect cycles needed during all iterations and calcullate mean"""
        all_cycles = []
        for line in stdout.splitlines():
            all_cycles.append(int(line.split()[1]))
        result["all_cycles"] = all_cycles
        result["cycles"] = np.mean(all_cycles)

    def summary(self):
        """Create plots showing needed cycles"""
        import matplotlib.pyplot as plt  # pylint: disable=import-outside-toplevel
        import allocbench.plots  # pylint: disable=import-outside-toplevel
        from allocbench.plots import SUMMARY_FILE_EXT  # pylint: disable=import-outside-toplevel

        for perm in self.iterate_args(args=self.results['args']):
            label = f'rdtsc_{perm}_cycles'
            fig = plt.figure(label)
            allocbench.plots.FIGURES[label] = fig

            axes = plt.axes()
            axes.set_ylim([50, 800])

            for i, alloc in enumerate(self.results['allocators']):
                data = np.sort(self.results[alloc][perm][0]['all_cycles'])
                color = allocbench.plots.get_alloc_color(self, alloc)
                color = f"C{i}"
                plt.plot(data, label=alloc, color=color)

            plt.legend()
            plt.title(str(perm))
            fig.savefig(f'{label}.{SUMMARY_FILE_EXT}')

        allocbench.plots.export_stats_to_csv(self, "cycles")
