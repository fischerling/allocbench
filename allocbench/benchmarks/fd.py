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
"""Definition of the fd benchmark"""

import os

from allocbench.artifact import ArchiveArtifact, GitArtifact
from allocbench.benchmark import Benchmark

LINUX_VERSION = 'v5.3'
FD_VERSION = 'v7.4.0'

FD_URL = ("https://github.com/sharkdp/fd/releases/latest/download/"
          f"fd-{FD_VERSION}-x86_64-unknown-linux-gnu.tar.gz")


class BenchmarkFd(Benchmark):
    """fd benchmark
    """
    def __init__(self):
        name = "fd"
        self.cmd = "fd -HI -e c '.*[0-9].*' {linux_files}"
        super().__init__(name)

        self.linux_artifact = GitArtifact(
            "linux",
            "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git")
        self.linux_files = None

        self.results["facts"]["versions"]["fd"] = FD_VERSION
        self.fd_artifact = ArchiveArtifact(
            "fd", FD_URL, "tar", "a5d8e7c8484449aa324a46abfdfaf026d7de77ee")

    def prepare(self):
        """Checkout the linux sources and download fd binary"""
        self.linux_files = self.linux_artifact.provide(LINUX_VERSION)

        if os.path.exists(self.build_dir):
            return

        fd_dir = os.path.join(self.build_dir, "fd_sources")
        self.fd_artifact.provide(fd_dir)

        # create symlink
        src = os.path.join(fd_dir, f"fd-{FD_VERSION}-x86_64-unknown-linux-gnu",
                           'fd')
        dest = os.path.join(self.build_dir, 'fd')
        os.link(src, dest)

    def summary(self):
        """Create plots showing execution time and VmHWM"""
        import allocbench.plots as plt  # pylint: disable=import-outside-toplevel
        plt.plot(self,
                 "{task-clock}",
                 plot_type='bar',
                 fig_options={
                     'ylabel': "runtime in ms",
                     'title': "fd runtime",
                 },
                 file_postfix="runtime")

        plt.export_stats_to_dataref(self, "task-clock")

        plt.plot(self,
                 "{VmHWM}",
                 plot_type='bar',
                 fig_options={
                     'ylabel': "VmHWM in KB",
                     'title': "fd memusage"
                 },
                 file_postfix="memusage")

        plt.export_stats_to_dataref(self, "VmHWM")
