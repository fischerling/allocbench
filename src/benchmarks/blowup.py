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

"""Definition of the blowup micro benchmark"""

from src.benchmark import Benchmark


class BenchmarkBlowup(Benchmark):
    """Blowup micro benchmark

    Check if allocators reuse memory.
    Thread behaviour:
        1. Do many allocations and frees (100MiB is the maximum of live allocations at all times)
        2. Start new thread
        3. Join new thread
    A perfect reusing allocator would need 100MiB RSS and a non reusing allocator
    would need 1GiB.
    """
    def __init__(self):
        name = "blowup"

        self.cmd = "blowup"

        self.requirements = ["blowup"]
        super().__init__(name)

    def summary(self):
        # hack ideal rss in data set
        allocators = self.results["allocators"]
        allocators["Ideal_RSS"] = {"color": "xkcd:gold"}
        self.results["stats"]["Ideal_RSS"] = {}
        for perm in self.iterate_args(args=self.results["args"]):
            self.results["stats"]["Ideal_RSS"][perm] = {"mean": {"VmHWM": 1024 * 100}, 
                                                        "std" : {"VmHWM": 0}}

        self.barplot_single_arg("{VmHWM}",
                                ylabel='"VmHWM in KB"',
                                title='"blowup test"',
                                filepostfix="vmhwm")

        del allocators["Ideal_RSS"]
        del self.results["stats"]["Ideal_RSS"]

        self.export_stats_to_dataref("VmHWM")


blowup = BenchmarkBlowup()
