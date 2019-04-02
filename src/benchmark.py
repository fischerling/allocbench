from collections import namedtuple
import csv
import itertools
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import pickle
import shutil
import subprocess

import src.globalvars
from src.util import *


class Benchmark (object):

    perf_allowed = None

    defaults = {
        "name": "default_benchmark",
        "description": ("This is the default benchmark description please add"
                        "your own useful one."),

        "measure_cmd": "perf stat -x, -d",
        "cmd": "true",
        "allocators": src.globalvars.allocators,
        "server_benchmark": False,
    }

    @staticmethod
    def scale_threads_for_cpus(factor, steps=None):
        cpus = multiprocessing.cpu_count()
        max_threads = cpus * factor
        if not steps:
            steps = 1
            if max_threads >= 20 and max_threads < 50:
                steps = 2
            if max_threads >= 50 and max_threads < 100:
                steps = 5
            if max_threads >= 100:
                steps = 10

        # Special thread counts
        nthreads = set([1, int(cpus/2), cpus, cpus*factor])
        nthreads.update(range(steps, cpus * factor + 1, steps))
        nthreads = list(nthreads)
        nthreads.sort()

        return nthreads

    def __str__(self):
        return self.name

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
        self.results["mean"] = {alloc: {} for alloc in self.allocators}
        self.results["std"] = {alloc: {} for alloc in self.allocators}
        self.results["allocators"] = self.allocators
        self.results["facts"] = {"libcs": {}}
        self.results.update({alloc: {} for alloc in self.allocators})

        if not hasattr(self, "requirements"):
            self.requirements = []

        print_debug("Creating benchmark", self.name)
        print_debug("Cmd:", self.cmd)
        print_debug("Args:", self.args)
        print_debug("Requirements:", self.requirements)
        print_debug("Results dictionary:", self.results)

    def save(self, path=None):
        f = path if path else self.name + ".save"
        print_info("Saving results to:", self.name + ".save")
        # Pickle can't handle namedtuples so convert the dicts of namedtuples
        # into lists of dicts.
        save_data = {}
        save_data.update(self.results)
        save_data["mean"] = {}
        save_data["std"] = {}
        for allocator in self.results["allocators"]:
            measures = []
            means = []
            stds = []
            for ntuple in self.iterate_args(args=self.results["args"]):
                measures.append((ntuple._asdict(), self.results[allocator][ntuple]))
                means.append((ntuple._asdict(), self.results["mean"][allocator][ntuple]))
                stds.append((ntuple._asdict(), self.results["std"][allocator][ntuple]))

            save_data[allocator] = measures
            save_data["mean"][allocator] = means
            save_data["std"][allocator] = stds

        with open(f, "wb") as f:
            pickle.dump(save_data, f)

    def load(self, path=None):
        if not path:
            f = self.name + ".save"
        else:
            if os.path.isdir(path):
                f = os.path.join(path, self.name + ".save")
            else:
                f = path

        print_info("Loading results from:", self.name + ".save")
        with open(f, "rb") as f:
            self.results = pickle.load(f)
        # Build new named tuples
        for allocator in self.results["allocators"]:
            d = {}
            for dic, measures in self.results[allocator]:
                d[self.Perm(**dic)] = measures
            self.results[allocator] = d

            for s in ["std", "mean"]:
                d = {}
                for dic, value in self.results[s][allocator]:
                    d[self.Perm(**dic)] = value
                self.results[s][allocator] = d

    def prepare(self):
        os.environ["PATH"] += os.pathsep + os.path.join("build", "benchmarks", self.name)

        for r in self.requirements:
            exe = find_cmd(r)
            if exe is not None:
                self.results["facts"]["libcs"][r] = src.facter.get_libc_version(bin=exe)
            else:
                raise Exception("Requirement: {} not found".format(r))

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

    def run(self, runs=5, dry_run=False, cmd_prefix=""):
        if runs < 1:
            return

        # check if perf is allowed on this system
        if self.measure_cmd == self.defaults["measure_cmd"]:
            if Benchmark.perf_allowed == None:
                print_info("Check if you are allowed to use perf ...")
                res = subprocess.run(["perf", "stat", "ls"],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True)

                if res.returncode != 0:
                    print_error("Test perf run failed with:")
                    print(res.stderr, file=sys.stderr)
                    Benchmark.perf_allowed = False
                else:
                    Benchmark.perf_allowed = True

            if not Benchmark.perf_allowed:
                raise Exception("You don't have the needed permissions to use perf")

        n = len(list(self.iterate_args())) * len(self.allocators)
        for run in range(1, runs + 1):
            print_status(run, ". run", sep='')

            i = 0
            for tname, t in self.allocators.items():
                if tname not in self.results:
                    self.results[tname] = {}

                env = dict(os.environ)
                env["LD_PRELOAD"] = env.get("LD_PRELOAD", "") + "build/print_status_on_exit.so " + t["LD_PRELOAD"]

                if hasattr(self, "preallocator_hook"):
                    self.preallocator_hook((tname, t), run, env,
                                            verbose=src.globalvars.verbosity)

                for perm in self.iterate_args():
                    i += 1
                    print_info0(i, "of", n, "\r", end='')

                    # Available substitutions in cmd
                    substitutions = {"run": run}
                    substitutions.update(perm._asdict())
                    substitutions["perm"] = ("{}-"*(len(perm)-1) + "{}").format(*perm)
                    substitutions.update(t)

                    actual_cmd = self.cmd.format(**substitutions)
                    actual_env = None

                    if not self.server_benchmark:
                        # Find absolute path of executable
                        binary_end = actual_cmd.find(" ")
                        binary_end = None if binary_end == -1 else binary_end
                        cmd_start = len(actual_cmd) if binary_end == None else binary_end

                        binary = subprocess.run(["whereis", actual_cmd[0:binary_end]],
                                                stdout=subprocess.PIPE,
                                                universal_newlines=True).stdout.split()[1]

                        actual_cmd = "{} {} {} {}{}".format(self.measure_cmd,
                                                            t["cmd_prefix"],
                                                            cmd_prefix,
                                                            binary,
                                                            actual_cmd[cmd_start:])
                        # substitute again
                        actual_cmd = actual_cmd.format(**substitutions)

                        actual_env = env

                    print_debug("Cmd:", actual_cmd)
                    res = subprocess.run(actual_cmd.split(),
                                         env=actual_env,
                                         stderr=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)

                    if res.returncode != 0:
                        print()
                        print_debug("Stdout:\n" + res.stdout)
                        print_debug("Stderr:\n" + res.stderr)
                        print_error("{} failed with exit code {} for {}".format(actual_cmd, res.returncode, tname))
                        break

                    if "ERROR: ld.so" in res.stderr:
                        print()
                        print_debug("Stderr:\n" + res.stderr)
                        print_error("Preloading of {} failed for {}".format(t["LD_PRELOAD"], tname))
                        break

                    result = {}

                    if not self.server_benchmark:
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
                                            tname, perm,
                                            verbose=src.globalvars.verbosity)

                    # Parse perf output if available
                    if self.measure_cmd == self.defaults["measure_cmd"]:
                        csvreader = csv.reader(res.stderr.splitlines(),
                                               delimiter=',')
                        for row in csvreader:
                            # Split of the user/kernel space info to be better portable
                            try:
                                result[row[2].split(":")[0]] = row[0]
                            except Exception as e:
                                print_warn("Exception", e, "occured on", row, "for",
                                      tname, "and", perm)

                    if not dry_run:
                        if not perm in self.results[tname]:
                            self.results[tname][perm] = []
                        self.results[tname][perm].append(result)

                        if run == runs:
                            self.results["mean"][tname][perm] = {}
                            self.results["std"][tname][perm] = {}

                            for datapoint in self.results[tname][perm][0]:
                                try:
                                    d = [np.float(m[datapoint]) for m in self.results[tname][perm]]
                                except ValueError:
                                    d = np.NaN
                                self.results["mean"][tname][perm][datapoint] = np.mean(d)
                                self.results["std"][tname][perm][datapoint] = np.std(d)

                if hasattr(self, "postallocator_hook"):
                    self.postallocator_hook((tname, t), run,
                                            verbose=src.globalvars.verbosity)
            print()

        # Reset PATH
        os.environ["PATH"] = os.environ["PATH"].replace(":build/" + self.name, "")

    def plot_single_arg(self, yval, ylabel="'y-label'", xlabel="'x-label'",
                        autoticks=True, title="'default title'", filepostfix="",
                        sumdir="", arg="", scale=None, file_ext="png"):

        args = self.results["args"]
        allocators = self.results["allocators"]

        arg = arg or list(args.keys())[0]

        if not autoticks:
            x_vals = list(range(1, len(args[arg]) + 1))
        else:
            x_vals = args[arg]

        for allocator in allocators:
            y_vals = []
            for perm in self.iterate_args(args=args):
                if scale:
                    if scale == allocator:
                        y_vals = [1] * len(x_vals)
                    else:
                        mean = eval(yval.format(**self.results["mean"][allocator][perm]))
                        norm_mean = eval(yval.format(**self.results["mean"][scale][perm]))
                        y_vals.append(mean / norm_mean)
                else:
                    y_vals.append(eval(yval.format(**self.results["mean"][allocator][perm])))


            plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                     label=allocator, color=allocators[allocator]["color"])

        plt.legend()
        if not autoticks:
            plt.xticks(x_vals, args[arg])
        plt.xlabel(eval(xlabel))
        plt.ylabel(eval(ylabel))
        plt.title(eval(title))
        plt.savefig(os.path.join(sumdir, ".".join([self.name, filepostfix, file_ext])))
        plt.clf()

    def plot_fixed_arg(self, yval, ylabel="'y-label'", xlabel="loose_arg",
                       autoticks=True, title="'default title'", filepostfix="",
                       sumdir="", fixed=[], file_ext="png"):

        args = self.results["args"]
        allocators = self.results["allocators"]

        for arg in fixed or args:
            loose_arg = [a for a in args if a != arg][0]

            if not autoticks:
                x_vals = list(range(1, len(args[arg]) + 1))
            else:
                x_vals = args[loose_arg]

            for arg_value in args[arg]:
                for allocator in allocators:
                    y_vals = []
                    for perm in self.iterate_args_fixed({arg: arg_value}, args=args):
                        y_vals.append(eval(yval.format(**self.results["mean"][allocator][perm])))


                    plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                             label=allocator, color=allocators[allocator]["color"])

                plt.legend()
                if not autoticks:
                    plt.xticks(x_vals, args[loose_arg])
                plt.xlabel(eval(xlabel))
                plt.ylabel(eval(ylabel))
                plt.title(eval(title))
                plt.savefig(os.path.join(sumdir, ".".join([self.name, arg,
                            str(arg_value), filepostfix, file_ext])))
                plt.clf()

    def export_to_csv(self, datapoints=None, path=None, std=True):
        args = self.results["args"]
        allocators = self.results["allocators"]

        if path is None:
            if datapoints is not None:
                path = ".".join(datapoints)
            else:
                path = "full"

        path = path + ".csv"

        if datapoints is None:
            first_alloc = list(allocators)[0]
            first_perm = list(self.results[first_alloc])[0]
            datapoints = list(self.results[first_alloc][first_perm])

        for allocator in self.results["allocators"]:
            path_alloc = allocator + '_' + path
            with open(path_alloc, "w") as f:
                fieldnames = [*args]
                for d in datapoints:
                    fieldnames.append(d)
                    if std:
                        fieldnames.append(d + "(std)")

                writer = csv.DictWriter(f, fieldnames, delimiter="\t",
                                        lineterminator='\n')
                writer.writeheader()

                for perm in self.iterate_args(args=args):
                    d = {}
                    d.update(perm._asdict())

                    for dp in datapoints:
                        d[dp] = self.results["mean"][allocator][perm][dp]
                        if std:
                            fieldname = dp + "(std)"
                            d[fieldname] = self.results["std"][allocator][perm][dp]

                    writer.writerow(d)

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
