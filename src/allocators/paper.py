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

"""Collection containing  all available allocators"""

from src.allocators.glibc import glibc
from src.allocators.tcmalloc import tcmalloc, tcmalloc_align, tcmalloc_gperftools, tcmalloc_gperftools_align
from src.allocators.jemalloc import jemalloc
from src.allocators.scalloc import scalloc
from src.allocators.llalloc import llalloc
from src.allocators.tbbmalloc import tbbmalloc
from src.allocators.mimalloc import mimalloc
from src.allocators.bumpptr import bumpptr
from src.allocators.speedymalloc import speedymalloc


allocators = [glibc, tcmalloc, tcmalloc_align, tcmalloc_gperftools, tcmalloc_gperftools_align, jemalloc, llalloc, mimalloc, bumpptr, speedymalloc]
