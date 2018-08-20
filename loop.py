import csv
import pickle
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import subprocess
from subprocess import PIPE

from benchmark import Benchmark
from common_targets import common_targets

perf_cmd = ("perf stat -x\; -d -e cpu-clock,cache-references,cache-misses,cycles,"
       "instructions,branches,faults,migrations ")
cmd = "build/bench_loop{} 1.2 {} 1000000 {} 10"

class Benchmark_Loop( Benchmark ):
    def __init__(self):
        self.name = "loop"
        self.descrition = """This benchmark makes n allocations in t concurrent threads.
                            How allocations are freed can be changed with the benchmark
                            version""",
        self.targets = common_targets
        self.maxsize = [2 ** x for x in range(6, 16)]
        self.nthreads = range(1, multiprocessing.cpu_count() * 2 + 1)

        self.results = {"args" : {"nthreads" : self.nthreads, "maxsize": self.maxsize},
                        "targets" : self.targets}

    def prepare(self, verbose=False):
        req = ["build/bench_loop"]
        for r in req:
            if not os.path.isfile(r):
                print(r, "not found")
                return False
            if not os.access(r, os.X_OK):
                print(r, "not found")
                return False
            if verbose:
                print(r, "found and executable.")
        return True


    def run(self, verbose=False, runs=3):
        args_permutations = [(x,y) for x in self.nthreads for y in self.maxsize]
        n = len(args_permutations)

        for run in range(1, runs + 1):
            print(str(run) + ". run")

            for i, args in enumerate(args_permutations):
                print(i + 1, "of", n, "\r", end='')

                # run cmd for each target
                for tname, t in self.targets.items():
                    if not tname in self.results:
                        self.results[tname] = {}

                    result = {}

                    os.environ["LD_PRELOAD"] = t["LD_PRELOAD"]

                    cur_cmd = cmd.format(t["binary_suffix"], *args)

                    # Collect memory consumtion on first run
                    if run == 1:
                        subprocess.run((cur_cmd + " yes loop.out").split(), env=os.environ)
                        with open("loop.out", "r") as f:
                            for l in f.readlines():
                                if l.startswith("VmHWM:"):
                                    result["rssmax"] = l.split()[1]

                    target_cmd = perf_cmd + cur_cmd + " no"
                    if verbose:
                        print("\n" + tname, t, "\n", target_cmd, "\n")

                    p = subprocess.run(target_cmd.split(),
                                         env=os.environ,
                                         stderr=PIPE,
                                         stdout=PIPE,
                                         universal_newlines=True)


                    output = p.stderr

                    if p.returncode != 0:
                        print("\n" + " ".join(target_cmd), "exited with", p.returncode, ".\n Aborting Benchmark.")
                        print(tname, t)
                        print(output)
                        print(p.stdout)
                        return False

                    if "ERROR: ld.so" in output:
                        print("\nPreloading of", t["LD_PRELOAD"], "failed for", tname, ".\n Aborting Benchmark.")
                        print(output)
                        return False

                    # Handle perf output
                    csvreader = csv.reader(output.splitlines(), delimiter=';')
                    for row in csvreader:
                        result[row[2].replace("\\", "")] = row[0].replace("\\", "")

                    if not args in self.results[tname]:
                        self.results[tname][args] = [result]
                    else:
                        self.results[tname][args].append(result)

            print()
        return True

    def summary(self, sd=None):
        nthreads = self.results["args"]["nthreads"]
        maxsize = self.results["args"]["maxsize"]
        targets = self.results["targets"]

        sd = sd or ""

        # MAXSIZE fixed
        y_mapping = {v : i for i, v in enumerate(nthreads)}
        for size in maxsize:
            for target in targets:
                y_vals = [0] * len(nthreads)
                for margs, measures in [(a, m) for a, m in self.results[target].items() if a[1] == size]:
                    d = []
                    for m in measures:
                        # nthreads/time = MOPS/s
                        for e in m:
                            if "cpu-clock" in e:
                                d.append(margs[0]/float(m[e]))
                    y_vals[y_mapping[margs[0]]] = np.mean(d)
                plt.plot(nthreads, y_vals, marker='.', linestyle='-', label=target, color=targets[target]["color"])

            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("MOPS/s")
            plt.title("Loop: " + str(size) + "B")
            plt.savefig(os.path.join(sd, self.name + "." + str(size) + "B.png"))
            plt.clf()

        # NTHREADS fixed
        y_mapping = {v : i for i, v in enumerate(maxsize)}
        x_vals = [i + 1 for i in range(0, len(maxsize))]
        for n in nthreads:
            for target in targets:
                y_vals = [0] * len(maxsize)
                for margs, measures in [(a, m) for a, m in self.results[target].items() if a[0] == n]:
                    d = []
                    for m in measures:
                        # nthreads/time = MOPS/S
                        for e in m:
                            if "cpu-clock" in e:
                                d.append(margs[0]/float(m[e]))
                    y_vals[y_mapping[margs[1]]] = np.mean(d)
                plt.plot(x_vals, y_vals, marker='.', linestyle='-', label=target, color=targets[target]["color"])

            plt.legend()
            plt.xticks(x_vals, maxsize)
            plt.xlabel("size in B")
            plt.ylabel("MOPS/s")
            plt.title("Loop: " + str(n) + "thread(s)")
            plt.savefig(os.path.join(sd, self.name + "." + str(n) + "threads.png"))
            plt.clf()

        #Memusage
        y_mapping = {v : i for i, v in enumerate(nthreads)}
        for size in maxsize:
            for target in targets:
                y_vals = [0] * len(nthreads)
                for margs, measures in [(a, m) for a, m in self.results[target].items() if a[1] == size]:
                    y_vals[y_mapping[margs[0]]] = int(measures[0]["rssmax"])
                plt.plot(nthreads, y_vals, marker='.', linestyle='-', label=target, color=targets[target]["color"])

            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("kb")
            plt.title("Memusage Loop: " + str(size) + "B")
            plt.savefig(os.path.join(sd, self.name + "." + str(size) + "B.mem.png"))
            plt.clf()

        # NTHREADS fixed
        y_mapping = {v : i for i, v in enumerate(maxsize)}
        x_vals = [i + 1 for i in range(0, len(maxsize))]
        for n in nthreads:
            for target in targets:
                y_vals = [0] * len(maxsize)
                for margs, measures in [(a, m) for a, m in self.results[target].items() if a[0] == n]:
                    y_vals[y_mapping[margs[1]]] = int(measures[0]["rssmax"])
                plt.plot(x_vals, y_vals, marker='.', linestyle='-', label=target, color=targets[target]["color"])

            plt.legend()
            plt.xticks(x_vals, maxsize)
            plt.xlabel("size in B")
            plt.ylabel("kb")
            plt.title("Memusage Loop: " + str(n) + "thread(s)")
            plt.savefig(os.path.join(sd, self.name + "." + str(n) + "threads.mem.png"))
            plt.clf()

loop = Benchmark_Loop()
