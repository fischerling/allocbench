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
"""Streamflow allocator definition for allocbench"""

from src.allocator import Allocator
from src.artifact import GitArtifact


class Streamflow(Allocator):
    """Streamflow allocator"""

    sources = GitArtifact("streamflow", "https://github.com/scotts/streamflow")

    def __init__(self, name, **kwargs):

        self.LD_PRELOAD = "{dir}/libstreamflow.so"
        self.build_cmds = [
            "cd {srcdir}; make", "mkdir -p {dir}",
            "ln -f -s {srcdir}/libstreamflow.so {dir}/libstreamflow.so"
        ]

        super().__init__(name, **kwargs)


streamflow = Streamflow("Streamflow",
                        version="8ac345c0f69ec9e7af02f3555c2c97eaa07a442e",
                        color="xkcd:light brown")
