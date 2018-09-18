import multiprocessing
import re

from benchmark import Benchmark

throughput_re = re.compile("^Throughput =\s*(?P<throughput>\d+) operations per second.$")

class Benchmark_Larson( Benchmark ):
    def __init__(self):
        self.name = "larson"
        self.descrition = """This benchmark is courtesy of Paul Larson at Microsoft
                             Research. It simulates a server: each thread allocates
                             and deallocates objects, and then transfers some objects
                             (randomly selected) to other threads to be freed."""

        self.cmd = "build/larson{binary_suffix} 1 8 {maxsize} 1000 50000 1 {threads}"
        self.measure_cmd = ""

        self.args = {
                        "maxsize" : [8, 32, 64, 128, 256, 512, 1024],
                        "threads" : range(1, multiprocessing.cpu_count() * 2 + 1)
                    }

        self.requirements = ["build/larson"]
        super().__init__()

    def process_output(self, result, stdout, stderr, target, perm, verbose):
        for l in stdout.splitlines():
            res = throughput_re.match(l)
            if res:
                result["throughput"] = int(res.group("throughput"))
                return

    def summary(self, sumdir):
        # Plot threads->throughput and maxsize->throughput
        self.plot_fixed_arg("{throughput}",
                    ylabel="'OPS/s'",
                    title = "'Larson: ' + arg + ' ' + str(arg_value)",
                    sumdir=sumdir)

larson = Benchmark_Larson()
