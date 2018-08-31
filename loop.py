import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os

from benchmark import Benchmark

class Benchmark_Loop( Benchmark ):
    def __init__(self):
        self.name = "loop"
        self.descrition = """This benchmark makes n allocations in t concurrent threads.
                            How allocations are freed can be changed with the benchmark
                            version""",

        self.cmd = "build/bench_loop{binary_suffix} 1.2 {nthreads} 1000000 {maxsize} 10"

        self.args = {
                        "maxsize" : [2 ** x for x in range(6, 16)],
                        "nthreads" : range(1, multiprocessing.cpu_count() * 2 + 1)
                    }

        self.requirements = ["build/bench_loop"]
        super().__init__()

    def summary(self, sd=None):
        args = self.results["args"]
        targets = self.results["targets"]

        sd = sd or ""

        # Speed
        for arg in args:
            loose_arg = [a for a in args if a != arg][0]
            for arg_value in args[arg]:
                for target in targets:
                    y_vals = []
                    for perm in self.iterate_args_fixed({arg : arg_value}):
                        d = []
                        for measure in self.results[target][perm]:
                            # nthreads/time = MOPS/s
                            for e in measure:
                                if "task-clock" in e:
                                    d.append(perm.nthreads/float(measure[e]))
                        y_vals.append(np.mean(d))

                    x_vals = list(range(1, len(y_vals) + 1))

                    plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                        label=target, color=targets[target]["color"])

                plt.legend()
                plt.xticks(x_vals, args[loose_arg])
                plt.xlabel(loose_arg)
                plt.ylabel("MOPS/s")
                plt.title("Loop: " + arg + " " + str(arg_value))
                plt.savefig(os.path.join(sd, ".".join([self.name, arg, str(arg_value), "png"])))
                plt.clf()

        # Memusage
        for arg in args:
            loose_arg = [a for a in args if a != arg][0]
            for arg_value in args[arg]:
                for target in targets:
                    y_vals = []
                    for perm in self.iterate_args_fixed({arg : arg_value}):
                        d = []
                        for measure in self.results[target][perm]:
                            d.append(int(measure["VmHWM"]))
                        y_vals.append(np.mean(d))

                    x_vals = list(range(1, len(y_vals) + 1))

                    plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                        label=target, color=targets[target]["color"])

                plt.legend()
                plt.xticks(x_vals, args[loose_arg])
                plt.xlabel(loose_arg)
                plt.ylabel("VmHWM")
                plt.title("Loop Memusage: " + arg + " " + str(arg_value))
                plt.savefig(os.path.join(sd, ".".join([self.name, arg, str(arg_value), "mem", "png"])))
                plt.clf()

loop = Benchmark_Loop()
