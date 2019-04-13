import atexit
import matplotlib.pyplot as plt
import numpy as np
import re
import shutil
import subprocess
from subprocess import PIPE
import sys
from time import sleep

from src.globalvars import builddir
from src.benchmark import Benchmark
from src.util import *

server_cmd = "{} -c {}/benchmarks/httpd/nginx/nginx.conf".format(shutil.which("nginx"), builddir).split()


class Benchmark_HTTPD(Benchmark):
    def __init__(self):
        self.name = "httpd"
        self.descrition = """TODO"""

        self.args = {"nthreads": Benchmark.scale_threads_for_cpus(2)}
        self.cmd = "ab -n 10000 -c {nthreads} localhost:8080/index.html"
        self.measure_cmd = ""
        self.server_benchmark = True

        self.requirements = ["nginx", "ab"]

        atexit.register(self.terminate_server)

        super().__init__()

    def terminate_server(self):
        ret = subprocess.run(server_cmd + ["-s", "stop"], stdout=PIPE,
                             stderr=PIPE, universal_newlines=True)
        
        if ret.returncode != 0:
            print_debug("Stdout:", ret.stdout)
            print_debug("Stderr:", ret.stderr)
            raise Exception("Stopping {} failed with {}".format(server_cmd[0], ret.returncode))

    def preallocator_hook(self, allocator, run, env, verbose):
        actual_cmd = allocator[1]["cmd_prefix"].split() + server_cmd
        print_info("Starting server with:", actual_cmd)

        ret = subprocess.run(actual_cmd, stdout=PIPE, stderr=PIPE, env=env,
                                       universal_newlines=True)
        if ret.returncode != 0:
            print_debug("Stdout:", ret.stdout)
            print_debug("Stderr:", ret.stderr)
            raise Exception("Starting {} for {} failed with {}".format(server_cmd[0], allocator[0], ret.returncode))


    def postallocator_hook(self, allocator, run, verbose):
        self.terminate_server()

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

        # linear plot
        self.plot_single_arg("{requests}",
                             xlabel='"threads"',
                             ylabel='"requests/s"',
                             title='"ab -n 10000 -c threads"')

        # linear plot
        ref_alloc = list(allocators)[0]
        self.plot_single_arg("{requests}",
                             xlabel='"threads"',
                             ylabel='"requests/s scaled at " + scale',
                             title='"ab -n 10000 -c threads (normalized)"',
                             filepostfix="norm",
                             scale=ref_alloc)

httpd = Benchmark_HTTPD()
