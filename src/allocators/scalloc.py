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

"""Scalloc definition for allocbench"""

from src.allocator import Allocator, AllocatorSources
from src.util import print_error


VERSION = "v1.0.0"

SCALLOC_SRC = AllocatorSources("scalloc",
                      retrieve_cmds=["git clone https://github.com/cksystemsgroup/scalloc"],
                      prepare_cmds=[f"git checkout {VERSION}",
                                    "cd {srcdir}; tools/make_deps.sh",
                                    "cd {srcdir}; build/gyp/gyp --depth=. scalloc.gyp"],
                      reset_cmds=["git reset --hard"])


class Scalloc(Allocator):
    """Scalloc allocator"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = SCALLOC_SRC

        kwargs["build_cmds"] = ["cd {srcdir}; BUILDTYPE=Release make",
                                "mkdir -p {dir}"]

        kwargs["LD_PRELOAD"] = "{srcdir}/out/Release/lib.target/libscalloc.so"

        kwargs["patches"] = ["{patchdir}/scalloc_fix_log.patch"]

        super().__init__(name, **kwargs)

    def build(self):
        with open("/proc/sys/vm/overcommit_memory", "r") as f:
            if f.read()[0] != "1":
                raise AssertionError("""\
vm.overcommit_memory not set
Scalloc needs permission to overcommit_memory.
sysctl vm.overcommit_memory=1
""")
        return super().build()


scalloc = Scalloc("scalloc", color="xkcd:magenta")
