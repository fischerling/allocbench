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
"""chattymalloc allocator

This shared library is not a functional allocator. It is used to trace
the allocator usage and the executed program. It overrides the malloc API
and saves each call and its result to a memory mapped output file.
"""

from allocbench.artifact import GitArtifact
from allocbench.allocator import Allocator

VERSION = "1a09b144eb18919014ecf86da3442344b0eaa5b2"


class Chattymalloc(Allocator):
    """Chattymalloc definition for allocbench"""

    sources = GitArtifact("chattymalloc",
                          "https://github.com/fischerling/chattymalloc")

    def __init__(self, name, **kwargs):

        configuration = "--buildtype=release "
        for option, value in kwargs.get("options", {}).items():
            configuration += f"-D{option}={value} "

        self.build_cmds = [
            f"meson {{srcdir}} {{dir}} {configuration}", "ninja -C {dir}"
        ]

        self.ld_preload = "{dir}/libchattymalloc.so"
        self.cmd_prefix = "env CHATTYMALLOC_FILE={{result_dir}}/{{perm}}.trace"
        self.analyze_alloc = True
        super().__init__(name, **kwargs)


# pylint: disable=invalid-name
chattymalloc = Chattymalloc("chattymalloc", version=VERSION)
