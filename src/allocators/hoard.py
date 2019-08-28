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

"""Hoard allocator definition for allocbench"""

from src.allocator import Allocator, AllocatorSources


sources = AllocatorSources("Hoard",
            retrieve_cmds=["git clone https://github.com/emeryberger/Hoard.git"],
            reset_cmds=["git reset --hard"])


class Hoard(Allocator):
    """Hoard allocator"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{dir}/libhoard.so"
        kwargs["build_cmds"] = ["cd {srcdir}/src; make",
                                "mkdir -p {dir}",
                                "ln -f -s {srcdir}/src/libhoard.so {dir}/libhoard.so"]
        kwargs["requirements"] = ["clang"]

        super().__init__(name, **kwargs)


hoard = Hoard("Hoard", color="xkcd:brown")
