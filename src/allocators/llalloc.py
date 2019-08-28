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

"""Lockless allocator definition for allocbench"""

from src.allocator import Allocator, AllocatorSources


LLALLOC_SOURCE = AllocatorSources("lockless_allocator",
                      retrieve_cmds=["wget https://locklessinc.com/downloads/lockless_allocator_src.tgz",
                                     "tar xf lockless_allocator_src.tgz"],
                      prepare_cmds=[],
                      reset_cmds=[])


class LocklessAllocator(Allocator):
    """Lockless allocator"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = LLALLOC_SOURCE

        kwargs["build_cmds"] = ["cd {srcdir}; make", "mkdir -p {dir}"]

        kwargs["LD_PRELOAD"] = "{srcdir}/libllalloc.so.1.3"

        super().__init__(name, **kwargs)


llalloc = LocklessAllocator("llalloc", color="purple")

