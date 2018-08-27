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

cmd = ("perf stat -d -x\; -e cpu-clock,cache-references,cache-misses,cycles,"
       "instructions,branches,faults,migrations "
       "build/cache-{}{} {} 100 8 1000000")

class Benchmark_Falsesharing( Benchmark ):
    def __init__(self):
        self.name = "falsesharing"
        self.descrition = """This benchmarks makes small allocations and writes
                            to them multiple times. If the allocated objects are
                            on the same cache line the writes will be expensive because
                            of cache thrashing.""",
        self.targets = common_targets
        self.nthreads = range(1, multiprocessing.cpu_count() * 2 + 1)

        self.results = {"args" : {"nthreads" : self.nthreads},
                        "targets" : self.targets,
                        "thrash": {x : {} for x in self.targets},
                        "scratch": {x: {} for x in self.targets}
                       }

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

                    os.environ["LD_PRELOAD"] = t["LD_PRELOAD"]

                    for bench in ["thrash", "scratch"]:

                        target_cmd = cmd.format(bench, t["binary_suffix"], threads).split(" ")
                        if verbose:
                            print("\n" + tname, t, "\n", " ".join(target_cmd), "\n")

                        p = subprocess.run(target_cmd,
                                             env=os.environ,
                                             stderr=subprocess.PIPE,
                                             stdout=subprocess.PIPE,
                                             universal_newlines=True)

                        output = str(p.stdout)
                        err = str(p.stderr)

                        if p.returncode != 0:
                            print("\n" + " ".join(target_cmd), "exited with",
                                    p.returncode, ".\n Aborting Benchmark.")
                            print(tname, t)
                            print(output)
                            print(p.stdout)
                            return False

                        if "ERROR: ld.so" in output:
                            print("\nPreloading of", t["LD_PRELOAD"], "failed for", tname,
                                    ".\n Aborting Benchmark.")
                            print(output)
                            return False

                        time = float(re.search("(\d*\.\d*)", output)[1])
                        result["time"] = time
                        # Handle perf output
                        csvreader = csv.reader(err.splitlines()[1:], delimiter=';')
                        for row in csvreader:
                            result[row[2].replace("\\", "")] = row[0].replace("\\", "")

                        if not threads in self.results[bench][tname]:
                            self.results[bench][tname][threads] = [result]
                        else:
                            self.results[bench][tname][threads].append(result)

            print()
        return True

    def summary(self, sd=None):
        # Speedup thrash
        nthreads = self.results["args"]["nthreads"]
        targets = self.results["targets"]

        sd = sd or ""

        y_mapping = {v : i for i, v in enumerate(nthreads)}
        for bench in ["thrash", "scratch"]:
            for target in targets:
                y_vals = [0] * len(nthreads)
                single_threaded = np.mean([m["time"] for m in self.results[bench][target][1]])
                for threads, measures in self.results[bench][target].items():
                    l1_load_misses = []
                    d = [m["time"] for m in measures]
                    y_vals[y_mapping[threads]] = single_threaded / np.mean(d)
                plt.plot(nthreads, y_vals, marker='.', linestyle='-', label=target,
                            color=targets[target]["color"])

            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("speedup")
            plt.title(bench + " speedup" )
            plt.savefig(os.path.join(sd, self.name + "." + bench + ".png"))
            plt.clf()

            for target in targets:
                y_vals = [0] * len(nthreads)
                for threads, measures in self.results[bench][target].items():
                    l1_load_misses = []
                    for m in measures:
                        misses = 0
                        loads = 0
                        for e in m:
                            if "L1-dcache-load-misses" in e:
                                misses = float(m[e])
                            elif "L1-dcache-loads" in e:
                                loads = float(m[e])
                        l1_load_misses.append(misses/loads)
                    y_vals[y_mapping[threads]] = np.mean(l1_load_misses) * 100
                plt.plot(nthreads, y_vals, marker='.', linestyle='-', label=target, color=targets[target]["color"])
            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("l1-cache-misses in %")
            plt.title(bench + " cache-misses")
            plt.savefig(os.path.join(sd, self.name + "." + bench + ".l1misses.png"))
            plt.clf()

falsesharing= Benchmark_Falsesharing()
