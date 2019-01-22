import multiprocessing

from src.benchmark import Benchmark

class Benchmark_Loop( Benchmark ):
    def __init__(self):
        self.name = "loop"
        self.descrition = """This benchmark makes n allocations in t concurrent threads.
                            How allocations are freed can be changed with the benchmark
                            version""",

        self.cmd = "build/bench_loop{binary_suffix} {nthreads} 1000000 {maxsize}"

        self.args = {
                        "maxsize" : [2 ** x for x in range(6, 16)],
                        "nthreads" : range(1, multiprocessing.cpu_count() * 2 + 1)
                    }

        self.requirements = ["build/bench_loop"]
        super().__init__()

    def summary(self):
        # Speed
        self.plot_fixed_arg("perm.nthreads / (float({task-clock})/1000)",
                    ylabel = '"MOPS/cpu-second"',
                    title = '"Loop: " + arg + " " + str(arg_value)',
                    filepostfix="time")

        # Memusage
        self.plot_fixed_arg("int({VmHWM})",
                    ylabel='"VmHWM in kB"',
                    title= '"Loop Memusage: " + arg + " " + str(arg_value)',
                    filepostfix="memusage")

        # L1 cache misses
        self.plot_fixed_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                    ylabel='"L1 misses in %"',
                    title= '"Loop l1 cache misses: " + arg + " " + str(arg_value)',
                    filepostfix="l1misses")

        # Speed Matrix
        self.write_best_doublearg_tex_table("perm.nthreads / (float({task-clock})/1000)",
                    filepostfix="memusage.matrix")

loop = Benchmark_Loop()
