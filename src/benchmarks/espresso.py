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
"""espresso is a single threaded programmable logic array analyzer, described by Zorn and Grunwald
their paper "Empirical Measurements of Six Allocation-intensive C Programs" in 1992.

It is mentioned in:
* Dirk Grunwald et al. - 1992 - CustoMalloc: Efficient Synthesized Memory Allocators
* Dirk Grunwald et al. - 1993 - Improving the Cache Locality of Memory Allocation
* Paul Wilson et al. - 1995 - Dynamic Storage Allocation: A Survey and Critical Review
* Emery Berger et al. - 2000 - Hoard: A Scalable Memory Allocator for Multithreaded Applications
* Emery Berger et al. - 2001 - Composing High-Performance Memory Allocators
* Emery Berger et al. - 2002 - Reconsidering Custom Memory Allocation
* Periklis Akritidis - 2010 - Cling: A Memory Allocator to Mitigate Dangling Pointers
* Daan Leijen et al. - 2019 - Mimalloc: Free List Sharding in Action

The file "largest.espresso" shipped with mimalloc-bench and allocbench generates
a workload with 3367364 allocator calls (malloc: 1659385, free: 1691851, realloc: 16128).
About 87% of all allocations are smaller than 64 Byte, the common cache line size.

Allocator portion of total cycles measured using perf record/report:
malloc 8.64%
free 5.04%

Top 10 allocation sizes 90.73% of all allocations
1. 48 B occurred 615622 times
2. 16 B occurred 533267 times
3. 56 B occurred 235944 times
4. 72 B occurred 27318 times
5. 88 B occurred 23640 times
6. 64 B occurred 22498 times
7. 80 B occurred 17779 times
8. 8 B occurred 16336 times
9. 272 B occurred 14644 times
10. 96 B occurred 13175 times

allocations <= 64   1442648 86.10%
allocations <= 1024 1657509 98.93%
allocations <= 4096 1667112 99.50%

The relevant non functional allocator properties are the raw speed of the
API function as well as memory placement strategies with good data locality.
"""

import os

from src.benchmark import Benchmark
import src.globalvars
import src.plots as plt


class BenchmarkEspresso(Benchmark):
    """Definition of the espresso benchmark for allocbench"""
    def __init__(self):
        name = "espresso"

        self.cmd = "espresso{binary_suffix} {file}"
        self.args = {
            "file": [
                os.path.join(src.globalvars.benchsrcdir, name,
                             "largest.espresso")
            ]
        }

        self.requirements = ["espresso"]
        super().__init__(name)

    def summary(self):
        # Speed
        plt.barplot_single_arg(self,
                               "{task-clock}/1000",
                               ylabel='"cpu-second"',
                               title='"Espresso: runtime"',
                               filepostfix="time")

        # L1 cache misses
        plt.barplot_single_arg(
            self,
            "({L1-dcache-load-misses}/{L1-dcache-loads})*100",
            ylabel='"L1 misses in %"',
            title='"Espresso l1 cache misses"',
            filepostfix="l1misses",
            yerr=False)

        # Memusage
        plt.barplot_single_arg(self,
                               "{VmHWM}",
                               ylabel='"VmHWM in KB"',
                               title='"Espresso VmHWM"',
                               filepostfix="vmhwm")

        plt.write_tex_table(self, [{
            "label": "Runtime [ms]",
            "expression": "{task-clock}",
            "sort": "<"
        }, {
            "label": "Memusage [KB]",
            "expression": "{VmHWM}",
            "sort": "<"
        }],
                            filepostfix="table")

        plt.export_stats_to_dataref(self, "task-clock")

        plt.export_stats_to_dataref(self, "VmHWM")


espresso = BenchmarkEspresso()
