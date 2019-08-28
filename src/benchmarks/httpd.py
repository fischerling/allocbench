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

"""Definition of the httpd benchmark"""

import re

from src.benchmark import Benchmark


class BenchmarkHTTPD(Benchmark):
    """TODO"""

    def __init__(self):
        self.name = "httpd"

        self.args = {"nthreads": Benchmark.scale_threads_for_cpus(2),
                     "site": ["index.html", "index.php"]}
        self.cmd = "ab -n 10000 -c {nthreads} localhost:8080/{site}"
        self.measure_cmd = ""
        self.server_cmds = ["nginx -c {builddir}/benchmarks/httpd/etc/nginx/nginx.conf",
                            "php-fpm -c {builddir}/benchmarks/httpd/etc/php/php.ini -y {builddir}/benchmarks/httpd/etc/php/php-fpm.conf -F"]

        self.requirements = ["nginx", "ab"]

        super().__init__()

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):
        result["time"] = re.search("Time taken for tests:\\s*(\\d*\\.\\d*) seconds", stdout).group(1)
        result["requests"] = re.search("Requests per second:\\s*(\\d*\\.\\d*) .*", stdout).group(1)

        # with open("/proc/"+str(self.server.pid)+"/status", "r") as f:
            # for l in f.readlines():
                # if l.startswith("VmHWM:"):
                    # result["rssmax"] = int(l.replace("VmHWM:", "").strip().split()[0])
                    # break

    def summary(self):
        allocators = self.results["allocators"]

        self.calc_desc_statistics()

        # linear plot
        self.plot_fixed_arg("{requests}",
                            xlabel='"threads"',
                            ylabel='"requests/s"',
                            autoticks=False,
                            filepostfix="requests",
                            title='"ab -n 10000 -c " + str(perm.nthreads)')

        # linear plot
        ref_alloc = list(allocators)[0]
        self.plot_fixed_arg("{requests}",
                            xlabel='"threads"',
                            ylabel='"requests/s scaled at " + scale',
                            title='"ab -n 10000 -c " + str(perm.nthreads) + " (normalized)"',
                            filepostfix="requests.norm",
                            autoticks=False,
                            scale=ref_alloc)

        # bar plot
        # self.barplot_fixed_arg("{requests}",
                               # xlabel='"threads"',
                               # ylabel='"requests/s"',
                               # filepostfix="b",
                               # title='"ab -n 10000 -c threads"')


httpd = BenchmarkHTTPD()
