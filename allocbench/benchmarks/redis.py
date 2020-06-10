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
"""Definition of the redis benchmark


This benchmark uses the redis benchmark tool included in the redis release
archive. The used parameters are inspired by the ones used in mimalloc-bench."
"""

import os
import re

from allocbench.artifact import ArchiveArtifact
from allocbench.benchmark import Benchmark
import allocbench.plots as plt
from allocbench.util import run_cmd

REQUESTS_RE = re.compile("(?P<requests>(\\d*.\\d*)) requests per second")

REDIS_VERSION = "5.0.5"


class BenchmarkRedis(Benchmark):
    """Definition of the redis benchmark"""
    def __init__(self):
        name = "redis"

        self.cmd = ("redis-benchmark 1000000 -n 1000000 -P 8 -q lpush"
                    " a 1 2 3 4 5 6 7 8 9 10 lrange a 1 10")
        self.servers = [{
            "name": "redis",
            "cmd": "redis-server",
            "shutdown_cmds": ["{build_dir}/redis-cli shutdown"]
        }]

        super().__init__(name)

    def prepare(self):
        """Build redis and memtier if necessary"""
        self.results["facts"]["versions"]["redis"] = REDIS_VERSION
        redis_artifact = ArchiveArtifact(
            "redis",
            f"http://download.redis.io/releases/redis-{REDIS_VERSION}.tar.gz",
            "tar", "71e38ae09ac70012b5bc326522b976bcb8e269d6")

        redis_dir = os.path.join(self.build_dir, f"redis-{REDIS_VERSION}")

        redis_artifact.provide(self.build_dir)

        # building redis
        run_cmd(["make", "-C", redis_dir, "MALLOC=libc", "USE_JEMALLOC=no"])

        # create symlinks
        for exe in ["redis-cli", "redis-server", "redis-benchmark"]:
            src = os.path.join(redis_dir, "src", exe)
            dest = os.path.join(self.build_dir, exe)
            if not os.path.exists(dest):
                os.link(src, dest)

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):  # pylint: disable=too-many-arguments, unused-argument
        result["requests"] = REQUESTS_RE.search(stdout).group("requests")

    @staticmethod
    def cleanup():
        if os.path.exists("dump.rdb"):
            os.remove("dump.rdb")

    def summary(self):
        plt.plot(self,
                 "{requests}",
                 plot_type='bar',
                 fig_options={
                     'ylabel': 'requests per s',
                     'title': 'redis throughput',
                 },
                 file_postfix="requests")

        plt.plot(self,
                 "{redis_VmHWM}",
                 plot_type='bar',
                 fig_options={
                     'ylabel': 'VmHWM in KB',
                     'title': 'redis memusage',
                 },
                 file_postfix="vmhwm")

        plt.export_stats_to_dataref(self, "requests")
