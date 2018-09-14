from collections import namedtuple
import copy
import csv
import itertools
import os
import pickle
import shutil
import subprocess

from common_targets import common_targets

class Benchmark (object):

    defaults = {
        "name" : "default_benchmark",
        "description" : "This is the default benchmark description please add your own useful one.",
        
        "measure_cmd" : "perf stat -x, -dd ",
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
        save_data = {}
        save_data.update(self.results)
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
            self.results = pickle.load(f)
        # Build new named tuples
        for target in self.results["targets"]:
            d = {}
            for dic, measures in self.results[target]:
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

    def iterate_args(self, args=None):
        """Return a dict for each possible combination of args"""
        if not args:
            args = self.args
        arg_names = sorted(args.keys())
        for p in itertools.product(*[args[k] for k in arg_names]):
            Perm = namedtuple("Perm", arg_names)
            yield Perm(*p)

    def iterate_args_fixed(self, fixed, args=None):
        for p in self.iterate_args(args=args):
            p_dict = p._asdict()
            is_fixed = True
            for k in fixed:
                if p_dict[k] != fixed[k]:
                    is_fixed = False
                    break
            if is_fixed:
                yield p
            

    def analyse(self, verbose=False, nolibmemusage=True):
        if not nolibmemusage and not shutil.which("memusage"):
            print("memusage not found. Using chattymalloc.")
            libmemusage = False

        if nolibmemusage:
            import chattyparser
            actual_cmd = ""
            old_preload = os.environ.get("LD_PRELOAD", None)
            os.environ["LD_PRELOAD"] = "build/chattymalloc.so"

        n = len(list(self.iterate_args()))
        for i, perm in enumerate(self.iterate_args()):
            print(i + 1, "of", n, "\r", end='')
            perm = perm._asdict()
            file_name = self.name + "."
            file_name += ".".join([str(x) for x in perm.values()])
            file_name += ".memusage"

            if not nolibmemusage:
                actual_cmd = self.analyse_cmd.format(file_name + ".png")

            if "binary_suffix" in self.cmd:
                perm["binary_suffix"] = ""
            actual_cmd += self.cmd.format(**perm)
            
            res = subprocess.run(actual_cmd.split(),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)

            if res.returncode != 0:
                print(actual_cmd, "failed.")
                print("Stdout:", res.stdout)
                print("Stderr:", res.stderr)
                print("Aborting analysing.")
                return

            if nolibmemusage:
                try:
                    hist, calls, reqsize, top5reqsize = chattyparser.parse()
                    top5 = [s[1] for s in sorted([(n, s) for s, n in hist.items()])]
                    hist, calls, reqsize, top5reqsize = chattyparser.parse(track_top5=top5)

                    chattyparser.plot_hist_ascii(hist, calls, file_name + ".hist")
                    chattyparser.plot_profile(reqsize, top5reqsize, file_name + ".profile.png")
                except MemoryError as memerr:
                    print("Can't Analyse", actual_cmd, "with chattymalloc because",
                            "to much memory would be needed.")
                    continue

        os.environ["LD_PRELOAD"] = old_preload or ""
        print()

    def run(self, verbose=False, runs=5):
        if runs > 0:
            print("Running", self.name, "...")
        n = len(list(self.iterate_args())) * len(self.targets)
        for run in range(1, runs + 1):
            print(str(run) + ". run")

            i = 0
            for tname, t in self.targets.items():
                if not tname in self.results:
                    self.results[tname] = {}

                os.environ["LD_PRELOAD"] = "build/print_status_on_exit.so "
                os.environ["LD_PRELOAD"] += t["LD_PRELOAD"]

                if hasattr(self, "pretarget_hook"):
                    if self.pretarget_hook((tname, t), run, verbose):
                        return False

                for perm in self.iterate_args():
                    i += 1
                    print(i, "of", n,"\r", end='')
                    
                    actual_cmd = self.measure_cmd

                    perm_dict = perm._asdict()
                    perm_dict.update(t)
                    actual_cmd += self.cmd.format(**perm_dict)

                    res = subprocess.run(actual_cmd.split(),
                                        stderr=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        universal_newlines=True)

                    if res.returncode != 0:
                        print("\n" + actual_cmd, "exited with", res.returncode, "for", tname)
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
                    
                    # Read VmHWM from status file. If our benchmark didn't fork
                    # the first occurance of VmHWM is from our benchmark
                    with open("status", "r") as f:
                        for l in f.readlines():
                            if l.startswith("VmHWM:"):
                                result["VmHWM"] = l.split()[1]
                                break
                    os.remove("status")
                        
                    if hasattr(self, "process_output"):
                        self.process_output(result, res.stdout, res.stderr,
                                                tname, perm, verbose)

                    # Parse perf output if available
                    if self.measure_cmd != self.defaults["measure_cmd"]:
                        csvreader = csv.reader(res.stderr.splitlines(), delimiter=',')
                        for row in csvreader:
                            # Split of the user/kernel space info to be better portable
                            try:
                                result[row[2].split(":")[0]] = row[0]
                            except Exception as e:
                                print("Exception", e, "occured on", row, "for", tname, "and", perm)

                    if run == 1:
                        self.results[tname][perm] = []
                    self.results[tname][perm].append(result)

                if hasattr(self, "posttarget_hook"):
                    if self.posttarget_hook((tname, t), run, verbose):
                        return False
            print()
        return True

