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

"""SuperMalloc definition for allocbench"""

from src.allocator import Allocator
from src.artifact import GitArtifact

class SuperMalloc(Allocator):
    """SuperMalloc allocator"""

    sources = GitArtifact("SuperMalloc", "https://github.com/kuszmaul/SuperMalloc")

    def __init__(self, name, **kwargs):
        self.LD_PRELOAD = "{dir}/libsupermalloc.so"
        self.build_cmds = ["cd {srcdir}/release; make",
                           "mkdir -p {dir}",
                           "ln -f -s {srcdir}/release/lib/libsupermalloc.so {dir}/libsupermalloc.so"]
        self.patches = ["{patchdir}/remove_faulty_aligned_alloc_test.patch"]

        super().__init__(name, **kwargs)


supermalloc = SuperMalloc("SuperMalloc", color="xkcd:lime",
                          version="709663fb81ba091b0a78058869a644a272f4163d")
