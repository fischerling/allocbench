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

    def summary(self, sumdir):
        args = self.results["args"]
        targets = self.results["targets"]

        # Speed
        self.plot_fixed_arg("perm.nthreads / float({task-clock})",
                    ylabel = '"MOPS/s"',
                    title = '"Loop: " + arg + " " + str(arg_value)',
                    filepostfix="tclock",
                    sumdir=sumdir)

        # Memusage
        self.plot_fixed_arg("int({VmHWM})",
                    ylabel='"VmHWM in kB"',
                    title= '"Loop Memusage: " + arg + " " + str(arg_value)',
                    filepostfix="memusage",
                    sumdir=sumdir)

loop = Benchmark_Loop()
