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

VERBOSITY: Verbosity level -1: quiet, 0: status, 1: info, 2: stdout of subcommands, 3: debug info
ALLOCATORS: Dict holding the allocators to compare
BENCHMARKS: List of available benchmarks

ALLOCBENCHDIR: Root directory of allocbench
SRCDIR: Directory of allocbench sources
BENCHSRCDIR: Source directory for all benchmarks
ALLOCSRCDIR: Source directory for all benchmarks
BUILDDIR: Path of the build directory
ALLOCBUILDDIR: Path of the allocators build directory
RESDIR: Directory were the benchmark results are stored
"""

import inspect
import os


VERBOSITY = 0

ALLOCATORS = {}

# /.../allocbench/allocbench
SRCDIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# /.../allocbench/allocbench/benchmarks
BENCHSRCDIR = os.path.join(SRCDIR, "benchmarks")

# /.../allocbench/allocbench/allocators
ALLOCSRCDIR = os.path.join(SRCDIR, "allocators")

# /.../allocbench
ALLOCBENCHDIR = os.path.dirname(SRCDIR)

# /.../allocbench/build
BUILDDIR = os.path.join(ALLOCBENCHDIR, "build")

# /.../allocbench/build/allocators
ALLOCBUILDDIR = os.path.join(BUILDDIR, "allocators")

RESDIR = None

BENCHMARKS = [e[:-3] for e in os.listdir(os.path.join(ALLOCBENCHDIR, BENCHSRCDIR))
              if e[-3:] == ".py" and e != "__init__.py"]

SUMMARY_FILE_EXT = "svg"

LATEX_CUSTOM_PREAMBLE = ""
