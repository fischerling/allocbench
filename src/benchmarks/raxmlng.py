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

from src.artifact import GitArtifact
from src.benchmark import Benchmark
import src.plots as plt
from src.util import print_info, run_cmd

RUNTIME_RE = re.compile("Elapsed time: (?P<runtime>(\\d*.\\d*)) seconds")


class BenchmarkRaxmlng(Benchmark):
    """RAxML-ng benchmark
    """
    def __init__(self):
        name = "raxmlng"

        super().__init__(name)

        self.cmd = (
            f"raxml-ng --msa {self.build_dir}/data/prim.phy --model GTR+G"
            " --redo --threads 2 --seed 2")

    def prepare(self):
        super().prepare()

        if os.path.exists(self.build_dir):
            return

        raxmlng_sources = GitArtifact("raxml-ng",
                                      "https://github.com/amkozlov/raxml-ng")
        raxmlng_version = "0.9.0"
        raxmlng_dir = os.path.join(self.build_dir, "raxml-ng-git")
        raxmlng_builddir = os.path.join(raxmlng_dir, "build")
        self.results["facts"]["versions"]["raxml-ng"] = raxmlng_version
        raxmlng_sources.provide(raxmlng_version, raxmlng_dir)

        # Create builddir
        os.makedirs(raxmlng_builddir, exist_ok=True)

        # building raxml-ng
        run_cmd(["cmake", ".."], cwd=raxmlng_builddir)
        run_cmd(["make"], cwd=raxmlng_builddir)

        # create symlinks
        for exe in ["raxml-ng"]:
            src = os.path.join(raxmlng_dir, "bin", exe)
            dest = os.path.join(self.build_dir, exe)
            os.link(src, dest)

        raxmlng_data = GitArtifact("raxml-ng-data",
                                   "https://github.com/amkozlov/ng-tutorial")
        raxmlng_data_dir = os.path.join(self.build_dir, "data")
        raxmlng_data.provide("f8f0b6a057a11397b4dad308440746e3436db8b4",
                             raxmlng_data_dir)

    def cleanup(self):
        for direntry in os.listdir():
            if direntry.startswith("prim.raxml"):
                os.remove(direntry)

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):
        result["runtime"] = RUNTIME_RE.search(stdout).group("runtime")

    def summary(self):
        plt.barplot_single_arg(self,
                               "{runtime}",
                               ylabel='"runtime in s"',
                               title='"raxml-ng tree inference benchmark"',
                               file_postfix="runtime")

        plt.export_stats_to_dataref(self, "runtime")

        plt.barplot_single_arg(self,
                               "{VmHWM}",
                               ylabel='"VmHWM in KB"',
                               title='"raxml-ng memusage"',
                               file_postfix="memusage")

        plt.export_stats_to_dataref(self, "VmHWM")


raxmlng = BenchmarkRaxmlng()
