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

"""Definition of the RAxML-ng benchmark"""

import os
import re
import subprocess
import sys
from urllib.request import urlretrieve

from src.benchmark import Benchmark
from src.util import print_info, download_reporthook


RUNTIME_RE = re.compile("Elapsed time: (?P<runtime>(\\d*.\\d*)) seconds")


class BenchmarkRaxmlng(Benchmark):
    """RAxML-ng benchmark
    """

    def __init__(self):
        name = "raxmlng"

        super().__init__(name)
        
        self.cmd = (f"raxml-ng --msa {self.build_dir}/ng-tutorial/prim.phy --model GTR+G"
                    " --redo --threads 2 --seed 2")

    def prepare(self):
        super().prepare()

        # git clone --recursive 
        # cd raxml-ng
        # mkdir build && cd build
        # cmake ..
        # make

        version = "0.9"
        
        url = "https://github.com/amkozlov/raxml-ng"
        data_url = "https://github.com/amkozlov/ng-tutorial"
        raxmlng_dir = os.path.join(self.build_dir, "raxml-ng-git")
        raxmlng_builddir = os.path.join(raxmlng_dir, "build")

        self.results["facts"]["versions"]["raxml-ng"] = version

        if not os.path.isdir(raxmlng_dir):
            proc = subprocess.run(["git", "clone", "--recursive", url, raxmlng_dir],
                                  # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)
            
            # Create builddir
            os.makedirs(raxmlng_builddir, exist_ok=True)

            # building raxml-ng
            proc = subprocess.run(["cmake", ".."],
                                  cwd=raxmlng_builddir,
                                  # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)

            proc = subprocess.run(["make"],
                                  cwd=raxmlng_builddir,
                                  # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)
            
            # create symlinks
            for exe in ["raxml-ng"]:
                src = os.path.join(raxmlng_dir, "bin", exe)
                dest = os.path.join(self.build_dir,exe)
                os.link(src, dest)

            # clone test data
            proc = subprocess.run(["git", "clone", data_url],
                                  cwd=self.build_dir,
                                  # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  universal_newlines=True)

    def cleanup(self):
        for direntry in os.listdir():
            if direntry.startswith("prim.raxml"):
                os.remove(direntry)


    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):
        result["runtime"] = RUNTIME_RE.search(stdout).group("runtime")

    def summary(self):
        self.barplot_single_arg("{runtime}",
                                ylabel='"runtime in s"',
                                title='"raxml-ng tree inference benchmark"',
                                filepostfix="runtime")

        self.export_stats_to_dataref("runtime")

        self.barplot_single_arg("{VmHWM}",
                                ylabel='"VmHWM in KB"',
                                title='"raxml-ng memusage"',
                                filepostfix="memusage")

        self.export_stats_to_dataref("VmHWM")


raxmlng = BenchmarkRaxmlng()
