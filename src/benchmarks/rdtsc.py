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
See: https://developers.redhat.com/blog/2016/03/11/practical-micro-benchmarking-with-ltrace-and-sched/
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from src.benchmark import Benchmark
import src.globalvars
import src.plots


class BenchmarkRdtsc(Benchmark):
    """rdtsc micro benchmark

    This benchmark allocates and frees n blocks in t concurrent threads measuring the used cycles.
    """
    def __init__(self):
        name = "rdtsc"

        self.cmd = "rdtsc {mode} 100000 64 {threads}"
        self.measure_cmd = ""

        self.args = {"threads": [1],
                     "mode": ['fresh', 'cached']}

        self.requirements = ["rdtsc"]
        super().__init__(name)

    def process_output(self, result, stdout, stderr, alloc, perm):
        all_cycles = []
        for line in stdout.splitlines():
            all_cycles.append(int(line.split()[1]))
        result["cycles"] = all_cycles

    def summary(self):
        for perm in self.iterate_args(args=self.results['args']):
            label = f'rdtsc_{perm}_cycles'
            fig = plt.figure(label)
            src.plots.FIGURES[label] = fig

            axes = plt.axes()
            axes.set_ylim([50, 800])

            for alloc in self.results['allocators']:
                d = np.sort(self.results[alloc][perm][0]['cycles'])
                plt.plot(d, label=alloc, color=src.plots._get_alloc_color(self, alloc))

            fig.savefig(f'{label}.{src.globalvars.summary_file_ext}')
            plt.legend()
            plt.title(str(perm))
            plt.show()


rdtsc = BenchmarkRdtsc()
