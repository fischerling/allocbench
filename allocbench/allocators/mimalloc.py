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
"""mimalloc definition for allocbench"""

from allocbench.allocator import Allocator
from allocbench.artifact import GitArtifact


class Mimalloc(Allocator):
    """mimalloc allocator"""

    sources = GitArtifact("mimalloc", "https://github.com/microsoft/mimalloc")

    def __init__(self, name, **kwargs):
        self.ld_preload = "{dir}/libmimalloc.so"
        self.build_cmds = [
            "mkdir -p {dir}", "cd {dir}; cmake {srcdir}", "cd {dir}; make"
        ]
        self.requirements = ["cmake"]

        super().__init__(name, **kwargs)


# pylint: disable=invalid-name
mimalloc = Mimalloc("mimalloc", version="v1.6.0")
