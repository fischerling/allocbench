from collections import namedtuple
import copy
import csv
import itertools
import os
import pickle
import subprocess

from common_targets import common_targets

class Benchmark (object):

    defaults = {
        "name" : "default_benchmark",
        "description" : "This is the default benchmark description please add your own useful one.",
        
        "perf_cmd" : "perf stat -x, -dd ",
        "analyse_cmd" : "memusage -p {} -t ",
        "cmd" : "true",
        "targets" : common_targets,
    }

    def __init__(self):
        # Set default values
        for k in Benchmark.defaults:
            if not hasattr(self, k):
                setattr(self, k, Benchmark.defaults[k])

        # non copy types
        if not hasattr(self, "args"):
            self.args = {}

        self.Perm = namedtuple("Perm", self.args.keys())
        
        if not hasattr(self, "results"):
            self.results = {}
        self.results["args"] = self.args
        self.results["targets"] = self.targets
        self.results.update({t : {} for t in self.targets})

        if not hasattr(self, "requirements"):
            self.requirements = []
    
    def save(self, path=None, verbose=False):
        f = path if path else self.name + ".save"
        if verbose:
            print("Saving results to:", self.name + ".save")
        # Pickle can't handle namedtuples so convert the dicts of namedtuples
        # into lists of dicts.
        save_data = {"args" : self.results["args"], "targets" : self.results["targets"]}
        for target in self.results["targets"]:
            l = []
            for ntuple, measures in self.results[target].items():
                l.append((ntuple._asdict(), measures))
            save_data[target] = l

        with open(f, "wb") as f:
            pickle.dump(save_data, f)

    def load(self, path=None, verbose=False):
        f = path if path else self.name + ".save"
        if verbose:
            print("Loading results from:", self.name + ".save")
        with open(f, "rb") as f:
            save_data = pickle.load(f)
        # Build new named tuples
        self.results["args"] = save_data["args"]
        self.results["targets"] = save_data["targets"]
        for target in save_data["targets"]:
            d = {}
            for dic, measures in save_data[target]:
                d[self.Perm(**dic)] = measures
            self.results[target] = d

    def prepare(self, verbose=False):
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        for r in self.requirements:
            fpath, fname = os.path.split(r)
            
            if fpath:
                if not is_exe(r):
                    return False
            else:
                found = False
                for path in os.environ["PATH"].split(os.pathsep):
                    exe_file = os.path.join(path, r)
                    if is_exe(exe_file):
                        found = True

                if not found:
                    return False

        return True

    def iterate_args(self):
        """Return a dict for each possible combination of args"""
        arg_names = sorted(self.args.keys())
        for p in itertools.product(*[self.args[k] for k in arg_names]):
            Perm = namedtuple("Perm", arg_names)
            yield Perm(*p)

    def iterate_args_fixed(self, fixed):
        for p in self.iterate_args():
            p_dict = p._asdict()
            is_fixed = True
            for k in fixed:
                if p_dict[k] != fixed[k]:
                    is_fixed = False
                    break
            if is_fixed:
                yield p
            

    def analyse(self, verbose=False):
        for perm in self.iterate_args():
            file_name = ".".join(list(self.name, *p.items()))

            actual_cmd = analyse_cmd.format(file_name + ".png")
            if "binary_suffix" in cmd:
                p["binary_suffix"] = ""
            actual_cmd += cmd.format(**perm._asdict())
            
            with open(file_name + ".hist", "w") as f:
                res = subprocess.run(actual_cmd.split(),
                                    stderr=f,
                                    universal_newlines=True)

                if res.returncode != 0:
                    print(actual_cmd, "failed.")
                    print("Aborting analysing.")
                    print("You may look at", file_name + ".hist", "to fix this.")
                    return


    def run(self, verbose=False, runs=5):
        n = len(list(self.iterate_args()))
        for run in range(1, runs + 1):
            print(str(run) + ". run")

            for i, perm in enumerate(self.iterate_args()):
                print(i + 1, "of", n, "\r", end='')

                for tname, t in self.targets.items():
                    if not tname in self.results:
                        self.results[tname] = {}
                    
                    actual_cmd = self.perf_cmd

                    perm_dict = perm._asdict()
                    perm_dict.update(t)
                    actual_cmd += self.cmd.format(**perm_dict)

                    os.environ["LD_PRELOAD"] = "build/print_status_on_exit.so "
                    os.environ["LD_PRELOAD"] += t["LD_PRELOAD"]

                    res = subprocess.run(actual_cmd.split(),
                                        stderr=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        universal_newlines=True)

                    if res.returncode != 0:
                        print("\n" + actual_cmd, "exited with", res.returncode)
                        print("Aborting Benchmark.")
                        print("Stdout:\n" + res.stdout)
                        print("Stderr:\n" + res.stderr)
                        return False

                    if "ERROR: ld.so" in res.stderr:
                        print("\nPreloading of", t["LD_PRELOAD"], "failed for", tname)
                        print("Stderr:\n" + res.stderr)
                        print("Aborting Benchmark.")
                        return False

                    result = {}
                    
                    # Read VmHWM from status file # If our benchmark didn't fork
                    # the first occurance of VmHWM is from our benchmark
                    with open("status", "r") as f:
                        for l in f.readlines():
                            if l.startswith("VmHWM:"):
                                result["VmHWM"] = l.split()[1]
                                break
                    os.remove("status")
                        
                    # Parse perf output
                    csvreader = csv.reader(res.stderr.splitlines(), delimiter=',')
                    for row in csvreader:
                        # Split of the user/kernel space info to be better portable
                        result[row[2].split(":")[0]] = row[0]

                    if run == 1:
                        self.results[tname][perm] = []
                    self.results[tname][perm].append(result)
            print()
        return True

