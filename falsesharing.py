import csv
import pickle
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import re
import subprocess

from benchmark import Benchmark
from common_targets import common_targets

cmd = ("perf stat -x\; -e cpu-clock:k,cache-references,cache-misses,cycles,"
       "instructions,branches,faults,migrations "
       "build/cache-{}{} {} 100 8 1000000")

class Benchmark_Falsesharing( Benchmark ):
    def __init__(self):
        self.name = "falsesharing"
        self.descrition = """This benchmarks makes small allocations and writes
                            to them multiple times. If the allocated objects are
                            on the same cache line the writes will be expensive because
                            of cache trashing.""",
        self.targets = common_targets
        self.nthreads = range(1, multiprocessing.cpu_count() * 2 + 1)

        self.results = {"args" : {"nthreads" : self.nthreads},
                        "targets" : self.targets,
                        "thrash": {},
                        "scratch": {}}

    def prepare(self, verbose=False):
        req = ["build/cache-thrash", "build/cache-scratch"]
        for r in req:
            if not os.path.isfile(r):
                print(r, "not found")
                return False
            if not os.access(r, os.X_OK):
                print(r, "not executable")
                return False
            if verbose:
                print(r, "found and executable.")
        return True


    def run(self, verbose=False, runs=3):
        for run in range(1, runs + 1):
            print(str(run) + ". run")

            n = len(self.nthreads)
            for i, threads in enumerate(list(range(1, n + 1)) * 2):
                print(i + 1, "of", n*2, "\r", end='')

                # run cmd for each target
                for tname, t in self.targets.items():
                    result = {}

                    os.environ["LD_PRELOAD"] = t[1]

                    for bench in ["thrash", "scratch"]:

                        target_cmd = cmd.format(bench, t[0], threads).split(" ")
                        if verbose:
                            print("\n" + tname, t, "\n", " ".join(target_cmd), "\n")

                        p = subprocess.run(target_cmd,
                                             env=os.environ,
                                             stderr=subprocess.PIPE,
                                             stdout=subprocess.PIPE,
                                             universal_newlines=True)

                        output = p.stdout

                        if p.returncode != 0:
                            print("\n" + " ".join(target_cmd), "exited with",
                                    p.returncode, ".\n Aborting Benchmark.")
                            print(tname, t)
                            print(output)
                            print(p.stdout)
                            return False

                        if "ERROR: ld.so" in output:
                            print("\nPreloading of", t[1], "failed for", tname,
                                    ".\n Aborting Benchmark.")
                            print(output)
                            return False

                        # Handle perf output
                        time = float(re.search("(\d*\.\d*)", str(output))[1])
                        key = (tname, threads)
                        if not key in self.results[bench]:
                            self.results[bench][key] = [time]
                        else:
                            self.results[bench][key].append(time)

            print()
        return True

    def summary(self):
        # Speedup thrash
        nthreads = self.results["args"]["nthreads"]
        targets = self.results["targets"]

        y_mapping = {v : i for i, v in enumerate(nthreads)}
        for bench in ["thrash", "scratch"]:
            for target in targets:
                y_vals = [0] * len(nthreads)
                single_threaded = np.mean(self.results[bench][(target, 1)])
                y_vals[0] = single_threaded
                for mid, measures in self.results[bench].items():
                    print(measures)
                    if mid[0] == target and mid[1] != 1:
                        y_vals[y_mapping[mid[1]]] = single_threaded / np.mean(measures)
                print(target, single_threaded, y_vals)
                plt.plot(nthreads, y_vals, marker='.', linestyle='-', label=target)

            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("speedup")
            plt.title(bench)
            plt.savefig(self.name + "." + bench + ".png")
            plt.clf()

falsesharing= Benchmark_Falsesharing()
