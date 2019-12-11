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
"""cfrac is a single threaded implementation of the continued fraction factorization algorithm,
described by Zorn and Grunwald in their paper "Empirical Measurements of Six Allocation-intensive C Programs" in 1992.

It is mentioned in:
* Dirk Grunwald et al. - 1992 - CustoMalloc: Efficient Synthesized Memory Allocators
* Emery Berger et al. - 2001 - Composing High-Performance Memory Allocators
* Emery Berger et al. - 2002 - Reconsidering Custom Memory Allocation
* Jason Evans - 2006 - A Scalable Concurrent malloc(3) Implementation for FreeBSD
* Daan Leijen et al. - 2019 - Mimalloc: Free List Sharding in Action

It uses many small short-lived allocations.
Factorizing 175451865205073170563711388363274837927895 results in
43044885 allocator calls (malloc: 21522444, free: 21522441).

Allocator portion of total cycles measured using perf record/report:
malloc 4.33%
free 7.74%

Top 10 allocation sizes 99.95% of all allocations
1. 18 B occurred 8172763 times
2. 28 B occurred 3781894 times
3. 10 B occurred 2989673 times
4. 26 B occurred 2566937 times
5. 20 B occurred 2420915 times
6. 16 B occurred 1168569 times
7. 12 B occurred 203177 times
8. 14 B occurred 170914 times
9. 30 B occurred 21149 times
10. 44 B occurred 15922 times

allocations <= 64 21522432   100.00%
allocations <= 1024 21522436 100.00%
allocations <= 4096 21522443 100.00%

Histogram of sizes:
0     -    15 3363764  15.63% *******
16    -    31 18132778 84.25% ******************************************
32    -    47 25888    0.12%
...

The relevant non functional allocator properties are the raw speed of the
API function as well as memory placement strategies with good data locality.
"""

from src.benchmark import Benchmark


class BenchmarkCfrac(Benchmark):
    """Definition of the cfrac benchmark"""
    def __init__(self):
        name = "cfrac"

        self.cmd = "cfrac{binary_suffix} {num}"

        self.args = {"num": [175451865205073170563711388363274837927895]}

        self.requirements = ["cfrac"]
        super().__init__(name)

    def summary(self):
        # Speed
        self.barplot_single_arg("{task-clock}/1000",
                                ylabel='"cpu-second"',
                                title='"Cfrac: runtime"',
                                filepostfix="time")

        # L1 cache misses
        self.barplot_single_arg(
            "({L1-dcache-load-misses}/{L1-dcache-loads})*100",
            ylabel='"L1 misses in %"',
            title='"Cfrac l1 cache misses"',
            filepostfix="l1misses",
            yerr=False)

        # Memusage
        self.barplot_single_arg("{VmHWM}",
                                ylabel='"VmHWM in KB"',
                                title='"Cfrac VmHWM"',
                                filepostfix="vmhwm")

        self.write_tex_table([{
            "label": "Runtime [ms]",
            "expression": "{task-clock}",
            "sort": "<"
        }, {
            "label": "Memusage [KB]",
            "expression": "{VmHWM}",
            "sort": "<"
        }],
                             filepostfix="table")

        self.export_stats_to_dataref("task-clock")

        self.export_stats_to_dataref("VmHWM")


cfrac = BenchmarkCfrac()
