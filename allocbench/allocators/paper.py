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
"""Collection containing  all available allocators"""

from allocbench.allocators.glibc import glibc
from allocbench.allocators.tcmalloc import tcmalloc, tcmalloc_align, tcmalloc_gperftools, tcmalloc_gperftools_align
from allocbench.allocators.jemalloc import jemalloc
from allocbench.allocators.llalloc import llalloc
from allocbench.allocators.mimalloc import mimalloc
from allocbench.allocators.bumpptr import bumpptr
from allocbench.allocators.speedymalloc import speedymalloc

# pylint: disable=invalid-name
allocators = [
    glibc, tcmalloc, tcmalloc_align, tcmalloc_gperftools,
    tcmalloc_gperftools_align, jemalloc, llalloc, mimalloc, bumpptr,
    speedymalloc
]
