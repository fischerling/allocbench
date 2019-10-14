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

"""rpmalloc definition for allocbench"""

from src.allocator import Allocator
from src.artifact import GitArtifact


class Rpmalloc(Allocator):
    """rpmalloc allocator"""

    sources = GitArtifact("rpmalloc", "https://github.com/mjansson/rpmalloc")

    def __init__(self, name, **kwargs):

        self.LD_PRELOAD = "{dir}/librpmalloc.so"
        self.build_cmds = ["cd {srcdir}; ./configure.py",
                           "cd {srcdir}; ninja",
                           "mkdir -p {dir}",
                           'ln -f -s $(find {srcdir}/bin -path "*release*librpmalloc.so") {dir}/librpmalloc.so']

        super().__init__(name, **kwargs)


rpmalloc = Rpmalloc("rpmalloc", color="xkcd:chestnut", version="1.4.0")
