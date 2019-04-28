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


# This is useful when evaluating strings in the plot functionsi. str(np.NaN) == "nan"
nan = np.NaN


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
        save_data["stats"] = {}
        for allocator in self.results["allocators"]:
            measures = []
            stats = []
            for ntuple in self.iterate_args(args=self.results["args"]):
                measures.append((ntuple._asdict(), self.results[allocator][ntuple]))
                if "stats" in self.results:
                    stats.append((ntuple._asdict(), self.results["stats"][allocator][ntuple]))

            save_data[allocator] = measures
            if "stats" in self.results:
                save_data["stats"][allocator] = stats

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

            d = {}
            if "stats" in self.results:
                for dic, value in self.results["stats"][allocator]:
                    d[self.Perm(**dic)] = value
                self.results["stats"][allocator] = d

        # add missing statistics
        if not "stats" in self.results:
            self.calc_desc_statistics()

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

    def run(self, runs=5):
        if runs < 1:
            return

        print_status("Running", self.name, "...")
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

        # save one valid result to expand expand invalid results
        valid_result = {}

        n = len(list(self.iterate_args())) * len(self.allocators)
        for run in range(1, runs + 1):
            print_status(run, ". run", sep='')

            i = 0
            for alloc_name, t in self.allocators.items():
                if alloc_name not in self.results:
                    self.results[alloc_name] = {}

                env = dict(os.environ)
                env["LD_PRELOAD"] = env.get("LD_PRELOAD", "")
                env["LD_PRELOAD"] += " " + "build/print_status_on_exit.so"
                env["LD_PRELOAD"] += " " + t["LD_PRELOAD"]

                if hasattr(self, "preallocator_hook"):
                    self.preallocator_hook((alloc_name, t), run, env,
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
                                                            binary,
                                                            actual_cmd[cmd_start:])
                        # substitute again
                        actual_cmd = actual_cmd.format(**substitutions)

                        actual_env = env

                    print_debug("\nCmd:", actual_cmd)
                    res = subprocess.run(actual_cmd.split(),
                                         env=actual_env,
                                         stderr=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)

                    result = {}

                    if res.returncode != 0 or "ERROR: ld.so" in res.stderr:
                        print()
                        print_debug("Stdout:\n" + res.stdout)
                        print_debug("Stderr:\n" + res.stderr)
                        if res.returncode != 0:
                            print_error("{} failed with exit code {} for {}".format(actual_cmd, res.returncode, alloc_name))
                        else:
                            print_error("Preloading of {} failed for {}".format(t["LD_PRELOAD"], alloc_name))

                    # parse and store results
                    else:
                        if not self.server_benchmark:
                            # Read VmHWM from status file. If our benchmark didn't fork
                            # the first occurance of VmHWM is from our benchmark
                            with open("status", "r") as f:
                                for l in f.readlines():
                                    if l.startswith("VmHWM:"):
                                        result["VmHWM"] = l.split()[1]
                                        break
                            os.remove("status")

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
                                              alloc_name, "and", perm)

                        if hasattr(self, "process_output"):
                            self.process_output(result, res.stdout, res.stderr,
                                                alloc_name, perm,
                                                verbose=src.globalvars.verbosity)

                        # save a valid result so we can expand invalid ones
                        if valid_result != None:
                            valid_result = result

                    if not perm in self.results[alloc_name]:
                        self.results[alloc_name][perm] = []
                    self.results[alloc_name][perm].append(result)

                if hasattr(self, "postallocator_hook"):
                    self.postallocator_hook((alloc_name, t), run,
                                            verbose=src.globalvars.verbosity)
            print()

        # Reset PATH
        os.environ["PATH"] = os.environ["PATH"].replace(":build/" + self.name, "")

        #expand invalid results
        if valid_result != {}:
            for allocator in self.allocators:
                for perm in self.iterate_args():
                    for i, m in enumerate(self.results[allocator][perm]):
                        if m == {}:
                            self.results[allocator][perm][i] = {k: np.NaN for k in valid_result}

        self.calc_desc_statistics()

    def calc_desc_statistics(self):
        if "stats" in self.results:
            return
        allocs = self.results["allocators"]
        self.results["stats"] = {}
        for alloc in allocs:
            self.results["stats"][alloc] = {}
            for perm in self.iterate_args(self.results["args"]):
                stats = {s: {} for s in ["min", "max", "mean", "median", "std",
                                         "std_perc",
                                         "lower_quartile", "upper_quartile",
                                         "lower_whiskers", "upper_whiskers",
                                         "outliers"]}
                for dp in self.results[alloc][perm][0]:
                    try:
                        data = [float(m[dp]) for m in self.results[alloc][perm]]
                    except ValueError as e:
                        print_debug(e)
                        continue
                    stats["min"][dp] = np.min(data)
                    stats["max"][dp] = np.max(data)
                    stats["mean"][dp] = np.mean(data)
                    stats["median"][dp] = np.median(data)
                    stats["std"][dp] = np.std(data, ddof=1)
                    stats["std_perc"][dp] = stats["std"][dp] / stats["mean"][dp]
                    stats["lower_quartile"][dp], stats["upper_quartile"][dp] = np.percentile(data, [25, 75])
                    trimmed_range = stats["upper_quartile"][dp] - stats["lower_quartile"][dp]
                    stats["lower_whiskers"][dp] = stats["lower_quartile"][dp] - trimmed_range
                    stats["upper_whiskers"][dp] = stats["upper_quartile"][dp] - trimmed_range
                    outliers = []
                    for d in data:
                        if d > stats["upper_whiskers"][dp] or d < stats["lower_whiskers"][dp]:
                            outliers.append(d)
                    stats["outliers"][dp] = outliers

                self.results["stats"][alloc][perm] = stats

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
                        mean = eval(yval.format(**self.results["stats"][allocator][perm]["mean"]))
                        norm_mean = eval(yval.format(**self.results["stats"][scale][perm]["mean"]))
                        y_vals.append(mean / norm_mean)
                else:
                    y_vals.append(eval(yval.format(**self.results["stats"][allocator][perm]["mean"])))


            plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                     label=allocator, color=allocators[allocator]["color"])

        plt.legend(loc="best")
        if not autoticks:
            plt.xticks(x_vals, args[arg])
        plt.xlabel(eval(xlabel))
        plt.ylabel(eval(ylabel))
        plt.title(eval(title))
        plt.savefig(os.path.join(sumdir, ".".join([self.name, filepostfix, file_ext])))
        plt.clf()

    def barplot_single_arg(self, yval, ylabel="'y-label'", xlabel="'x-label'",
                        title="'default title'", filepostfix="", sumdir="",
                        arg="", scale=None, file_ext="png"):

        args = self.results["args"]
        allocators = self.results["allocators"]
        nallocators = len(allocators)

        arg = arg or list(args.keys())[0]
        narg = len(args[arg])


        for i, allocator in enumerate(allocators):
            x_vals = list(range(i, narg * (nallocators+1), nallocators+1))
            y_vals = []
            for perm in self.iterate_args(args=args):
                if scale:
                    if scale == allocator:
                        y_vals = [1] * len(x_vals)
                    else:
                        mean = eval(yval.format(**self.results["stats"][allocator][perm]["mean"]))
                        norm_mean = eval(yval.format(**self.results["stats"][scale][perm]["mean"]))
                        y_vals.append(mean / norm_mean)
                else:
                    y_vals.append(eval(yval.format(**self.results["stats"][allocator][perm]["mean"])))


            plt.bar(x_vals, y_vals, width=1, label=allocator,
                    color=allocators[allocator]["color"])

        plt.legend(loc="best")
        plt.xticks(list(range(int(np.floor(nallocators/2)), narg*(nallocators+1), nallocators+1)), args[arg])
        plt.xlabel(eval(xlabel))
        plt.ylabel(eval(ylabel))
        plt.title(eval(title))
        plt.savefig(os.path.join(sumdir, ".".join([self.name, filepostfix, file_ext])))
        plt.clf()

    def plot_fixed_arg(self, yval, ylabel="'y-label'", xlabel="loose_arg",
                       autoticks=True, title="'default title'", filepostfix="",
                       sumdir="", fixed=[], file_ext="png", scale=None):

        args = self.results["args"]
        allocators = self.results["allocators"]

        for arg in fixed or args:
            loose_arg = [a for a in args if a != arg][0]

            if not autoticks:
                x_vals = list(range(1, len(args[loose_arg]) + 1))
            else:
                x_vals = args[loose_arg]

            for arg_value in args[arg]:
                for allocator in allocators:
                    y_vals = []
                    for perm in self.iterate_args_fixed({arg: arg_value}, args=args):
                        if scale:
                            if scale == allocator:
                                y_vals = [1] * len(x_vals)
                            else:
                                mean = eval(yval.format(**self.results["stats"][allocator][perm]["mean"]))
                                norm_mean = eval(yval.format(**self.results["stats"][scale][perm]["mean"]))
                                y_vals.append(mean / norm_mean)
                        else:
                            eval_dict = self.results["stats"][allocator][perm]["mean"]
                            eval_str = yval.format(**eval_dict)
                            y_vals.append(eval(eval_str))


                    plt.plot(x_vals, y_vals, marker='.', linestyle='-',
                             label=allocator, color=allocators[allocator]["color"])

                plt.legend(loc="best")
                if not autoticks:
                    plt.xticks(x_vals, args[loose_arg])
                plt.xlabel(eval(xlabel))
                plt.ylabel(eval(ylabel))
                plt.title(eval(title))
                plt.savefig(os.path.join(sumdir, ".".join([self.name, arg,
                            str(arg_value), filepostfix, file_ext])))
                plt.clf()

    def export_to_csv(self, datapoint, path=None):
        allocators = self.results["allocators"]
        args = self.results["args"]
        stats = self.results["stats"]

        if path is None:
            path = datapoint

        path = path + ".csv"

        stats_fields = list(stats[list(allocators)[0]][list(self.iterate_args(args=args))[0]])
        fieldnames = ["allocator", *args, *stats_fields]
        widths = []
        for fieldname in fieldnames:
            widths.append(len(fieldname) + 2)

        # collect rows
        rows = {}
        for alloc in allocators:
            rows[alloc] = {}
            for perm in self.iterate_args(args=args):
                d = []
                d.append(alloc)
                d += list(perm._asdict().values())
                d += [stats[alloc][perm][s][datapoint] for s in stats[alloc][perm]]
                d[-1] = (",".join([str(x) for x in d[-1]]))
                rows[alloc][perm] = d

        # calc widths
        for i in range(0, len(fieldnames)):
            for alloc in allocators:
                for perm in self.iterate_args(args=args):
                    field_len = len(str(rows[alloc][perm][i])) + 2
                    if  field_len > widths[i]:
                        widths[i] = field_len

        with open(path, "w") as f:
            headerline = ""
            for i, h in enumerate(fieldnames):
                headerline += h.ljust(widths[i])
            print(headerline, file=f)

            for alloc in allocators:
                for perm in self.iterate_args(args=args):
                    line = ""
                    for i, x in enumerate(rows[alloc][perm]):
                        line += str(x).ljust(widths[i])
                    print(line, file=f)

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
            print("\\documentclass{standalone}", file=f)
            print("\\begin{document}", file=f)
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
            print("\\end{document}", file=f)
