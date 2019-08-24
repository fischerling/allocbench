import matplotlib.pyplot as plt
import numpy as np
import os
from urllib.request import urlretrieve
import subprocess
import sys

from src.benchmark import Benchmark
from src.util import print_status


class BenchmarkLld(Benchmark):
    def __init__(self):
        self.name = "lld"
        self.descrition = """This benchmark runs the lld benchmarks provided
                             by the llvm project."""

        self.run_dir = "lld-speed-test/{test}"
        # TODO: don't hardcode ld.lld location
        self.cmd = "/usr/bin/ld.lld @response.txt"

        self.args = {"test": ["chrome", "clang-fsds", "gold", "linux-kernel",
                              "llvm-as-fsds", "scylla", "clang", "clang-gdb-index",
                              "gold-fsds", "llvm-as", "mozilla"]}

        self.requirements = ["ld.lld"]
        super().__init__()

    def prepare(self):
        super().prepare()

        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                s = "\r%5.1f%% %*d / %d" % (
                    percent, len(str(totalsize)), readsofar, totalsize)
                sys.stderr.write(s)
            else:  # total size is unknown
                sys.stderr.write("\rdownloaded %d" % (readsofar,))

        test_dir = "lld-speed-test"
        test_archive = f"{test_dir}.tar.xz"
        if not os.path.isdir(test_dir):
            if not os.path.isfile(test_archive):
                choice = input("Download missing test archive (1.1GB) [Y/n/x] ")
                if not choice in ['', 'Y', 'y']:
                    return False

                url = f"https://s3-us-west-2.amazonaws.com/linker-tests/{test_archive}"
                urlretrieve(url, test_archive, reporthook)
                sys.stderr.write("\n")

            # Extract tests
            p = subprocess.run(["tar", "xf", test_archive], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True)

        self.args["test"] = os.listdir(test_dir)

        return True

    def cleanup(self):
        for perm in self.iterate_args():
            a_out = os.path.join("lld-speed-test", perm.test, "a.out")
            if os.path.isfile(a_out):
                os.remove(a_out)
            

    def summary(self):
        args = self.results["args"]
        allocators = self.results["allocators"]

        for perm in self.iterate_args(args=args):
            for i, allocator in enumerate(allocators):
                
                plt.bar([i], self.results["stats"][allocator][perm]["mean"]["task-clock"],
                        label=allocator, color=allocators[allocator]["color"])
            
            plt.legend(loc="best")
            plt.ylabel("Zeit in ms")
            plt.title("Gesamte Laufzeit")
            plt.savefig(".".join([self.name, perm.test, "runtime", "png"]))
            plt.clf()

        # TODO: get memusage
        # Memusage
        # self.barplot_single_arg("{VmHWM}",
                                # ylabel='"Max RSS in KB"',
                                # title='"Highwatermark of Vm (VmHWM)"',
                                # filepostfix="rss")

        # self.export_stats_to_csv("VmHWM")
        self.export_stats_to_csv("task-clock")

        # self.export_stats_to_dataref("VmHWM")
        self.export_stats_to_dataref("task-clock")


lld = BenchmarkLld()
