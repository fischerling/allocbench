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

"""TCMalloc definition for allocbench"""

from src.allocator import Allocator, BUILDDIR
from src.artifact import GitArtifact


class TCMalloc(Allocator):
    """TCMalloc allocator"""

    sources = GitArtifact("tcmalloc", "https://github.com/gperftools/gperftools.git")

    def __init__(self, name, **kwargs):

        self.LD_PRELOAD = "{dir}/lib/libtcmalloc.so"
        self.prepare_cmds = ["./autogen.sh"]
        self.build_cmds = ["cd {srcdir}; ./configure --prefix={dir}",
                           "cd {srcdir}; make install -j4"]

        super().__init__(name, **kwargs)


tcmalloc = TCMalloc("TCMalloc", color="xkcd:blue", version="gperftools-2.7")

tcmalloc_nofs = TCMalloc("TCMalloc-NoFalsesharing",
                         patches=["{patchdir}/tcmalloc_2.7_no_active_falsesharing.patch"],
                         version="gperftools-2.7",
                         color="xkcd:navy")

tcmalloc_align = TCMalloc("TCMalloc-Aligned",
                         version="gperftools-2.7",
                         color="xkcd:navy")

tcmalloc_align.LD_PRELOAD = f"{BUILDDIR}/align_to_cl.so {tcmalloc_align.LD_PRELOAD}"
