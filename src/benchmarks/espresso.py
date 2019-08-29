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

"""Definition of the espresso benchmark"""

import os

from src.benchmark import Benchmark
import src.globalvars

class BenchmarkEspresso(Benchmark):
    """TODO"""
    def __init__(self):
        name = "espresso"

        self.cmd = "espresso{binary_suffix} {file}"
        self.args = {"file": [os.path.join(src.globalvars.benchsrcdir, name,
                                           "largest.espresso")]}

        self.requirements = ["espresso"]
        super().__init__(name)

    def summary(self):
        # Speed
        self.barplot_single_arg("{task-clock}/1000",
                                ylabel='"cpu-second"',
                                title='"Espresso: runtime"',
                                filepostfix="time")

        # L1 cache misses
        self.barplot_single_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                                ylabel='"L1 misses in %"',
                                title='"Espresso l1 cache misses"',
                                filepostfix="l1misses",
                                yerr=False)

        # Memusage
        self.barplot_single_arg("{VmHWM}",
                                ylabel='"VmHWM in KB"',
                                title='"Espresso VmHWM"',
                                filepostfix="vmhwm")

        self.export_stats_to_dataref("task-clock")

        self.export_stats_to_dataref("VmHWM")


espresso = BenchmarkEspresso()
