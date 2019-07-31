from src.allocator import bumpptr
from src.benchmark import Benchmark


class Benchmark_Loop(Benchmark):
    def __init__(self):
        self.name = "loop"
        self.descrition = """This benchmark allocates and frees n blocks in t concurrent
                             threads."""

        self.cmd = "loop{binary_suffix} {nthreads} 1000000 {maxsize}"

        self.args = {"maxsize":  [2 ** x for x in range(6, 16)],
                     "nthreads": Benchmark.scale_threads_for_cpus(2)}

        self.requirements = ["loop"]
        super().__init__()

        # add bumpptr alloc
        self.allocators["bumpptr"] = bumpptr.build()

    def summary(self):
        # Speed
        self.plot_fixed_arg("perm.nthreads / ({task-clock}/1000)",
                            ylabel='"MOPS/cpu-second"',
                            title='"Loop: " + arg + " " + str(arg_value)',
                            filepostfix="time",
                            autoticks=False)

        scale = list(self.results["allocators"].keys())[0]
        self.plot_fixed_arg("perm.nthreads / ({task-clock}/1000)",
                            ylabel='"MOPS/cpu-second normalized {}"'.format(scale),
                            title='"Loop: " + arg + " " + str(arg_value) + " normalized {}"'.format(scale),
                            filepostfix="time.norm",
                            scale=scale,
                            autoticks=False)

        # L1 cache misses
        self.plot_fixed_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                            ylabel='"L1 misses in %"',
                            title='"Loop l1 cache misses: " + arg + " " + str(arg_value)',
                            filepostfix="l1misses",
                            autoticks=False)

        # Speed Matrix
        self.write_best_doublearg_tex_table("perm.nthreads / ({task-clock}/1000)",
                                            filepostfix="memusage.matrix")

        self.export_stats_to_csv("task-clock")
        self.export_stats_to_dataref("task-clock")


loop = Benchmark_Loop()
