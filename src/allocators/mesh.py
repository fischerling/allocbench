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

"""Mesh definition for allocbench"""

from src.allocator import Allocator, AllocatorSources

sources = AllocatorSources("Mesh",
            retrieve_cmds=["git clone https://github.com/plasma-umass/Mesh"],
            reset_cmds=["git reset --hard"])

# sources = src.allocator.GitAllocatorSources("Mesh",
#             "https://github.com/plasma-umass/Mesh",
#             "adsf0982345")


class Mesh(Allocator):
    """Mesh allocator"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{srcdir}/libmesh.so"
        kwargs["build_cmds"] = ["cd {srcdir}; git submodule update --init",
                                "cd {srcdir}; ./configure",
                                "cd {srcdir}; make -j 4",
                                "mkdir -p {dir}"]

        super().__init__(name, **kwargs)


mesh = Mesh("Mesh", color="xkcd:mint")
