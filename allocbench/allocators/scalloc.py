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
"""Scalloc definition for allocbench"""

from allocbench.allocator import Allocator
from allocbench.artifact import GitArtifact


class Scalloc(Allocator):
    """Scalloc allocator"""

    sources = GitArtifact("scalloc",
                          "https://github.com/cksystemsgroup/scalloc")

    def __init__(self, name, **kwargs):
        self.prepare_cmds = [
            "tools/make_deps.sh", "build/gyp/gyp --depth=. scalloc.gyp"
        ]

        self.build_cmds = [
            "cd {srcdir}; BUILDTYPE=Release make", "mkdir -p {dir}"
        ]

        self.ld_preload = "{srcdir}/out/Release/lib.target/libscalloc.so"

        self.patches = ["{patchdir}/scalloc_fix_log.patch"]

        super().__init__(name, **kwargs)

    def build(self):
        with open("/proc/sys/vm/overcommit_memory", "r") as overcommit_memory_file:
            if overcommit_memory_file.read()[0] != "1":
                raise AssertionError("""\
vm.overcommit_memory not set
Scalloc needs permission to overcommit_memory.
sysctl vm.overcommit_memory=1
""")
        return super().build()


# pylint: disable=invalid-name
scalloc = Scalloc("scalloc", color="xkcd:magenta", version="v1.0.0")
