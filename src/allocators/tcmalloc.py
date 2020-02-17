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

from src.allocator import Allocator
from src.artifact import GitArtifact


class TCMalloc(Allocator):
    """TCMalloc allocator"""

    sources = GitArtifact("tcmalloc", "https://github.com/google/tcmalloc.git")

    def __init__(self, name, **kwargs):

        self.LD_PRELOAD = "{dir}/libtcmalloc.so"
        self.patches = ["{patchdir}/tcmalloc_bazel_build_so.patch"]
        self.build_cmds = [
            "cd {srcdir}; bazel build tcmalloc/tcmalloc.so", "mkdir {dir}",
            "cp {srcdir}/bazel-bin/tcmalloc/tcmalloc.so {dir}/libtcmalloc.so"
        ]

        super().__init__(name, **kwargs)


tcmalloc = TCMalloc("TCMalloc",
                    color="xkcd:blue",
                    version="1676100265bd189df6b5513feac15f102542367e")


class TCMallocGperftools(Allocator):
    """gperftools TCMalloc allocator"""

    sources = GitArtifact("gperftools",
                          "https://github.com/gperftools/gperftools.git")

    def __init__(self, name, **kwargs):

        self.LD_PRELOAD = "{dir}/lib/libtcmalloc.so"
        self.prepare_cmds = ["./autogen.sh"]
        self.build_cmds = [
            "cd {srcdir}; ./configure --prefix={dir}",
            "cd {srcdir}; make install -j4"
        ]

        super().__init__(name, **kwargs)


tcmalloc_gperftools = TCMallocGperftools("TCMalloc-gperftools",
                                         color="xkcd:blue",
                                         version="gperftools-2.7")

tcmalloc_gperftools_nofs = TCMallocGperftools(
    "TCMalloc-gperftools-NoFalsesharing",
    patches=["{patchdir}/tcmalloc_2.7_no_active_falsesharing.patch"],
    version="gperftools-2.7",
    color="xkcd:navy")
