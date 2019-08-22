import atexit
from collections import namedtuple
import copy
import csv
import itertools
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import pickle
import subprocess
from time import sleep

import src.globalvars
import src.util
from src.util import print_status, print_error, print_warn
from src.util import print_info0, print_info, print_debug

# This is useful when evaluating strings in the plot functions. str(np.NaN) == "nan"
nan = np.NaN


class Benchmark (object):
    """Default implementation of most methods allocbench expects from a benchmark"""

    perf_allowed = None

    defaults = {
        "name": "default_benchmark",
        "description": ("This is the default benchmark description please add"
                        "your own useful one."),

        "measure_cmd": "perf stat -x, -d",
        "cmd": "true",
        "server_cmds": [],
        "allocators": copy.deepcopy(src.globalvars.allocators),
    }

    @staticmethod
    def terminate_subprocess(popen, timeout=5):
        """Terminate or kill a Popen object"""

        # Skip already terminated subprocess
        if popen.poll() is not None:
            return

        print_info("Terminating subprocess", popen.args)
        popen.terminate()
        try:
            print_info("Subprocess exited with ", popen.wait(timeout=timeout))
        except subprocess.TimeoutExpired:
            print_error("Killing subprocess ", popen.args)
            popen.kill()
            popen.wait()
        print_debug("Server Out:", popen.stdout.read())
        print_debug("Server Err:", popen.stderr.read())

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

        default_results = {"args": self.args,
                           "allocators": self.allocators,
                           "facts": {"libcs": {}}
                          }
        default_results.update({alloc: {} for alloc in self.allocators})

        if not hasattr(self, "results"):
            self.results = default_results
        # Add default default entrys to self.results if their key is absent
        else:
            for key, default in default_results.items():
                if key not in self.results:
                    self.results[key] = default

        if not hasattr(self, "requirements"):
            self.requirements = []

        print_debug("Creating benchmark", self.name)
        print_debug("Cmd:", self.cmd)
        print_debug("Server Cmds:", self.server_cmds)
        print_debug("Args:", self.args)
        print_debug("Requirements:", self.requirements)
        print_debug("Results dictionary:", self.results)

    def save(self, path=None):
        f = path if path else self.name + ".save"
        print_info("Saving results to:", f)
        # Pickle can't handle namedtuples so convert the dicts of namedtuples
        # into lists of dicts.
        save_data = {}
        save_data.update(self.results)
        save_data["stats"] = {}
        for allocator in self.results["allocators"]:
            # Skip allocators without measurements
            if self.results[allocator] == {}:
                continue

            measures = []
            stats = []
            for ntuple in self.iterate_args(args=self.results["args"]):
                measures.append((ntuple._asdict(),
                                 self.results[allocator][ntuple]))

                if "stats" in self.results:
                    stats.append((ntuple._asdict(),
                                  self.results["stats"][allocator][ntuple]))

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

        print_info("Loading results from:", f)
        # TODO merge loaded result
        with open(f, "rb") as f:
            self.results = pickle.load(f)
        # Build new named tuples
        for allocator in self.results["allocators"]:
            d = {}
            for perm, measures in self.results[allocator]:
                d[self.Perm(**perm)] = measures
            self.results[allocator] = d

            d = {}
            if "stats" in self.results:
                for perm, value in self.results["stats"][allocator]:
                    d[self.Perm(**perm)] = value
                self.results["stats"][allocator] = d

        # add eventual missing statistics
        if "stats" not in self.results:
            self.calc_desc_statistics()

    def prepare(self):
        os.environ["PATH"] += f"{os.pathsep}{src.globalvars.builddir}/benchmarks/{self.name}"

        for r in self.requirements:
            exe = src.util.find_cmd(r)
            if exe is not None:
                self.results["facts"]["libcs"][r] = src.facter.libc_ver(bin=exe)
            else:
                raise Exception("Requirement: {} not found".format(r))

    def iterate_args(self, args=None):
        """Iterator over each possible combination of args"""
        if not args:
            args = self.args
        arg_names = sorted(args.keys())
        for p in itertools.product(*[args[k] for k in arg_names]):
            Perm = namedtuple("Perm", arg_names)
            yield Perm(*p)

    def iterate_args_fixed(self, fixed, args=None):
        """Iterator over each possible combination of args containing all fixed values

        self.args = {"a1": [1,2], "a2": ["foo", "bar"]}
        self.iterate_args_fixed({"a1":1}) yields [(1, "foo"), (1, "bar")
        self.iterate_args_fixed({"a2":"bar"}) yields [(1, "bar"), (2, "bar")
        self.iterate_args_fixed({"a1":2, "a2":"foo"}) yields only [(2, "foo")]"""

        for perm in self.iterate_args(args=args):
            p_dict = perm._asdict()
            is_fixed = True
            for arg in fixed:
                if p_dict[arg] != fixed[arg]:
                    is_fixed = False
                    break
            if is_fixed:
                yield perm

    def start_servers(self, env=None, alloc_name="None", alloc={"cmd_prefix": ""}):
        """Start Servers

        Servers are not allowed to deamonize because then they can't
        be terminated with their Popen object."""
        self.servers = []

        substitutions = {"alloc": alloc_name,
                         "perm": alloc_name,
                         "builddir": src.globalvars.builddir}

        substitutions.update(alloc)

        for server_cmd in self.server_cmds:
            print_info("Starting Server for", alloc_name)

            server_cmd = src.util.prefix_cmd_with_abspath(server_cmd)
            server_cmd = "{} {} {}".format(self.measure_cmd,
                                           alloc["cmd_prefix"],
                                           server_cmd)

            server_cmd = server_cmd.format(**substitutions)
            print_debug(server_cmd)

            server = subprocess.Popen(server_cmd.split(), env=env,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      universal_newlines=True)

            # TODO: check if server is up
            sleep(5)

            ret = server.poll()
            if ret is not None:
                print_debug("Stdout:", server.stdout)
                print_debug("Stderr:", server.stderr)
                raise Exception("Starting Server failed with exit code " + str(ret))
            # Register termination of the server
            atexit.register(Benchmark.terminate_subprocess, popen=server)
            self.servers.append(server)

    def shutdown_servers(self):
        print_info("Shutting down servers")
        for server in self.servers:
            Benchmark.terminate_subprocess(server)

    def run(self, runs=3):
        # check if perf is allowed on this system
        if self.measure_cmd == self.defaults["measure_cmd"]:
            if Benchmark.perf_allowed is None:
                print_info("Check if you are allowed to use perf ...")
                res = subprocess.run(["perf", "stat", "ls"],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True)

                if res.returncode != 0:
                    print_error("Test perf run failed with:")
                    print_debug(res.stderr)
                    Benchmark.perf_allowed = False
                else:
                    Benchmark.perf_allowed = True

            if not Benchmark.perf_allowed:
                raise Exception("You don't have the needed permissions to use perf")

        # save one valid result to expand invalid results
        valid_result = {}

        n = len(list(self.iterate_args())) * len(self.allocators)
        for run in range(1, runs + 1):
            print_status(run, ". run", sep='')

            i = 0
            for alloc_name, alloc in self.allocators.items():
                if alloc_name not in self.results:
                    self.results[alloc_name] = {}

                env = dict(os.environ)
                env["LD_PRELOAD"] = env.get("LD_PRELOAD", "")
                env["LD_PRELOAD"] += " " + f"{src.globalvars.builddir}/print_status_on_exit.so"
                env["LD_PRELOAD"] += " " + alloc["LD_PRELOAD"]

                if "LD_LIBRARY_PATH" in alloc:
                    env["LD_LIBRARY_PATH"] = env.get("LD_LIBRARY_PATH", "")
                    env["LD_LIBRARY_PATH"] += ":" + alloc["LD_LIBRARY_PATH"]

                self.start_servers(alloc_name=alloc_name, alloc=alloc, env=env)

                # Preallocator hook
                if hasattr(self, "preallocator_hook"):
                    self.preallocator_hook((alloc_name, alloc), run, env,
                                           verbose=src.globalvars.verbosity)

                # Run benchmark for alloc
                for perm in self.iterate_args():
                    i += 1
                    print_info0(i, "of", n, "\r", end='')

                    # Available substitutions in cmd
                    substitutions = {"run": run}
                    substitutions.update(perm._asdict())
                    substitutions["perm"] = ("{}-"*(len(perm)-1) + "{}").format(*perm)
                    substitutions.update(alloc)

                    cmd_argv = self.cmd.format(**substitutions)
                    cmd_argv = src.util.prefix_cmd_with_abspath(cmd_argv).split()
                    argv = []

                    # Prepend cmd if we are not measuring servers
                    if self.server_cmds == []:
                        prefix_argv = alloc["cmd_prefix"].format(**substitutions).split()
                        if self.measure_cmd != "":
                            measure_argv = self.measure_cmd.format(**substitutions)
                            measure_argv = src.util.prefix_cmd_with_abspath(measure_argv).split()

                            argv.extend(measure_argv)

                        argv.extend([f"{src.globalvars.builddir}/exec", "-p", env["LD_PRELOAD"]])
                        if alloc["LD_LIBRARY_PATH"] != "":
                            argv.extend(["-l", env["LD_LIBRARY_PATH"]])

                        argv.extend(prefix_argv)

                    argv.extend(cmd_argv)

                    cwd = os.getcwd()
                    if hasattr(self, "run_dir"):
                        run_dir = self.run_dir.format(**substitutions)
                        os.chdir(run_dir)
                        print_debug("\nChange cwd to:", run_dir)

                    print_debug("\nCmd:", argv)
                    res = subprocess.run(argv, stderr=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)

                    result = {}

                    if res.returncode != 0 or "ERROR: ld.so" in res.stderr:
                        print()
                        print_debug("Stdout:\n" + res.stdout)
                        print_debug("Stderr:\n" + res.stderr)
                        if res.returncode != 0:
                            print_error("{} failed with exit code {} for {}".format(argv, res.returncode, alloc_name))
                        else:
                            print_error("Preloading of {} failed for {}".format(alloc["LD_PRELOAD"], alloc_name))

                    # parse and store results
                    else:
                        if self.server_cmds == []:
                            if os.path.isfile("status"):
                                # Read VmHWM from status file. If our benchmark
                                # didn't fork the first occurance of VmHWM is from
                                # our benchmark
                                with open("status", "r") as f:
                                    for l in f.readlines():
                                        if l.startswith("VmHWM:"):
                                            result["VmHWM"] = l.split()[1]
                                            break
                                os.remove("status")
                        # TODO: get VmHWM from servers
                        else:
                            result["server_status"] = []
                            for server in self.servers:
                                with open("/proc/{}/status".format(server.pid), "r") as f:
                                    result["server_status"].append(f.read())

                        # parse perf output if available
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
                        if valid_result is not None:
                            valid_result = result

                    if perm not in self.results[alloc_name]:
                        self.results[alloc_name][perm] = []
                    self.results[alloc_name][perm].append(result)

                    if os.getcwd() != cwd:
                        os.chdir(cwd)

                self.shutdown_servers()

                if hasattr(self, "postallocator_hook"):
                    self.postallocator_hook((alloc_name, alloc), run,
                                            verbose=src.globalvars.verbosity)

            print()

        # reset PATH
        os.environ["PATH"] = os.environ["PATH"].replace(f"{os.pathsep}{src.globalvars.builddir}/benchmarks/{self.name}", "")


        # expand invalid results
        if valid_result != {}:
            for allocator in self.allocators:
                for perm in self.iterate_args():
                    for i, m in enumerate(self.results[allocator][perm]):
                        if m == {}:
                            self.results[allocator][perm][i] = {k: np.NaN for k in valid_result}

        self.calc_desc_statistics()

    def calc_desc_statistics(self):
        allocs = self.results["allocators"]
        self.results["stats"] = {}
        for alloc in allocs:
            # Skip allocators without measurements
            if self.results[alloc] == {}:
                continue

            self.results["stats"][alloc] = {}

            for perm in self.iterate_args(self.results["args"]):
                stats = {s: {} for s in ["min", "max", "mean", "median", "std",
                                         "std_perc",
                                         "lower_quartile", "upper_quartile",
                                         "lower_whisker", "upper_whisker",
                                         "outliers"]}
                for dp in self.results[alloc][perm][0]:
                    try:
                        data = [float(m[dp]) for m in self.results[alloc][perm]]
                    except (TypeError, ValueError) as e:
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
                    stats["lower_whisker"][dp] = stats["lower_quartile"][dp] - trimmed_range
                    stats["upper_whisker"][dp] = stats["upper_quartile"][dp] + trimmed_range
                    outliers = []
                    for d in data:
                        if d > stats["upper_whisker"][dp] or d < stats["lower_whisker"][dp]:
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

    def export_facts_to_file(self, comment_symbol, f):
        """Write collected facts about used system and benchmark to file"""
        print(comment_symbol, self.name, file=f)
        print(file=f)
        print(comment_symbol, "Common facts:", file=f)
        for k, v in src.globalvars.facts.items():
            print(comment_symbol, k + ":", v, file=f)
        print(file=f)
        print(comment_symbol, "Benchmark facts:", file=f)
        for k, v in self.results["facts"].items():
            print(comment_symbol, k + ":", v, file=f)
        print(file=f)

    def export_stats_to_csv(self, datapoint, path=None):
        """Write descriptive statistics about datapoint to csv file"""
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
                    if field_len > widths[i]:
                        widths[i] = field_len

        with open(path, "w") as f:
            headerline = ""
            for i, h in enumerate(fieldnames):
                headerline += h.capitalize().ljust(widths[i]).replace("_", "-")
            print(headerline, file=f)

            for alloc in allocators:
                for perm in self.iterate_args(args=args):
                    line = ""
                    for i, x in enumerate(rows[alloc][perm]):
                        line += str(x).ljust(widths[i])
                    print(line.replace("_", "-"), file=f)

    def export_stats_to_dataref(self, datapoint, path=None):
        """Write descriptive statistics about datapoint to dataref file"""
        stats = self.results["stats"]

        if path is None:
            path = datapoint

        path = path + ".dataref"

        # Example: \drefset{/mysql/glibc/40/Lower-whisker}{71552.0}
        line = "\\drefset{{/{}/{}/{}/{}}}{{{}}}"

        with open(path, "w") as f:
            # Write facts to file
            self.export_facts_to_file("%", f)

            for alloc in self.results["allocators"]:
                for perm in self.iterate_args(args=self.results["args"]):
                    for statistic, values in stats[alloc][perm].items():
                        cur_line = line.format(self.name, alloc,
                                         "/".join([str(p) for p in list(perm)]),
                                         statistic, values[datapoint])
                        # Replace empty outliers
                        cur_line.replace("[]", "")
                        # Replace underscores
                        cur_line.replace("_", "-")
                        print(cur_line, file=f)

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
