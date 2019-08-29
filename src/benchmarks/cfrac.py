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

""" Definition of the cfrac benchmark"""

from src.benchmark import Benchmark

class BenchmarkCfrac(Benchmark):
    """TODO"""
    def __init__(self):
        name = "cfrac"

        self.cmd = "cfrac{binary_suffix} {num}"

        self.args = {"num": [175451865205073170563711388363274837927895]}

        self.requirements = ["cfrac"]
        super().__init__("cfrac")

    def summary(self):
        # Speed
        self.barplot_single_arg("{task-clock}/1000",
                                ylabel='"cpu-second"',
                                title='"Cfrac: runtime"',
                                filepostfix="time")

        # L1 cache misses
        self.barplot_single_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                                ylabel='"L1 misses in %"',
                                title='"Cfrac l1 cache misses"',
                                filepostfix="l1misses",
                                yerr=False)

        # Memusage
        self.barplot_single_arg("{VmHWM}",
                                ylabel='"VmHWM in KB"',
                                title='"Cfrac VmHWM"',
                                filepostfix="vmhwm")

        self.export_stats_to_dataref("task-clock")

        self.export_stats_to_dataref("VmHWM")


cfrac = BenchmarkCfrac()
