from src.benchmark import Benchmark


class Benchmark_Realloc(Benchmark):
    def __init__(self):
        self.name = "realloc"
        self.descrition = """Realloc 100 times"""

        self.cmd = "realloc"

        self.args = {"oneshot": [1]}

        self.requirements = ["realloc"]
        super().__init__()

    def summary(self):
        self.barplot_single_arg("{task-clock}",
                                ylabel='"task-clock in ms"',
                                title='"realloc micro benchmark"')

        self.export_to_csv("task-clock")
        self.export_to_dataref("task-clock")


realloc = Benchmark_Realloc()
