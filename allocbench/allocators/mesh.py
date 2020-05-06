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
"""Mesh definition for allocbench"""

from allocbench.allocator import Allocator
from allocbench.artifact import GitArtifact


class Mesh(Allocator):
    """Mesh allocator"""

    sources = GitArtifact("Mesh", "https://github.com/plasma-umass/Mesh")

    def __init__(self, name, **kwargs):
        self.ld_preload = "{dir}/libmesh.so"
        self.build_cmds = [
            "cd {srcdir}; ./configure", "cd {srcdir}; make -j 4",
            "mkdir -p {dir}", "ln -f -s {srcdir}/libmesh.so {dir}/libmesh.so"
        ]

        super().__init__(name, **kwargs)


# pylint: disable=invalid-name
mesh = Mesh("Mesh",
            version="4a1012cee990cb98cc1ea0294a836f467b29be02",
            color="xkcd:mint")
