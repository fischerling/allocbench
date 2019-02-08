from collections import namedtuple
import csv
import itertools
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import shutil
import subprocess

from src.allocators import allocators


class Benchmark (object):

    defaults = {
        "name": "default_benchmark",
        "description": ("This is the default benchmark description please add"
                        "your own useful one."),

        "measure_cmd": "perf stat -x, -d",
        "cmd": "true",
        "allocators": allocators,
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
        self.results["allocators"] = self.allocators
        self.results.update({t: {} for t in self.allocators})

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
        for allocator in self.results["allocators"]:
            tmp_list = []
            for ntuple, measures in self.results[allocator].items():
                tmp_list.append((ntuple._asdict(), measures))
            save_data[allocator] = tmp_list

        with open(f, "wb") as f:
            pickle.dump(save_data, f)

    def load(self, path=None, verbose=False):
        if not path:
            f = self.name + ".save"
        else:
            if os.path.isdir(path):
                f = os.path.join(path, self.name + ".save")
            else:
                f = path
        if verbose:
            print("Loading results from:", self.name + ".save")
        with open(f, "rb") as f:
            self.results = pickle.load(f)
        # Build new named tuples
        for allocator in self.results["allocators"]:
            d = {}
            for dic, measures in self.results[allocator]:
                d[self.Perm(**dic)] = measures
            self.results[allocator] = d

    def prepare(self, verbose=False):
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        os.environ["PATH"] += ":" + os.path.join("build", "benchmarks",
                                                 self.name)

        for r in self.requirements:
            fpath, fname = os.path.split(r)

            # Search for file
            if fpath:
                if not is_exe(r):
                    return False
            # Search in PATH
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

    def run(self, verbose=False, runs=5):
        if runs > 0:
            print("Running", self.name, "...")
        n = len(list(self.iterate_args())) * len(self.allocators)
        for run in range(1, runs + 1):
            print(str(run) + ". run")

            i = 0
            for tname, t in self.allocators.items():
                if tname not in self.results:
                    self.results[tname] = {}

                os.environ["LD_PRELOAD"] = "build/print_status_on_exit.so "
                os.environ["LD_PRELOAD"] += t["LD_PRELOAD"]

                if hasattr(self, "preallocator_hook"):
                    if self.preallocator_hook((tname, t), run, verbose):
                        return False

                for perm in self.iterate_args():
                    i += 1
                    print(i, "of", n, "\r", end='')

                    actual_cmd = self.measure_cmd + " "

                    perm_dict = perm._asdict()
                    perm_dict.update(t)
                    actual_cmd += self.cmd.format(**perm_dict)

                    res = subprocess.run(actual_cmd.split(),
                                         stderr=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)

                    if res.returncode != 0:
                        print("\n" + actual_cmd, "exited with", res.returncode,
                              "for", tname)
                        print("Aborting Benchmark.")
                        print("Stdout:\n" + res.stdout)
                        print("Stderr:\n" + res.stderr)
                        return False

                    if "ERROR: ld.so" in res.stderr:
                        print("\nPreloading of", t["LD_PRELOAD"],
                              "failed for", tname)
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
                    if self.measure_cmd == self.defaults["measure_cmd"]:
                        csvreader = csv.reader(res.stderr.splitlines(),
                                               delimiter=',')
                        for row in csvreader:
                            # Split of the user/kernel space info to be better portable
                            try:
                                result[row[2].split(":")[0]] = row[0]
                            except Exception as e:
                                print("Exception", e, "occured on", row, "for",
                                      tname, "and", perm)

                    if run == 1:
                        self.results[tname][perm] = []
                    self.results[tname][perm].append(result)

                if hasattr(self, "postallocator_hook"):
                    if self.postallocator_hook((tname, t), run, verbose):
                        return False
            print()
        os.environ["PATH"] = os.environ["PATH"].replace(":build/" + self.name, "")
        return True

    def plot_single_arg(self, yval, ylabel="'y-label'", xlabel="'x-label'",
                        autoticks=True, title="default title", filepostfix="",
                        sumdir="", arg=""):

        args = self.results["args"]
        allocators = self.results["allocators"]

        arg = arg or list(args.keys())[0]

        for allocator in allocators:
            y_vals = []
            for perm in self.iterate_args(args=args):
                d = []
                for m in self.results[allocator][perm]:
                    d.append(eval(yval.format(**m)))
                y_vals.append(np.mean(d))
            if not autoticks:
                x_vals = list(range(1, len(y_vals) + 1))
            else:
                x_vals = args[arg]
            plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                     label=allocator, color=allocators[allocator]["color"])

        plt.legend()
        if not autoticks:
            plt.xticks(x_vals, args[arg])
        plt.xlabel(eval(xlabel))
        plt.ylabel(eval(ylabel))
        plt.title(eval(title))
        plt.savefig(os.path.join(sumdir, ".".join([self.name, filepostfix, "png"])))
        plt.clf()

    def plot_fixed_arg(self, yval, ylabel="'y-label'", xlabel="loose_arg",
                       autoticks=True, title="'default title'", filepostfix="",
                       sumdir="", fixed=[]):

        args = self.results["args"]
        allocators = self.results["allocators"]

        for arg in fixed or args:
            loose_arg = [a for a in args if a != arg][0]
            for arg_value in args[arg]:
                for allocator in allocators:
                    y_vals = []
                    for perm in self.iterate_args_fixed({arg: arg_value}, args=args):
                        d = []
                        for m in self.results[allocator][perm]:
                            d.append(eval(yval.format(**m)))
                        y_vals.append(np.mean(d))
                    if not autoticks:
                        x_vals = list(range(1, len(y_vals) + 1))
                    else:
                        x_vals = args[loose_arg]
                    plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                             label=allocator, color=allocators[allocator]["color"])

                plt.legend()
                if not autoticks:
                    plt.xticks(x_vals, args[loose_arg])
                plt.xlabel(eval(xlabel))
                plt.ylabel(eval(ylabel))
                plt.title(eval(title))
                plt.savefig(os.path.join(sumdir, ".".join([self.name, arg,
                            str(arg_value), filepostfix, "png"])))
                plt.clf()

    def write_best_doublearg_tex_table(self, evaluation, sort=">",
                                       filepostfix="", sumdir="", std=False):
        args = self.results["args"]
        keys = list(args.keys())
        allocators = self.results["allocators"]

        header_arg = keys[0] if len(args[keys[0]]) < len(args[keys[1]]) else keys[1]
        row_arg = [arg for arg in args if arg != header_arg][0]

        headers = args[header_arg]
        rows = args[row_arg]

        cell_text = []
        for av in rows:
            row = []
            for perm in self.iterate_args_fixed({row_arg: av}, args=args):
                best = []
                best_val = None
                for allocator in allocators:
                    d = []
                    for m in self.results[allocator][perm]:
                        d.append(eval(evaluation.format(**m)))
                    mean = np.mean(d)
                    if not best_val:
                        best = [allocator]
                        best_val = mean
                    elif ((sort == ">" and mean > best_val)
                          or (sort == "<" and mean < best_val)):
                        best = [allocator]
                        best_val = mean
                    elif mean == best_val:
                        best.append(allocator)

                row.append("{}: {:.3f}".format(best[0], best_val))
            cell_text.append(row)

        fname = os.path.join(sumdir, ".".join([self.name, filepostfix, "tex"]))
        with open(fname, "w") as f:
            print("\\begin{tabular}{|", end="", file=f)
            print(" l |" * len(headers), "}", file=f)

            print(header_arg+"/"+row_arg, end=" & ", file=f)
            for header in headers[:-1]:
                print(header, end="& ", file=f)
            print(headers[-1], "\\\\", file=f)

            for i, row in enumerate(cell_text):
                print(rows[i], end=" & ", file=f)
                for e in row[:-1]:
                    print(e, end=" & ", file=f)
                print(row[-1], "\\\\", file=f)
            print("\\end{tabular}", file=f)
