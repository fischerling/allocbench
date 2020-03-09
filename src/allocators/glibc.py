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
"""Glibc definitions"""

from multiprocessing import cpu_count

from src.allocator import Allocator, LIBRARY_PATH
from src.artifact import GitArtifact


class Glibc(Allocator):
    """Glibc definition for allocbench

    Glibcs are loaded using their own supplied loader"""

    sources = GitArtifact("glibc", "git://sourceware.org/git/glibc.git")

    def __init__(self, name, **kwargs):
        configure_args = ""
        if "configure_args" in kwargs:
            configure_args = kwargs["configure_args"]
            del kwargs["configure_args"]

        self.build_cmds = [
            "mkdir -p glibc-build",
            "cd glibc-build; {srcdir}/configure --prefix={dir} " +
            configure_args, "cd glibc-build; make",
            f"cd glibc-build; make -l {cpu_count()} install"
        ]

        self.cmd_prefix = "{dir}/lib/ld-linux-x86-64.so.2 --library-path {dir}/lib:" + LIBRARY_PATH

        super().__init__(name, **kwargs)


glibc = Glibc("glibc", version="glibc-2.29", color="xkcd:red")

glibc_notc = Glibc("glibc-noThreadCache",
                   configure_args="--disable-experimental-malloc",
                   version="glibc-2.29",
                   color="xkcd:maroon")

glibc_nofs = Glibc(
    "glibc-noFalsesharing",
    patches=["{patchdir}/glibc_2.29_no_passive_falsesharing.patch"],
    version="glibc-2.29",
    color="xkcd:pink")

glibc_nofs_fancy = Glibc(
    "glibc-noFalsesharingClever",
    patches=["{patchdir}/glibc_2.29_no_passive_falsesharing_fancy.patch"],
    version="glibc-2.29",
    color="xkcd:orange")
