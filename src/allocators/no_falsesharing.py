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
# along with allocbench.
"""Collection containing all no falsesahring patches"""

from src.allocators.tcmalloc import tcmalloc, tcmalloc_nofs
from src.allocators.glibc import glibc, glibc_nofs, glibc_nofs_fancy

allocators = [
    glibc, glibc_nofs, glibc_nofs_fancy, tcmalloc_gperftools,
    tcmalloc_gperftools_nofs
]
