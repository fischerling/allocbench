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

"""Definition of the redis benchmark"""

import re

from src.benchmark import Benchmark


REQUESTS_RE = re.compile("(?P<requests>(\\d*.\\d*)) requests per second")

class BenchmarkRedis(Benchmark):
    """Redis benchmark

    This benchmark uses the redis benchmark tool included in the redis release
    archive. The used parameters are inspired by the ones used in mimalloc-bench."
    """

    def __init__(self):
        name = "redis"

        self.cmd = "redis-benchmark 1000000 -n 1000000 -P 8 -q lpush a 1 2 3 4 5 6 7 8 9 10 lrange a 1 10"
        self.servers = [{"name": "redis",
                         "cmd": "redis-server",
                         "shutdown_cmds": ["redis-cli shutdown"]}]

        super().__init__(name)

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):
        result["requests"] = REQUESTS_RE.search(stdout).group("requests")

    def summary(self):
        self.barplot_single_arg("{requests}",
                                ylabel='"requests per s"',
                                title='"redis benchmark"',
                                filepostfix="requests")

        self.export_stats_to_dataref("requests")


redis = BenchmarkRedis()
