import matplotlib.pyplot as plt

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
        # bar plot
        allocators = self.results["allocators"]

        for i, allocator in enumerate(allocators):
            y_vals = []
            for perm in self.iterate_args(args=self.results["args"]):
                y_vals.append(self.results["mean"][allocator][perm]["task-clock"])
            x_vals = [i * x for x in range(1, len(y_vals) + 1)]
            plt.bar(x_vals, y_vals, width=0.7, label=allocator, align="center",
                    color=allocators[allocator]["color"])
        
        plt.legend()
        plt.ylabel("task-clock in ms")
        plt.title("realloc micro bench")
        plt.savefig(self.name + ".png")
        plt.clf()

        self.export_to_csv(datapoints=["task-clock"])


realloc = Benchmark_Realloc()
