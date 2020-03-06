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
# along with allocbench.  If not, see <http://www.gnu.org/licenses/>.

"""Bumpptr allocator

The bumpptr allocator makes the biggest possible tradeoff between speed and
memory in speeds favor. Memory is mmapped per thread and never freed.
See src/bumpptr.c for the actual implementation.
"""

from src.artifact import GitArtifact
from src.allocator import Allocator

VERSION = "7b73dc51bba043d6b3269dd497263f03d52fc1ca"

class Speedymalloc(Allocator):
    """ Speedymalloc definition for allocbench"""

    sources = GitArtifact("speedymalloc", "https://gitlab.cs.fau.de/flow/speedymalloc.git")

    def __init__(self, name, **kwargs):

        configuration = ""
        for option, value in kwargs.get("options", {}).items():
            configuration += f"-D{option}={value} "

        self.build_cmds = [f"meson {{srcdir}} {{dir}} {configuration}",
                           "ninja -C {dir}"]

        self.LD_PRELOAD = "{dir}/libspeedymalloc.so"
        super().__init__(name, **kwargs)

speedymalloc = Speedymalloc("speedymalloc", version=VERSION)

speedymalloc_dont_madv_free = Speedymalloc("speedymalloc_dont_madv_free",
                                            options = {"madvise_free": "false"},
                                            version=VERSION)

speedymalloc_dont_madv_willneed = Speedymalloc("speedymalloc_dont_madv_willneed",
                                               options = {"madvise_willneed": "false"},
                                               version=VERSION)

speedymalloc_4095_sc_32 = Speedymalloc("speedymalloc_dont_madv_willneed",
                                       options = {"cache_bins": 4095,
                                                  "cache_bin_seperation": 32},
                                       version=VERSION)

speedymalloc_no_glab = Speedymalloc("speedymalloc_dont_madv_willneed",
                                    options = {"max_local_allocation_buffer_size": 0},
                                    version=VERSION)
