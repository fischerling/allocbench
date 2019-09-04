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

from src.allocator import Allocator, AllocatorSources

import src.allocator

VERSION = "709663fb81ba091b0a78058869a644a272f4163d"

sources = AllocatorSources("SuperMalloc",
            retrieve_cmds=["git clone https://github.com/kuszmaul/SuperMalloc"],
            prepare_cmds=[f"git checkout {VERSION}"],
            reset_cmds=["git reset --hard"])


class SuperMalloc(Allocator):
    """SuperMalloc allocator"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{srcdir}/release/lib/libsupermalloc.so"
        kwargs["build_cmds"] = ["cd {srcdir}/release; make",
                                "mkdir -p {dir}"]
        kwargs["patches"] = ["{patchdir}/remove_faulty_aligned_alloc_test.patch"]

        super().__init__(name, **kwargs)


supermalloc = SuperMalloc("SuperMalloc", color="xkcd:lime")
