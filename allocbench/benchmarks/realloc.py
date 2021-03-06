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
"""Definition of the realloc micro benchmark"""

from allocbench.benchmark import Benchmark


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
        """Create plot showing the needed runtime"""
        import allocbench.plots as plt  # pylint: disable=import-outside-toplevel

        plt.plot(self,
                 "{task-clock}",
                 plot_type='bar',
                 fig_options={
                     'ylabel': 'task-clock in ms',
                     'title': 'realloc micro benchmark',
                 },
                 file_postfix="time")

        plt.export_stats_to_csv(self, "task-clock")
        plt.export_stats_to_dataref(self, "task-clock")
