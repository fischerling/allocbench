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

import src.allocators.glibcs
from src.allocators.tcmalloc import tcmalloc, tcmalloc_nofs
from src.allocators.jemalloc import jemalloc
from src.allocators.hoard import hoard
from src.allocators.mesh import mesh
from src.allocators.scalloc import scalloc
from src.allocators.supermalloc import supermalloc
from src.allocators.llalloc import llalloc
from src.allocators.tbbmalloc import tbbmalloc
from src.allocators.mimalloc import mimalloc
from src.allocators.snmalloc import snmalloc


allocators = [*src.allocators.glibcs.allocators, tcmalloc, tcmalloc_nofs,
              jemalloc, hoard, mesh, supermalloc, scalloc, llalloc, tbbmalloc,
              mimalloc, snmalloc]
