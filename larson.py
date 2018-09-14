import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
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

        self.cmd = "build/larson{binary_suffix} 1 8 {maxsize} 1000 10000 1 {threads}"

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
        print(stdout)
        print("no match")

    def summary(self, sd=None):
        # Speedup thrash
        args = self.results["args"]
        nthreads = args["threads"]
        targets = self.results["targets"]

        sd = sd or ""

        for arg in args:
            loose_arg = [a for a in args if a != arg][0]
            for arg_value in args[arg]:
                for target in targets:
                    y_vals = []
                    for perm in self.iterate_args_fixed({arg : arg_value}, args=args):
                        d = [m["throughput"] for m in self.results[target][perm]]
                        y_vals.append(np.mean(d))
                    x_vals = list(range(1, len(y_vals) + 1))
                    plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                        label=target, color=targets[target]["color"])
                plt.legend()
                plt.xticks(x_vals, args[loose_arg])
                plt.xlabel(loose_arg)
                plt.ylabel("OPS/s")
                plt.title("Larson: " + arg + " " + str(arg_value))
                plt.savefig(os.path.join(sd, ".".join([self.name, arg, str(arg_value), "png"])))
                plt.clf()


larson = Benchmark_Larson()
