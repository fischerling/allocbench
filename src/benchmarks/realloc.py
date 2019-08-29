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

"""Definition of the realloc micro benchmark"""

from src.benchmark import Benchmark


class BenchmarkRealloc(Benchmark):
    """Realloc micro benchmark

    realloc a pointer 100 times
    """
    def __init__(self):
        name = "realloc"

        self.cmd = "realloc"

        self.requirements = ["realloc"]
        super().__init__(name)

    def summary(self):
        self.barplot_single_arg("{task-clock}",
                                ylabel='"task-clock in ms"',
                                title='"realloc micro benchmark"')

        self.export_stats_to_csv("task-clock")
        self.export_stats_to_dataref("task-clock")


realloc = BenchmarkRealloc()
