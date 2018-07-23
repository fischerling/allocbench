import csv
import pickle
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import subprocess

from benchmark import Benchmark
from common_targets import common_targets

cmd = ("perf stat -x\; -e cpu-clock:k,cache-references,cache-misses,cycles,"
       "instructions,branches,faults,migrations "
       "build/bench_loop{} 1.2 {} 1000000 {} 10")

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
                    result = {"VSZ": [], "RSS" : []}

                    os.environ["LD_PRELOAD"] = t[1]

                    target_cmd = cmd.format(t[0], *args).split(" ")
                    if verbose:
                        print("\n" + tname, t, "\n", " ".join(target_cmd), "\n")

                    p = subprocess.Popen(target_cmd,
                                         env=os.environ,
                                         stderr=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)

                    while p.poll() == None:
                        ps = subprocess.run(["ps", "-F", "--ppid", str(p.pid)], stdout=subprocess.PIPE)
                        lines = ps.stdout.splitlines()
                        if len(lines) == 1: # perf hasn't forked yet
                            continue
                        tokens = str(lines[1]).split()
                        result["VSZ"].append(tokens[4])
                        result["RSS"].append(tokens[5])

                    p.wait()

                    output = p.stderr.read()

                    if p.returncode != 0:
                        print("\n" + " ".join(target_cmd), "exited with", p.returncode, ".\n Aborting Benchmark.")
                        print(tname, t)
                        print(output)
                        print(p.stdout)
                        return False

                    if "ERROR: ld.so" in output:
                        print("\nPreloading of", t[1], "failed for", tname, ".\n Aborting Benchmark.")
                        print(output)
                        return False

                    # Handle perf output
                    csvreader = csv.reader(output.splitlines(), delimiter=';')
                    for row in csvreader:
                        result[row[2].replace("\\", "")] = row[0].replace("\\", "")
                    key = (tname, *args)
                    if not key in self.results:
                        self.results[key] = [result]
                    else:
                        self.results[key].append(result)

            print()
        return True

    def summary(self):
        # MAXSIZE fixed
        nthreads = self.results["args"]["nthreads"]
        maxsize = self.results["args"]["maxsize"]
        targets = self.results["targets"]

        y_mapping = {v : i for i, v in enumerate(nthreads)}
        for size in maxsize:
            for target in targets:
                y_vals = [0] * len(nthreads)
                for mid, measures in self.results.items():
                    if mid[0] == target and mid[2] == size:
                        d = []
                        for m in measures:
                            # nthreads/time = MOPS/S
                            d.append(mid[1]/float(m["cpu-clock:ku"]))
                        y_vals[y_mapping[mid[1]]] = np.mean(d)
                plt.plot(nthreads, y_vals, marker='.', linestyle='-', label=target)

            plt.legend()
            plt.xlabel("threads")
            plt.ylabel("MOPS/s")
            plt.title("Loop: " + str(size) + "B")
            plt.savefig(self.name + "." + str(size) + "B.png")
            plt.clf()

        # NTHREADS fixed
        y_mapping = {v : i for i, v in enumerate(maxsize)}
        x_vals = [i + 1 for i in range(0, len(maxsize))]
        for n in nthreads:
            for target in targets:
                y_vals = [0] * len(maxsize)
                for mid, measures in self.results.items():
                    if mid[0] == target and mid[1] == n:
                        d = []
                        for m in measures:
                            # nthreads/time = MOPS/S
                            d.append(n/float(m["cpu-clock:ku"]))
                        y_vals[y_mapping[mid[2]]] = np.mean(d)
                plt.plot(x_vals, y_vals, marker='.', linestyle='-', label=target)

            plt.legend()
            plt.xticks(x_vals, maxsize)
            plt.xlabel("size in B")
            plt.ylabel("MOPS/s")
            plt.title("Loop: " + str(n) + "thread(s)")
            plt.savefig(self.name + "." + str(n) + "threads.png")
            plt.clf()

loop = Benchmark_Loop()
