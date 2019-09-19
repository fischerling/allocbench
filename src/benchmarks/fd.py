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

"""Definition of the fd benchmark"""

import os
import re
import subprocess
import sys
from urllib.request import urlretrieve

from src.benchmark import Benchmark
from src.util import print_info, download_reporthook


class BenchmarkFd(Benchmark):
    """fd benchmark
    """

    def __init__(self):
        name = "fd"

        super().__init__(name)
        
        self.cmd = "fd -HI -e c \"\" {build_dir}/linux"

    def prepare(self):
        super().prepare()

        fd_tag = "v7.4.0"
        fd_release =  f"fd-{fd_tag}-x86_64-unknown-linux-gnu"
        fd_archive = f"{fd_release}.tar.gz"
        fd_url = f"https://github.com/sharkdp/fd/releases/latest/download/{fd_archive}"
        fd_dir = os.path.join(self.build_dir, fd_release)

        self.results["facts"]["versions"]["fd"] = fd_tag

        # Create builddir
        os.makedirs(self.build_dir, exist_ok=True)

        if not os.path.isdir(fd_dir):
            if not os.path.isfile(fd_archive):
                print(f"Downloading fd {fd_tag}...")
                urlretrieve(fd_url, fd_archive, download_reporthook)
                sys.stderr.write("\n")
            
            
            # Extract redis
            proc = subprocess.run(["tar", "Cxf", self.build_dir, fd_archive],
                                  # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)
            
            # delete archive
            if proc.returncode == 0:
                os.remove(fd_archive)

            
            # create symlinks
            for exe in ["fd"]:
                src = os.path.join(fd_dir, exe)
                dest = os.path.join(self.build_dir, exe)
                os.link(src, dest)
        
        linux_version = "v5.3"
        linux_url = f"git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
        linux_dir = os.path.join(self.build_dir, "linux")
        if not os.path.isdir(linux_dir):
            # Extract redis
            proc = subprocess.run(["git", "clone", linux_url, linux_dir],
                                  # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)


    def summary(self):
        self.barplot_single_arg("{task-clock}",
                                ylabel='"runtime in s"',
                                title='"fd runtime"',
                                filepostfix="runtime")

        self.export_stats_to_dataref("task-clock")

        self.barplot_single_arg("{VmHWM}",
                                ylabel='"VmHWM in KB"',
                                title='"fd memusage"',
                                filepostfix="memusage")

        self.export_stats_to_dataref("VmHWM")


fd = BenchmarkFd()
