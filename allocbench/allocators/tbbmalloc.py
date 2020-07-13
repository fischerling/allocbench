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
# along with allocbench.
"""tbbmalloc definition for allocbench"""

from allocbench.allocator import Allocator
from allocbench.artifact import GitArtifact


class TBBMalloc(Allocator):
    """tbbmalloc allocator"""

    sources = GitArtifact("tbb", "https://github.com/intel/tbb.git")

    def __init__(self, name, **kwargs):
        self.ld_preload = "{dir}/libtbbmalloc.so"
        self.build_cmds = [
            "cd {srcdir}; make tbbmalloc -j4", "mkdir -p {dir}",
            ('ln -f -s $(find {srcdir} -executable -name "*libtbbmalloc_proxy.so*"'
             ' | head -1) {dir}/libtbbmalloc.so')
        ]

        super().__init__(name, **kwargs)


# pylint: disable=invalid-name
tbbmalloc = TBBMalloc("tbbmalloc", color="xkcd:green", version="2019_U8")
