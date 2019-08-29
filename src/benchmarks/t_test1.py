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

"""Definition of the commonly used t-test1 allocator test"""

from src.benchmark import Benchmark


class BenchmarkTTest1(Benchmark):
    """t-test1 unit test

    This benchmark from ptmalloc2 allocates and frees n bins in t concurrent threads.
    """

    def __init__(self):
        name = "t_test1"

        self.cmd = "t-test1 {nthreads} {nthreads} 1000000 {maxsize}"

        self.args = {"maxsize":  [2 ** x for x in range(6, 18)],
                     "nthreads": Benchmark.scale_threads_for_cpus(2)}

        self.requirements = ["t-test1"]
        super().__init__(name)

    def summary(self):
        # mops / per second
        yval = "perm.nthreads / ({task-clock}/1000)"
        # Speed
        self.plot_fixed_arg(yval,
                            ylabel='"Mops / CPU second"',
                            title='"T-Ttest1: " + arg + " " + str(arg_value)',
                            filepostfix="time",
                            autoticks=False)

        scale = list(self.results["allocators"].keys())[0]
        self.plot_fixed_arg(yval,
                            ylabel='"Mops / CPU second scaled at {}"'.format(scale),
                            title='"T-Test1: " + arg + " " + str(arg_value) + " normalized {}"'.format(scale),
                            filepostfix="time.norm",
                            scale=scale,
                            autoticks=False)

        # L1 cache misses
        self.plot_fixed_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                            ylabel='"L1 misses in %"',
                            title='"T-Test1 l1 cache misses: " + arg + " " + str(arg_value)',
                            filepostfix="l1misses",
                            autoticks=False)

        # Speed Matrix
        self.write_best_doublearg_tex_table(yval,
                                            filepostfix="memusage.matrix")

        self.export_stats_to_csv("task-clock")


t_test1 = BenchmarkTTest1()
