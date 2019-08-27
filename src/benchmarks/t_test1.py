"""Definition of the commonly used t-test1 allocator test"""

from src.benchmark import Benchmark


class BenchmarkTTest1(Benchmark):
    """t-test1 unit test

    This benchmark from ptmalloc2 allocates and frees n bins in t concurrent threads.
    """

    def __init__(self):
        self.name = "t_test1"

        self.cmd = "t-test1 {nthreads} {nthreads} 1000000 {maxsize}"

        self.args = {"maxsize":  [2 ** x for x in range(6, 18)],
                     "nthreads": Benchmark.scale_threads_for_cpus(2)}

        self.requirements = ["t-test1"]
        super().__init__()

    def summary(self):
        # mops / per second
        yval = "perm.nthreads / ({task-clock}/1000)"
        # Speed
        self.plot_fixed_arg(yval,
                            ylabel='"Mops / CPU second"',
                            title='"T-Ttest1: " + arg + " " + str(arg_value)',
                            filepostfix="time",
                            autoticks=False)

        scale = list(self.results["allocators"].keys())[0]
        self.plot_fixed_arg(yval,
                            ylabel='"Mops / CPU second scaled at {}"'.format(scale),
                            title='"T-Test1: " + arg + " " + str(arg_value) + " normalized {}"'.format(scale),
                            filepostfix="time.norm",
                            scale=scale,
                            autoticks=False)

        # L1 cache misses
        self.plot_fixed_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                            ylabel='"L1 misses in %"',
                            title='"T-Test1 l1 cache misses: " + arg + " " + str(arg_value)',
                            filepostfix="l1misses",
                            autoticks=False)

        # Speed Matrix
        self.write_best_doublearg_tex_table(yval,
                                            filepostfix="memusage.matrix")

        self.export_stats_to_csv("task-clock")


t_test1 = BenchmarkTTest1()
