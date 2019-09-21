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

"""Global variables for allocbench

facts: Dict holding facts about the current benchmark run
verbosity: Verbosity level -1: quiet, 0: status, 1: info, 2: stdout of subcommands, 3: debug info
allocators: Dict holding the allocators to compare
benchmarks: List of available benchmarks

allocbenchdir: Root directory of allocbench
srcdir: Directory of allocbench sources
benchsrcdir: Source directory for all benchmarks
allocsrcdir: Source directory for all benchmarks
builddir: Path of the build directory
allocbuilddir: Path of the allocators build directory
resdir: Directory were the benchmark results are stored
"""

import inspect
import os


facts = {}

verbosity = 0

allocators = {}

# allocbench/src/
srcdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# allocbench/src/benchmarks
benchsrcdir = os.path.join(srcdir, "benchmarks")

# allocbench/src/allocators
allocsrcdir = os.path.join(srcdir, "allocators")

# allocbench
allocbenchdir = os.path.dirname(srcdir)

# allocbench/build
builddir = os.path.join(allocbenchdir, "build")

# allocbench/build/allocators
allocbuilddir = os.path.join(builddir, "allocators")

resdir = None

benchmarks = [e[:-3] for e in os.listdir(os.path.join(allocbenchdir, benchsrcdir))
              if e[-3:] == ".py" and e != "__init__.py"]
