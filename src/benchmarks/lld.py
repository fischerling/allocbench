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

"""Benchmark definition using the llvm-lld speed benchmark"""

import os
from urllib.request import urlretrieve
import subprocess
import sys

import matplotlib.pyplot as plt

from src.benchmark import Benchmark
import src.facter
from src.util import download_reporthook


class BenchmarkLld(Benchmark):
    """LLVM-lld speed benchmark

    This benchmark runs the lld speed benchmark provided by the llvm project.
    """

    def __init__(self):
        name = "lld"

        self.run_dir = "lld-speed-test/{test}"
        # TODO: don't hardcode ld.lld location
        self.cmd = "/usr/bin/ld.lld @response.txt"

        self.args = {"test": ["chrome", "clang-fsds", "gold", "linux-kernel",
                              "llvm-as-fsds", "scylla", "clang", "clang-gdb-index",
                              "gold-fsds", "llvm-as", "mozilla"]}

        self.requirements = ["ld.lld"]
        super().__init__(name)

    def prepare(self):
        super().prepare()

        # save lld version
        self.results["facts"]["versions"]["lld"] = src.facter.exe_version("ld.lld", "-v")

        test_dir = "lld-speed-test"
        test_archive = f"{test_dir}.tar.xz"
        if not os.path.isdir(test_dir):
            if not os.path.isfile(test_archive):
                choice = input("Download missing test archive (1.1GB) [Y/n/x] ")
                if not choice in ['', 'Y', 'y']:
                    return False

                url = f"https://s3-us-west-2.amazonaws.com/linker-tests/{test_archive}"
                urlretrieve(url, test_archive, download_reporthook)
                sys.stderr.write("\n")

            # Extract tests
            proc = subprocess.run(["tar", "xf", test_archive], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, universal_newlines=True)

            # delete archive
            if proc.returncode == 0:
                os.remove(test_archive)

        self.args["test"] = os.listdir(test_dir)

        return True


    def cleanup(self):
        for perm in self.iterate_args():
            a_out = os.path.join("lld-speed-test", perm.test, "a.out")
            if os.path.isfile(a_out):
                os.remove(a_out)


    def summary(self):
        args = self.results["args"]
        allocators = self.results["allocators"]

        for perm in self.iterate_args(args=args):
            for i, allocator in enumerate(allocators):

                plt.bar([i],
                        self.results["stats"][allocator][perm]["mean"]["task-clock"],
                        yerr=self.results["stats"][allocator][perm]["std"]["task-clock"],
                        label=allocator, color=allocators[allocator]["color"])

            plt.legend(loc="best")
            plt.ylabel("Zeit in ms")
            plt.title(f"Gesamte Laufzeit {perm.test}")
            plt.savefig(".".join([self.name, perm.test, "runtime", "png"]))
            plt.clf()

        # TODO: get memusage
        # Memusage
        # self.barplot_single_arg("{VmHWM}",
                                # ylabel='"Max RSS in KB"',
                                # title='"Highwatermark of Vm (VmHWM)"',
                                # filepostfix="rss")

        # self.export_stats_to_csv("VmHWM")
        self.export_stats_to_csv("task-clock")

        # self.export_stats_to_dataref("VmHWM")
        self.export_stats_to_dataref("task-clock")


lld = BenchmarkLld()
