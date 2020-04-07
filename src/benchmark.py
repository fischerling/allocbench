# Copyright 2018-2020 Florian Fischer <florian.fl.fischer@fau.de>
#
# This file is part of allocbench.
#
# allocbench is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# allocbench is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with allocbench.  If not, see <http://www.gnu.org/licenses/>.
"""Benchmark class providing general purpose implementation of required methods"""

import atexit
from collections import namedtuple
import errno
import copy
import csv
import itertools
import multiprocessing
import os
import subprocess
from time import sleep
import traceback

import numpy as np

import src.globalvars
import src.util
from src.util import print_status, print_error, print_warn
from src.util import print_info0, print_info, print_debug


class Benchmark:
    """Default implementation of most methods allocbench expects from a benchmark"""

    # class member to remember if we are allowed to use perf
    perf_allowed = None

    cmd = "false"
    args = {}
    measure_cmd_csv = False
    measure_cmd = "perf stat -x, -d"
    servers = []
    allocators = copy.deepcopy(src.globalvars.allocators)

    @staticmethod
    def terminate_subprocess(proc, timeout=5):
        """Terminate or kill a Popen object"""

        # Skip already terminated subprocess
        if proc.poll() is not None:
            return proc.communicate()

        print_info("Terminating subprocess", proc.args)
        proc.terminate()
        try:
            outs, errs = proc.communicate(timeout=timeout)
            print_info("Subprocess exited with ", proc.returncode)
        except subprocess.TimeoutExpired:
            print_error("Killing subprocess ", proc.args)
            proc.kill()
            outs, errs = proc.communicate()

        print_debug("Server Out:", outs)
        print_debug("Server Err:", errs)
        return outs, errs

    @staticmethod
    def scale_threads_for_cpus(factor=1, min_threads=1, steps=10):
        """Helper to scale thread count to execution units

        Return a list of numbers between start and multiprocessing.cpu_count() * factor
        with len <= steps."""
        max_threads = int(multiprocessing.cpu_count() * factor)

        if steps > max_threads - min_threads + 1:
            return list(range(min_threads, int(max_threads) + 1))

        nthreads = []
        divider = 2
        while True:
            factor = max_threads // divider
            entries = max_threads // factor
            if entries > steps - 1:
                return sorted(list(set([min_threads] + nthreads + [max_threads])))

            nthreads = [int((i + 1) * factor) for i in range(int(entries))]
            divider *= 2

    @staticmethod
    def is_perf_allowed():
        """raise an exception if perf is not allowed on this system"""
        if Benchmark.perf_allowed is None:
            print_info("Check if you are allowed to use perf ...")
            res = subprocess.run(["perf", "stat", "ls"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)

            if res.returncode != 0:
                print_error(f"Test perf run failed with exit status: {res.returncode}")
                print_debug(res.stderr)
                Benchmark.perf_allowed = False
            else:
                Benchmark.perf_allowed = True

        if not Benchmark.perf_allowed:
            raise Exception("You don't have the needed permissions to use perf")

    def __str__(self):
        return self.name

    def __init__(self, name):
        """Initialize a benchmark with default members if they aren't set already"""
        self.name = name

        # Set result_dir
        if not hasattr(self, "result_dir"):
            self.result_dir = os.path.abspath(os.path.join(src.globalvars.resdir or "",
                                                           self.name))
        # Set build_dir
        if not hasattr(self, "build_dir"):
            self.build_dir = os.path.abspath(os.path.join(src.globalvars.builddir,
                                                          "benchmarks", self.name))

        self.Perm = namedtuple("Perm", self.args.keys())

        default_results = {"args": self.args,
                           "allocators": self.allocators,
                           "facts": {"libcs": {},
                                     "versions": {}}}
        default_results.update({alloc: {} for alloc in self.allocators})

        if not hasattr(self, "results"):
            self.results = default_results
        # Add default default entrys to self.results if their key is absent
        else:
            for key, default in default_results.items():
                if key not in self.results:
                    self.results[key] = default

        if self.servers:
            self.results["servers"] = {}

        if not hasattr(self, "requirements"):
            self.requirements = []

        print_debug("Creating benchmark", self.name)
        print_debug("Cmd:", self.cmd)
        print_debug("Args:", self.args)
        print_debug("Servers:", self.servers)
        print_debug("Requirements:", self.requirements)
        print_debug("Results dictionary:", self.results)
        print_debug("Results directory:", self.result_dir)

    def save(self, path=None):
        """Save benchmark results to a json file"""
        import json
        if not path:
            path = self.name + ".json"
        elif os.path.isdir(path):
            path = os.path.join(path, self.name + ".json")

        print_info(f"Saving results to: {path}")
        # JSON can't handle namedtuples so convert the dicts of namedtuples
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

        with open(path, "w") as f:
            json.dump(save_data, f)

    def load(self, path=None):
        """Load benchmark results from file"""
        if not path:
            filename = self.name
        else:
            if os.path.isdir(path):
                filename = os.path.join(path, self.name)
            else:
                filename = os.path.splitext(path)

        if os.path.exists(filename + ".json"):
            import json
            filename += ".json"
            with open(filename, "r") as f:
                self.results = json.load(f)
        elif os.path.exists(filename + ".save"):
            import pickle
            filename += ".save"
            with open(filename, "rb") as f:
                self.results = pickle.load(f)
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        print_info(f"Loading results from: {filename}")

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
        """default prepare implementation raising an error if a requirement is not found"""
        os.environ["PATH"] += f"{os.pathsep}{src.globalvars.builddir}/benchmarks/{self.name}"

        for r in self.requirements:
            exe = src.util.find_cmd(r)
            if exe is not None:
                self.results["facts"]["libcs"][r] = src.facter.libc_ver(executable=exe)
            else:
                raise Exception("Requirement: {} not found".format(r))

    def iterate_args(self, args=None, fixed=None):
        """Iterator over each possible combination of args

        Parameters
        ----------
        args : dict, optional, default=None
            Dictionary of arguments and iterables with their possible values.
            If not provided defaults to :rc:`self.args`

        fixed : dict, optional, default=None
            Mapping of arguments to one of their values. The yielded result
            contains this value. If not provided defaults to :rc:`{}`.

        Returns
        -------
        perm : :rc:`self.Perm`
            A namedtuple containing one permutation of the benchmark's arguments.

        Examples
        --------
        args = {"a1": [1,2], "a2": ["foo", "bar"]}

        self.iterate_args(args=args) yields [(1, "foo"), (2, "foo"), (1, "bar"), (2,"bar")]
        self.iterate_args(args, {"a2":"bar"}) yields [(1, "bar"), (2, "bar")]
        self.iterate_args(args, {"a1":2, "a2":"foo"}) yields [(2, "foo")]"""
        if not args:
            args = self.args
        if not fixed:
            fixed = {}

        for perm in itertools.product(*[args[k] for k in args]):
            perm = self.Perm(*perm)
            p_dict = perm._asdict()
            is_fixed = True
            for arg in fixed:
                if p_dict[arg] != fixed[arg]:
                    is_fixed = False
                    break

            if is_fixed:
                yield perm

    def prepare_argv(self, cmd, env={}, alloc={}, substitutions={}, prepend=True):
        """Prepare an complete argv list for benchmarking"""
        argv = []
        if prepend:
            if "cmd_prefix" in alloc:
                prefix_argv = alloc["cmd_prefix"].format(**substitutions).split()
                argv.extend(prefix_argv)
                # add exec wrapper so that a possible prefixed loader can execute shell scripts
                argv.append(f"{src.globalvars.builddir}/exec")

            if self.measure_cmd != "":
                measure_argv = self.measure_cmd.format(**substitutions)
                measure_argv = src.util.prefix_cmd_with_abspath(measure_argv).split()
                argv.extend(measure_argv)

            argv.append(f"{src.globalvars.builddir}/exec")

            ld_preload = f"{src.globalvars.builddir}/print_status_on_exit.so"
            ld_preload += f" {src.globalvars.builddir}/sig_handlers.so"

            if "LD_PRELOAD" in env or alloc.get("LD_PRELOAD", ""):
                ld_preload += f" {alloc.get('LD_PRELOAD', '')}"
                ld_preload += " " + env.get('LD_PRELOAD', '')

            argv.extend(["-p", ld_preload])

            if "LD_LIBRARY_PATH" in env or alloc.get("LD_LIBRARY_PATH", ""):
                argv.extend(["-l", f"{alloc.get('LD_LIBRARY_PATH', '')} {env.get('LD_LIBRARY_PATH', '')}"])

        cmd_argv = cmd.format(**substitutions)
        cmd_argv = src.util.prefix_cmd_with_abspath(cmd_argv).split()

        argv.extend(cmd_argv)

        return argv

    def start_servers(self, env={}, alloc_name="None", alloc={"cmd_prefix": ""}):
        """Start Servers

        Servers are not allowed to deamonize because then they can't
        be terminated using their Popen object."""

        substitutions = {"alloc": alloc_name,
                         "perm": alloc_name,
                         "builddir": src.globalvars.builddir}

        substitutions.update(self.__dict__)
        substitutions.update(alloc)

        for server in self.servers:
            server_name = server.get("name", "Server")
            print_info(f"Starting {server_name} for {alloc_name}")

            argv = self.prepare_argv(server["cmd"], env, alloc, substitutions)
            print_debug(argv)

            proc = subprocess.Popen(argv, env=env,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)

            # TODO: check if server is up
            sleep(5)

            ret = proc.poll()
            if ret is not None:
                print_debug("Stdout:", proc.stdout.read())
                print_debug("Stderr:", proc.stderr.read())
                raise Exception(f"Starting {server_name} failed with exit code: {ret}")
            server["popen"] = proc
            # Register termination of the server
            atexit.register(Benchmark.shutdown_server, self=self, server=server)

            self.results["servers"].setdefault(alloc_name, {s["name"]: {"stdout": [], "stderr": []} for s in self.servers})

            if not "prepare_cmds" in server:
                continue

            print_info(f"Preparing {server_name}")
            for prep_cmd in server["prepare_cmds"]:
                prep_cmd = prep_cmd.format(**substitutions)
                print_debug(prep_cmd)

                proc = subprocess.run(prep_cmd.split(), universal_newlines=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                print_debug("Stdout:", proc.stdout)
                print_debug("Stderr:", proc.stderr)


    def shutdown_server(self, server):
        """Terminate a started server running its shutdown_cmds in advance"""
        if server["popen"].poll() != None:
            return

        server_name = server.get("name", "Server")
        print_info(f"Shutting down {server_name}")

        substitutions = {}
        substitutions.update(self.__dict__)
        substitutions.update(server)

        if "shutdown_cmds" in server:
            for shutdown_cmd in server["shutdown_cmds"]:
                shutdown_cmd = shutdown_cmd.format(**substitutions)
                print_debug(shutdown_cmd)

                proc = subprocess.run(shutdown_cmd.split(), universal_newlines=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                print_debug("Stdout:", proc.stdout)
                print_debug("Stderr:", proc.stderr)

            # wait for server termination
            sleep(5)

        outs, errs = Benchmark.terminate_subprocess(server["popen"])
        server["stdout"] = outs
        server["stderr"] = errs

    def shutdown_servers(self):
        """Terminate all started servers"""
        print_info("Shutting down servers")
        for server in self.servers:
            self.shutdown_server(server)

    def run(self, runs=3):
        """generic run implementation"""

        # check if we are allowed to use perf
        if self.measure_cmd.startswith("perf"):
            Benchmark.is_perf_allowed()

        # add benchmark dir to PATH
        os.environ["PATH"] += f"{os.pathsep}{src.globalvars.builddir}/benchmarks/{self.name}"

        # save one valid result to expand invalid results
        valid_result = {}

        self.results["facts"]["runs"] = runs

        n = len(list(self.iterate_args())) * len(self.allocators)
        for run in range(1, runs + 1):
            print_status(run, ". run", sep='')

            i = 0
            for alloc_name, alloc in self.allocators.items():
                if alloc_name not in self.results:
                    self.results[alloc_name] = {}

                skip = False
                try:
                    self.start_servers(alloc_name=alloc_name, alloc=alloc, env=os.environ)
                except Exception as e:
                    print_debug(traceback.format_exc())
                    print_error(e)
                    print_error("Skipping", alloc_name)
                    skip = True

                # Preallocator hook
                if hasattr(self, "preallocator_hook"):
                    self.preallocator_hook((alloc_name, alloc), run, os.environ)

                # Run benchmark for alloc
                for perm in self.iterate_args():
                    i += 1

                    # create new result entry
                    if perm not in self.results[alloc_name]:
                        self.results[alloc_name][perm] = []

                    # starting the server failed -> add empty result and continue
                    if skip:
                        self.results[alloc_name][perm].append({})
                        continue

                    print_info0(i, "of", n, "\r", end='')

                    # Available substitutions in cmd
                    substitutions = {"run": run, "alloc": alloc_name}
                    substitutions.update(self.__dict__)
                    substitutions.update(alloc)
                    if perm:
                        substitutions.update(perm._asdict())
                        substitutions["perm"] = "-".join([str(v) for v in perm])
                    else:
                        substitutions["perm"] = ""

                    # we measure the cmd -> prepare it accordingly
                    if not self.servers:
                        argv = self.prepare_argv(self.cmd, os.environ, alloc, substitutions)
                    # we measure the server -> run cmd as it is
                    else:
                        argv = self.prepare_argv(self.cmd, substitutions=substitutions, prepend=False)

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

                    if res.returncode != 0 or "ERROR: ld.so" in res.stderr or "Segmentation fault" in res.stderr or "Aborted" in res.stderr:
                        print()
                        print_debug("Stdout:\n" + res.stdout)
                        print_debug("Stderr:\n" + res.stderr)
                        if res.returncode != 0:
                            print_error(f"{argv} failed with exit code {res.returncode} for {alloc_name}")
                        elif "ERROR: ld.so" in res.stderr:
                            print_error(f"Preloading of {alloc['LD_PRELOAD']} failed for {alloc_name}")
                        else:
                            print_error(f"{argv} terminated abnormally")

                    # parse and store results
                    else:
                        if not self.servers:
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

                            # parse perf output if available
                            if self.measure_cmd == Benchmark.measure_cmd or self.measure_cmd_csv:
                                csvreader = csv.reader(res.stderr.splitlines(),
                                                       delimiter=',')
                                for row in csvreader:
                                    # Split of the user/kernel space info to be better portable
                                    try:
                                        result[row[2].split(":")[0]] = row[0]
                                    except Exception as e:
                                        print_warn("Exception", e, "occured on", row, "for",
                                                   alloc_name, "and", perm)
                        else:
                            result["server_status"] = []
                            for server in self.servers:
                                with open(f"/proc/{server['popen'].pid}/status", "r") as f:
                                    server_status = f.read()
                                    result["server_status"].append(server_status)

                                    for l in server_status.splitlines():
                                        if l.startswith("VmHWM:"):
                                            result[f"{server.get('name', 'Server')}_vmhwm"] = l.split()[1]
                                            break


                        if hasattr(self, "process_output"):
                            self.process_output(result, res.stdout, res.stderr,
                                                alloc_name, perm)


                        # save a valid result so we can expand invalid ones
                        if valid_result is None:
                            valid_result = result

                    self.results[alloc_name][perm].append(result)

                    if os.getcwd() != cwd:
                        os.chdir(cwd)

                if self.servers != [] and not skip:
                    self.shutdown_servers()

                    for server in self.servers:
                        self.results["servers"][alloc_name][server['name']]["stdout"].append(server["stdout"])
                        self.results["servers"][alloc_name][server['name']]["stderr"].append(server["stderr"])

                if hasattr(self, "postallocator_hook"):
                    self.postallocator_hook((alloc_name, alloc), run)

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
        """Calculate descriptive statistics for each datapoint"""
        allocs = self.results["allocators"]
        self.results["stats"] = {}
        for alloc in allocs:
            # Skip allocators without measurements
            if self.results[alloc] == {}:
                continue

            self.results["stats"][alloc] = {}

            for perm in self.iterate_args(args=self.results["args"]):
                stats = {s: {} for s in ["min", "max", "mean", "median", "std",
                                         "std_perc",
                                         "lower_quartile", "upper_quartile",
                                         "lower_whisker", "upper_whisker",
                                         "outliers"]}
                for dp in self.results[alloc][perm][0]:
                    try:
                        data = [float(m[dp]) for m in self.results[alloc][perm]]
                    except (TypeError, ValueError) as e:
                        print_debug(dp, e)
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
