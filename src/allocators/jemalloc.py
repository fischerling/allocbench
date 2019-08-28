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

"""jemalloc definition for allocbench"""

from src.allocator import Allocator, AllocatorSources

VERSION = "5.1.0"

sources = AllocatorSources("jemalloc",
            retrieve_cmds=["git clone https://github.com/jemalloc/jemalloc.git"],
            prepare_cmds=[f"git checkout {VERSION}", "./autogen.sh"])


class Jemalloc(Allocator):
    """jemalloc allocator"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{srcdir}/lib/libjemalloc.so"
        kwargs["build_cmds"] = ["cd {srcdir}; ./configure --prefix={dir}",
                                "cd {srcdir}; make -j4",
                                "mkdir -p {dir}"]

        super().__init__(name, **kwargs)


jemalloc = Jemalloc("jemalloc", color="xkcd:yellow")
