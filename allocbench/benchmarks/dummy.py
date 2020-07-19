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
"""Definition of dummy benchmark

This benchmark does nothing and is only usefull for testing allocbench"""

from allocbench.benchmark import Benchmark


class BenchmarkDummy(Benchmark):
    """Dummy benchmark

    This benchmark does nothing"""
    def __init__(self):
        name = "dummy"

        self.cmd = "true"

        self.args = {}

        super().__init__(name)
