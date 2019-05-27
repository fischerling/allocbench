import matplotlib.pyplot as plt
import numpy as np
import re
import shutil
import subprocess
from subprocess import PIPE
import sys
from time import sleep

from src.benchmark import Benchmark
from src.util import *


class Benchmark_HTTPD(Benchmark):
    def __init__(self):
        self.name = "httpd"
        self.descrition = """TODO"""

        self.args = {"nthreads": Benchmark.scale_threads_for_cpus(2),
                     "site": ["index.html", "index.php"]}
        self.cmd = "ab -n 10000 -c {nthreads} localhost:8080/{site}"
        self.measure_cmd = ""
        self.server_cmds = ["nginx -c {builddir}/benchmarks/httpd/etc/nginx/nginx.conf",
                            "php-fpm -c {builddir}/benchmarks/httpd/etc/php/php.ini -y {builddir}/benchmarks/httpd/etc/php/php-fpm.conf -F"]

        self.requirements = ["nginx", "ab"]

        super().__init__()

    def process_output(self, result, stdout, stderr, allocator, perm, verbose):
        result["time"] = re.search("Time taken for tests:\s*(\d*\.\d*) seconds", stdout).group(1)
        result["requests"] = re.search("Requests per second:\s*(\d*\.\d*) .*", stdout).group(1)

        # with open("/proc/"+str(self.server.pid)+"/status", "r") as f:
            # for l in f.readlines():
                # if l.startswith("VmHWM:"):
                    # result["rssmax"] = int(l.replace("VmHWM:", "").strip().split()[0])
                    # break

    def summary(self):
        allocators = self.results["allocators"]
        args = self.results["args"]

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


httpd = Benchmark_HTTPD()
