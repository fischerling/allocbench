import multiprocessing
import re

from src.benchmark import Benchmark

throughput_re = re.compile("^Throughput =\s*(?P<throughput>\d+) operations per second.$")

class Benchmark_Larson( Benchmark ):
    def __init__(self):
        self.name = "larson"
        self.descrition = """This benchmark is courtesy of Paul Larson at Microsoft
                             Research. It simulates a server: each thread allocates
                             and deallocates objects, and then transfers some objects
                             (randomly selected) to other threads to be freed."""

        self.cmd = "build/larson{binary_suffix} 1 8 {maxsize} 1000 50000 1 {threads}"

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
        self.plot_fixed_arg("{throughput}/1000000",
                    ylabel="'MOPS/s'",
                    title = "'Larson: ' + arg + ' ' + str(arg_value)",
                    filepostfix = "throughput",
                    sumdir=sumdir)

        self.plot_fixed_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                    ylabel="'l1 cache misses in %'",
                    title = "'Larson cache misses: ' + arg + ' ' + str(arg_value)",
                    filepostfix = "cachemisses",
                    sumdir=sumdir)

        # Memusage
        self.plot_fixed_arg("int({VmHWM})",
                    ylabel='"VmHWM in kB"',
                    title= '"Loop Memusage: " + arg + " " + str(arg_value)',
                    filepostfix="memusage",
                    sumdir=sumdir)

larson = Benchmark_Larson()
