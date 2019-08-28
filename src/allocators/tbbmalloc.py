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

"""tbbmalloc definition for allocbench"""

from src.allocator import Allocator, AllocatorSources

VERSION = "2019_U8"

source = AllocatorSources("tbb",
                         ["git clone https://github.com/intel/tbb.git"],
                         [f"git checkout {VERSION}"],
                         ["git reset --hard"])


class TBBMalloc(Allocator):
    """tbbmalloc allocator"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = source
        kwargs["LD_PRELOAD"] = "{dir}/libtbbmalloc.so"
        kwargs["build_cmds"] = ["cd {srcdir}; make tbbmalloc -j4",
                                "mkdir -p {dir}",
                                'ln -f -s $(find {srcdir} -executable -name "*libtbbmalloc_proxy.so*" | head -1) {dir}/libtbbmalloc.so']

        super().__init__(name, **kwargs)


tbbmalloc = TBBMalloc("tbbmalloc", color="xkcd:green")
