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

"""Snmalloc definition for allocbench"""

from src.allocator import Allocator
from src.artifact import GitArtifact


class Snmalloc(Allocator):
    """snmalloc allocator"""

    sources = GitArtifact("snmalloc", "https://github.com/microsoft/snmalloc")

    def __init__(self, name, **kwargs):
        self.LD_PRELOAD = "{dir}/libsnmallocshim.so"
        self.build_cmds = ["mkdir -p {dir}",
                           "cd {dir}; cmake -G Ninja {srcdir} -DCMAKE_BUILD_TYPE=Release",
                           "cd {dir}; ninja"]
        self.requirements = ["cmake", "ninja", "clang"]

        super().__init__(name, **kwargs)


snmalloc = Snmalloc("snmalloc", version="0.2")
