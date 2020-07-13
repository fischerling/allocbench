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
"""TCMalloc definition for allocbench"""

from allocbench.allocator import Allocator
from allocbench.artifact import GitArtifact
from allocbench.directories import get_allocbench_allocator_build_dir


class TCMalloc(Allocator):
    """TCMalloc allocator"""

    sources = GitArtifact("tcmalloc", "https://github.com/google/tcmalloc.git")

    def __init__(self, name, **kwargs):

        self.ld_preload = "{dir}/libtcmalloc.so"
        self.patches = ["{patchdir}/tcmalloc_bazel_build_so.patch"]
        self.build_cmds = [
            "cd {srcdir}; bazel build tcmalloc/tcmalloc.so --compilation_mode opt",
            "mkdir -p {dir}",
            "cp -f {srcdir}/bazel-bin/tcmalloc/tcmalloc.so {dir}/libtcmalloc.so"
        ]

        super().__init__(name, **kwargs)


# pylint: disable=invalid-name
tcmalloc = TCMalloc("TCMalloc",
                    color="xkcd:blue",
                    version="1676100265bd189df6b5513feac15f102542367e")

tcmalloc_align = TCMalloc("TCMalloc-Aligned",
                          version="1676100265bd189df6b5513feac15f102542367e",
                          color="xkcd:light blue")

align_to_cl_location = f"{get_allocbench_allocator_build_dir()}/align_to_cl.so"

tcmalloc_align.ld_preload = f"{align_to_cl_location} {tcmalloc_align.ld_preload}"
# pylint: enable=invalid-name


class TCMallocGperftools(Allocator):
    """gperftools TCMalloc allocator"""

    sources = GitArtifact("gperftools",
                          "https://github.com/gperftools/gperftools.git")

    def __init__(self, name, **kwargs):

        self.ld_preload = "{dir}/lib/libtcmalloc.so"
        self.prepare_cmds = ["./autogen.sh"]
        self.build_cmds = [
            "cd {srcdir}; ./configure --prefix={dir}",
            "cd {srcdir}; make install -j4"
        ]

        super().__init__(name, **kwargs)


# pylint: disable=invalid-name
tcmalloc_gperftools = TCMallocGperftools("TCMalloc-gperftools",
                                         color="xkcd:dark blue",
                                         version="gperftools-2.7")

tcmalloc_gperftools_nofs = TCMallocGperftools(
    "TCMalloc-Gperftools-NoFalsesharing",
    patches=["{patchdir}/tcmalloc_2.7_no_active_falsesharing.patch"],
    version="gperftools-2.7",
    color="xkcd:navy")

tcmalloc_gperftools_align = TCMallocGperftools("TCMalloc-Gperftools-Aligned",
                                               version="gperftools-2.7",
                                               color="xkcd:navy blue")

tcmalloc_gperftools_align.ld_preload = (
    f"{align_to_cl_location} {tcmalloc_gperftools_align.ld_preload}")

tcmalloc_gperftools_cacheline_exclusive = TCMallocGperftools(
    "TCMalloc-Gperftools-Cacheline-Exclusive",
    patches=["{patchdir}/tcmalloc_2.7_cacheline_exclusive.patch"],
    version="gperftools-2.7",
    color="xkcd:royal blue")
