import os

from src.benchmark import Benchmark
import src.globalvars

class Benchmark_Espresso(Benchmark):
    def __init__(self):
        self.name = "espresso"
        self.descrition = """TODO."""

        self.cmd = "espresso{binary_suffix} {file}"
        self.args = {"file": [os.path.join(src.globalvars.benchsrcdir, self.name, "largest.espresso")]}

        super().__init__()

        self.requirements = ["espresso"]

    def summary(self):
        # Speed
        self.barplot_single_arg("{task-clock}/1000",
                                ylabel='"cpu-second"',
                                title='"Espresso: runtime"',
                                filepostfix="time")

        # L1 cache misses
        self.barplot_single_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                                ylabel='"L1 misses in %"',
                                title='"Espresso l1 cache misses"',
                                filepostfix="l1misses",
                                yerr=False)

        # Memusage
        self.barplot_single_arg("{VmHWM}",
                                ylabel='"VmHWM in KB"',
                                title='"Espresso VmHWM"',
                                filepostfix="vmhwm")

        self.export_stats_to_dataref("task-clock")

        self.export_stats_to_dataref("VmHWM")


espresso = Benchmark_Espresso()