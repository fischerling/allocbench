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
"""Lockless allocator definition for allocbench"""

from src.allocator import Allocator
from src.artifact import ArchiveArtifact


class LocklessAllocator(Allocator):
    """Lockless allocator"""
    def __init__(self, name, **kwargs):

        self.sources = ArchiveArtifact(
            "llalloc",
            "https://locklessinc.com/downloads/lockless_allocator_src.tgz",
            "tar", "c6cb5a57882fa4775b5227a322333a6126b61f7c")

        self.build_cmds = [
            "cd {srcdir}/lockless_allocator; make", "mkdir -p {dir}",
            "ln -f -s {srcdir}/lockless_allocator/libllalloc.so.1.3 {dir}/libllalloc.so"
        ]

        self.LD_PRELOAD = "{dir}/libllalloc.so"

        super().__init__(name, **kwargs)


llalloc = LocklessAllocator("llalloc", color="purple")
