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
"""

from typing import Dict

VERBOSITY = 0

ALLOCATORS = {}

SUMMARY_FILE_EXT = "svg"

LATEX_CUSTOM_PREAMBLE = ""
