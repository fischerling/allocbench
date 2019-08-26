from src.benchmark import Benchmark

class Benchmark_Cfrac(Benchmark):
    def __init__(self):
        self.name = "cfrac"
        self.descrition = """TODO."""

        self.cmd = "cfrac{binary_suffix} {num}"

        self.args = {"num": [175451865205073170563711388363274837927895]}

        self.requirements = ["cfrac"]
        super().__init__()

    def summary(self):
        # Speed
        self.barplot_single_arg("{task-clock}/1000",
                                ylabel='"cpu-second"',
                                title='"Cfrac: runtime"',
                                filepostfix="time")

        # L1 cache misses
        self.barplot_single_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                                ylabel='"L1 misses in %"',
                                title='"Cfrac l1 cache misses"',
                                filepostfix="l1misses",
                                yerr=False)

        # Memusage
        self.barplot_single_arg("{VmHWM}",
                                ylabel='"VmHWM in KB"',
                                title='"Cfrac VmHWM"',
                                filepostfix="vmhwm")

        self.export_stats_to_dataref("task-clock")

        self.export_stats_to_dataref("VmHWM")


cfrac = Benchmark_Cfrac()
