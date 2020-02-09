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

"""chattymalloc allocator

This shared library is no functional allocator. It is used to retrieve a trace
of the allocator usage of the executed programm. It overrides the malloc API
and writes each call and its result to an output file.
See src/chattymalloc.c and chattyparser.py for its implementation and usage.
"""

import os
from src.allocator import Allocator, BUILDDIR

chattymalloc = Allocator("chattymalloc",
                         LD_PRELOAD=os.path.join(BUILDDIR, "chattymalloc.so"),
                         cmd_prefix="env CHATTYMALLOC_FILE={{result_dir}}/{{perm}}.trace")
