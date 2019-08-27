"""Definition of the realloc micro benchmark"""

from src.benchmark import Benchmark


class BenchmarkRealloc(Benchmark):
    """Realloc micro benchmark

    realloc a pointer 100 times
    """
    def __init__(self):
        self.name = "realloc"

        self.cmd = "realloc"

        self.args = {"oneshot": [1]}

        self.requirements = ["realloc"]
        super().__init__()

    def summary(self):
        self.barplot_single_arg("{task-clock}",
                                ylabel='"task-clock in ms"',
                                title='"realloc micro benchmark"')

        self.export_stats_to_csv("task-clock")
        self.export_stats_to_dataref("task-clock")


realloc = BenchmarkRealloc()
