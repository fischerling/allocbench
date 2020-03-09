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
"""Collection containing all allocators used in Florian's BA thesis"""

from src.allocators.glibc import glibc, glibc_notc
from src.allocators.tcmalloc import tcmalloc
from src.allocators.jemalloc import jemalloc
from src.allocators.hoard import hoard

allocators = [glibc, glibc_notc, tcmalloc, jemalloc, hoard]
