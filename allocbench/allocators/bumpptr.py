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
"""Bumpptr allocator

The bumpptr allocator makes the biggest possible tradeoff between speed and
memory in speeds favor. Memory is mmapped per thread and never freed.
See allocbench/bumpptr.c for the actual implementation.
"""

import os
from allocbench.allocator import Allocator, BUILDDIR

# pylint: disable=invalid-name
bumpptr = Allocator("bumpptr",
                    ld_preload=os.path.join(BUILDDIR, "bumpptr_alloc.so"),
                    color="xkcd:black")
