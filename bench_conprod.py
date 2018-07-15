import csv
import pickle
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import subprocess

from common_targets import common_targets

cmd = ("perf stat -x\; -e cpu-clock:k,cache-references,cache-misses,cycles,"
       "instructions,branches,faults,migrations "
       "build/memusage build/bench_conprod{0} {1} {1} {1} 1000000 {2}")

class Benchmark_ConProd():
    def __init__(self):
        self.name = "Consumer Producer Stress Benchmark"
        self.descrition = """This benchmark makes 1000000 allocations in each of
                            n producer threads. The allocations are shared through n
                            synchronisation objects and freed/consumed by n threads."""
        self.targets = common_targets
        self.maxsize = [2 ** x for x in range(6, 16)]
        self.nthreads = range(1, multiprocessing.cpu_count() + 1)
        
        self.results = {}
    
    def prepare(self, verbose=False):
        req = ["build/bench_conprod", "build/memusage"]
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

    
    def run(self, verbose=False, save=False, runs=3):
        args_permutations = [(x,y) for x in self.nthreads for y in self.maxsize]
        n = len(args_permutations)
        for run in range(1, runs + 1):
            print(str(run) + ". run")

            for i, args in enumerate(args_permutations):
                print(i + 1, "of", n, "\r", end='')
                
                # run cmd for each target
                for tname, t in self.targets.items():

                    env = {"LD_PRELOAD" : t[1]} if t[1] != "" else None

                    target_cmd = cmd.format(t[0], *args).split(" ")
                    if verbose:
                        print("\n" + tname, t, "\n", " ".join(target_cmd), "\n")

                    p = subprocess.run(target_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                        env=env, universal_newlines=True)
                    if p.returncode != 0:
                        print("\n" + " ".join(target_cmd), "exited with", p.returncode, ".\n Aborting Benchmark.")
                        print(tname, t)
                        print(p.stderr)
                        print(p.stdout)
                        return False

                    if "ERROR: ld.so" in p.stderr:
                        print("\nPreloading of", t[1], "failed for", tname, ".\n Aborting Benchmark.")
                        return False

                    output = p.stderr.split("# End memusage\n")
                    if len(output) != 2:
                        print()
                        print(output)
                        print(tname, t)
                        print("Aborting output is not correct")

                    result = {}
                    # Strip all whitespace from memusage output
                    result["memusage"] = [x.replace(" ", "").replace("\t", "")
                                            for x in output[0].splitlines()]
                        
                    # Handle perf output
                    csvreader = csv.reader(output[1].splitlines(), delimiter=';')
                    for row in csvreader:
                        result[row[2].replace("\\", "")] = row[0].replace("\\", "")
                    key = (tname, *args)
                    if not key in self.results:
                        self.results[key] = [result]
                    else:
                        self.results[key].append(result)

            print()
        if save:
            with open(self.name + ".save", "wb") as f:
                pickle.dump(self.results, f)
        return True

    def summary(self):
        # MAXSIZE fixed
        for size in self.maxsize:
            for target in self.targets:
                y_vals = [0] * len(self.nthreads)
                for mid, measures in self.results.items():
                    if mid[0] == target and mid[2] == size:
                        d = []
                        for m in measures:
                            # nthreads/time = MOPS/S
                            d.append(mid[1]/float(m["cpu-clock:ku"]))
                        y_vals[mid[1]-1] = np.mean(d)
                plt.plot(self.nthreads, y_vals, label=target, linestyle='-', marker='.')

            plt.legend()
            plt.xlabel("consumers/producers")
            plt.ylabel("MOPS/s")
            plt.title("Consumer Producer: " + str(size) + "B")
            plt.savefig("Conprod." + str(size) + "B.png")
            plt.clf()

        # NTHREADS fixed
        y_mapping = {v : i for i, v in enumerate(self.maxsize)}
        x_vals = [i + 1 for i in range(0, len(self.maxsize))]
        for n in self.nthreads:
            for target in self.targets:
                y_vals = [0] * len(self.maxsize)
                for mid, measures in self.results.items():
                    if mid[0] == target and mid[1] == n:
                        d = []
                        for m in measures:
                            # nthreads/time = MOPS/S
                            d.append(n/float(m["cpu-clock:ku"]))
                        y_vals[y_mapping[mid[2]]] = np.mean(d)
                plt.plot(x_vals, y_vals, label=target, linestyle='-', marker='.')

            plt.legend()
            plt.xticks(x_vals, self.maxsize)
            plt.xlabel("size in B")
            plt.ylabel("MOPS/s")
            plt.title("Consumer Producer: " + str(n) + "thread(s)")
            plt.savefig("Conprod." + str(n) + "thread.png")
            plt.clf()
        
conprod = Benchmark_ConProd()
