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
# along with allocbench.  If not, see <http://www.gnu.org/licenses/>.
"""Speedymalloc

Speedymalloc is a cached bump pointer allocator.
A bump pointer allocator makes the biggest possible tradeoff between speed and
memory in speeds favor. Memory is mmapped per thread and never freed.
"""

from src.artifact import GitArtifact
from src.allocator import Allocator

VERSION = "33d05bda26fbb9cf6351b604b292af664e5f51b4"


class Speedymalloc(Allocator):
    """Speedymalloc definition for allocbench"""

    sources = GitArtifact("speedymalloc",
                          "https://gitlab.cs.fau.de/flow/speedymalloc.git")

    def __init__(self, name, **kwargs):

        configuration = ""
        for option, value in kwargs.get("options", {}).items():
            configuration += f"-D{option}={value} "

        self.build_cmds = [
            f"meson {{srcdir}} {{dir}} {configuration}", "ninja -C {dir}"
        ]

        self.LD_PRELOAD = "{dir}/libspeedymalloc.so"
        super().__init__(name, **kwargs)


speedymalloc = Speedymalloc("speedymalloc", version=VERSION)

speedymalloc_no_madv_free = Speedymalloc("speedymalloc_no_madv_free",
                                         options={"madvise_free": "false"},
                                         version=VERSION)

speedymalloc_no_madv_willneed = Speedymalloc(
    "speedymalloc_no_madv_willneed",
    options={"madvise_willneed": "false"},
    version=VERSION)

speedymalloc_4095_sc_32 = Speedymalloc("speedymalloc_4095_sc_32",
                                       options={
                                           "cache_bins": 4095,
                                           "cache_bin_seperation": 32
                                       },
                                       version=VERSION)

speedymalloc_4095_sc_128 = Speedymalloc("speedymalloc_4095_sc_128",
                                       options={
                                           "cache_bins": 4095,
                                           "cache_bin_seperation": 128
                                       },
                                       version=VERSION)

speedymalloc_only_glab = Speedymalloc(
    "speedymalloc_no_glab",
    options={"max_local_allocation_buffer_size": 0},
    version=VERSION)

speedymalloc_no_glab = Speedymalloc(
    "speedymalloc_no_glab",
    options={"max_local_allocation_buffer_size": -1},
    version=VERSION)

# speedymalloc_rseq = Speedymalloc(
    # "speedymalloc_rseq",
    # version="e1549fa2a2833deba0ba53504a6c67ee31a0e42a")
