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
"""Definition of the httpd benchmark"""

import re

from allocbench.benchmark import Benchmark
import allocbench.facter as facter
import allocbench.plots as plt


class BenchmarkHTTPD(Benchmark):
    """TODO"""
    def __init__(self):
        name = "httpd"

        self.args = {
            "nthreads": Benchmark.scale_threads_for_cpus(2),
            "site": ["index.html", "index.php"]
        }
        self.cmd = "ab -n 10000 -c {nthreads} localhost:8080/{site}"
        self.measure_cmd = ""
        self.servers = [{"name": "nginx",
                         "cmd": "nginx -c {builddir}/benchmarks/httpd/etc/nginx/nginx.conf"},
                        {"name": "php-fpm",
                         "cmd": "php-fpm -c {builddir}/benchmarks/httpd/etc/php/php.ini "\
                                 "-y {builddir}/benchmarks/httpd/etc/php/php-fpm.conf -F"}]

        self.requirements = ["nginx", "ab"]

        super().__init__(name)

    def prepare(self):
        """Retrieve nginx and ab versions"""
        super().prepare()
        self.results["facts"]["versions"]["nginx"] = facter.exe_version(
            "nginx", "-v")
        self.results["facts"]["versions"]["ab"] = facter.exe_version(
            "ab", "-V")

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):  # pylint: disable=too-many-arguments, unused-argument
        result["time"] = re.search(
            "Time taken for tests:\\s*(\\d*\\.\\d*) seconds", stdout).group(1)
        result["requests"] = re.search(
            "Requests per second:\\s*(\\d*\\.\\d*) .*", stdout).group(1)

    def summary(self):
        plt.plot(self,
                 "{requests}",
                 fig_options={
                     'xlabel': "threads",
                     'ylabel': "requests/s",
                     'title': "{perm.site}: requests/s",
                     'autoticks': False,
                 },
                 file_postfix="requests")

        plt.plot(self,
                 "{nginx_vmhwm}",
                 fig_options={
                     'xlabel': "threads",
                     'ylabel': "VmHWM in KB",
                     'title': "{perm.site}: nginx memory usage",
                     'autoticks': False,
                 },
                 file_postfix="httpd_vmhwm")

        plt.plot(self,
                 "{php-fpm_vmhwm}",
                 fig_options={
                     'xlabel': "threads",
                     'ylabel': "VmHWM in KB",
                     'title': "{perm.site}: php-fpm memory usage",
                     'autoticks': False,
                 },
                 file_postfix="php-fpm_vmhwm")
