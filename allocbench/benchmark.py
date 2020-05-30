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
import importlib
import itertools
import json
import multiprocessing
import os
import subprocess
from time import sleep
import traceback

import numpy as np

import allocbench.facter as facter
import allocbench.globalvars
from allocbench.util import print_status, print_error, print_warn
from allocbench.util import print_info0, print_info, print_debug
from allocbench.util import find_cmd, prefix_cmd_with_abspath, run_cmd


class Benchmark:
    """Default implementation of most methods allocbench expects from a benchmark"""

    # class member to remember if we are allowed to use perf
    perf_allowed = None

    cmd = "false"
    args = {}
    measure_cmd_csv = False
    measure_cmd = "perf stat -x, -d"
    servers = []

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
                return sorted(
                    list(set([min_threads] + nthreads + [max_threads])))

            nthreads = [int((i + 1) * factor) for i in range(int(entries))]
            divider *= 2

    @staticmethod
    def is_perf_allowed():
        """raise an exception if perf is not allowed on this system"""
        if Benchmark.perf_allowed is None:
            print_info("Check if you are allowed to use perf ...")
            try:
                run_cmd(["perf", "stat", "ls"], capture=True)
                Benchmark.perf_allowed = True
            except subprocess.CalledProcessError as err:
                print_error(
                    f"Test perf run failed with exit status: {err.returncode}")
                print_debug(err.stderr)
                Benchmark.perf_allowed = False

        if not Benchmark.perf_allowed:
            raise Exception(
                "You don't have the needed permissions to use perf")

    @staticmethod
    def save_values_from_proc_status(result,
                                     keys,
                                     status_file="status",
                                     status_content=None,
                                     key_prefix=""):
        """Parse a /proc/status file or its content and extract requested keys from it"""
        assert status_file or status_content

        if status_content is None:
            if hasattr(status_file, "read"):
                status_content = status_file.read()
            else:
                with open(status_file, "r") as opened_status_file:
                    status_content = opened_status_file.read()

        for line in status_content.splitlines():
            key, value = line.split(':')
            value = value.replace("kB", "")
            value = value.strip()

            if key in keys:
                result[f"{key_prefix}{key}"] = value

    @staticmethod
    def save_server_status_and_values(result, server, keys):
        """Read, save and extract values from a server process /proc/status file

        The whole status is stored in result with the key {server.name}_status
        and every extracted key in keys is stored as {server.name}_{key}.
        """
        with open(f"/proc/{server['popen'].pid}/status", "r") as status_file:
            server_name = server.get('name', 'Server')
            server_status = status_file.read()
            result[f"{server_name}_status"] = server_status

            Benchmark.save_values_from_proc_status(
                result, keys, status_content=server_status)

    @staticmethod
    def parse_and_save_perf_output(result, output, alloc_name, perm):
        """Parse and store csv output from perf -x,"""
        csvreader = csv.reader(output.splitlines(), delimiter=',')
        for row in csvreader:
            try:
                # Split of the user/kernel space info to be better portable
                datapoint = row[2].split(":")[0]
                value = row[0]
                result[datapoint] = value
            except IndexError as err:
                print_warn(
                    f"Exception {err} occured on {row} for {alloc_name} and {perm}"
                )

    def __str__(self):
        return self.name

    def __init__(self, name):
        """Initialize a benchmark with default members if they aren't set already"""
        self.name = name

        self.allocators = copy.deepcopy(allocbench.globalvars.ALLOCATORS)

        # Set result_dir
        if not hasattr(self, "result_dir"):
            self.result_dir = os.path.abspath(
                os.path.join(allocbench.globalvars.RESDIR or "", self.name))
        # Set build_dir
        if not hasattr(self, "build_dir"):
            self.build_dir = os.path.abspath(
                os.path.join(allocbench.globalvars.BUILDDIR, "benchmarks",
                             self.name))

        self.Perm = namedtuple("Perm", self.args.keys())

        default_results = {
            "args": self.args,
            "allocators": self.allocators,
            "facts": {
                "libcs": {},
                "versions": {}
            }
        }
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

    def prepare(self):
        self.check_requirements()

    def save(self, path=None):
        """Save benchmark results to a json file"""
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
                measures.append(
                    (ntuple._asdict(), self.results[allocator][ntuple]))

                if "stats" in self.results:
                    stats.append((ntuple._asdict(),
                                  self.results["stats"][allocator][ntuple]))

            save_data[allocator] = measures
            if "stats" in self.results:
                save_data["stats"][allocator] = stats

        with open(path, "w") as save_file:
            json.dump(save_data, save_file)

    def load(self, path=None):
        """Load benchmark results from file"""
        if not path:
            filename = f"{self.name}.json"
        elif os.path.isdir(path):
            filename = os.path.join(path, self.name)

        if os.path.exists(filename):
            with open(filename, "r") as load_file:
                self.results = json.load(load_file)
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                                    filename)

        print_info(f"Loading results from: {filename}")

        # Build new named tuples
        for allocator in self.results["allocators"]:
            data = {}
            for perm, measures in self.results[allocator]:
                data[self.Perm(**perm)] = measures
            self.results[allocator] = data

            stats = {}
            if "stats" in self.results:
                for perm, value in self.results["stats"][allocator]:
                    stats[self.Perm(**perm)] = value
                self.results["stats"][allocator] = stats

        # add eventual missing statistics
        if "stats" not in self.results:
            self.calc_desc_statistics()

    def check_requirements(self):
        """raise an error if a requirement is not found"""
        os.environ[
            "PATH"] += f"{os.pathsep}{allocbench.globalvars.BUILDDIR}/benchmarks/{self.name}"

        for requirement in self.requirements:
            exe = find_cmd(requirement)
            if exe is not None:
                self.results["facts"]["libcs"][requirement] = facter.libc_ver(
                    executable=exe)
            else:
                raise Exception(
                    "Requirement: {} not found".format(requirement))

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

    def prepare_argv(self,
                     cmd,
                     env=None,
                     alloc=None,
                     substitutions=None,
                     prepend=True):
        """Prepare an complete argv list for benchmarking"""
        if env is None:
            env = {}
        if alloc is None:
            alloc = {}
        if substitutions is None:
            substitutions = {}

        argv = []
        if prepend:
            if "cmd_prefix" in alloc:
                prefix_argv = alloc["cmd_prefix"].format(
                    **substitutions).split()
                argv.extend(prefix_argv)
                # add exec wrapper so that a possible prefixed loader can execute shell scripts
                argv.append(f"{allocbench.globalvars.BUILDDIR}/exec")

            if self.measure_cmd != "":
                measure_argv = self.measure_cmd.format(**substitutions)
                measure_argv = prefix_cmd_with_abspath(measure_argv).split()
                argv.extend(measure_argv)

            argv.append(f"{allocbench.globalvars.BUILDDIR}/exec")

            ld_preload = f"{allocbench.globalvars.BUILDDIR}/print_status_on_exit.so"
            ld_preload += f" {allocbench.globalvars.BUILDDIR}/sig_handlers.so"

            if "LD_PRELOAD" in env or alloc.get("LD_PRELOAD", ""):
                ld_preload += f" {alloc.get('LD_PRELOAD', '')}"
                ld_preload += " " + env.get('LD_PRELOAD', '')

            argv.extend(["-p", ld_preload])

            if "LD_LIBRARY_PATH" in env or alloc.get("LD_LIBRARY_PATH", ""):
                old_ld_lib_path = env.get('LD_LIBRARY_PATH', '')
                ld_lib_path = alloc.get('LD_LIBRARY_PATH', '')
                argv.extend(["-l", f"{ld_lib_path} {old_ld_lib_path}"])

        cmd_expanded = cmd.format(**substitutions)
        cmd_argv = prefix_cmd_with_abspath(cmd_expanded).split()

        argv.extend(cmd_argv)

        return argv

    def start_servers(self, env=None, alloc_name="None", alloc=None):
        """Start Servers

        Servers are not allowed to deamonize because then they can't
        be terminated using their Popen object."""

        if env is None:
            env = {}

        if alloc is None:
            alloc = {"cmd_prefix": ""}

        substitutions = {
            "alloc": alloc_name,
            "perm": alloc_name,
            "builddir": allocbench.globalvars.BUILDDIR
        }

        substitutions.update(self.__dict__)
        substitutions.update(alloc)

        for server in self.servers:
            server_name = server.get("name", "Server")
            print_info(f"Starting {server_name} for {alloc_name}")

            argv = self.prepare_argv(server["cmd"], env, alloc, substitutions)
            print_debug(argv)

            proc = subprocess.Popen(argv,
                                    env=env,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True)

            # TODO: check if server is up
            sleep(5)

            ret = proc.poll()
            if ret is not None:
                print_debug("Stdout:", proc.stdout.read())
                print_debug("Stderr:", proc.stderr.read())
                raise Exception(
                    f"Starting {server_name} failed with exit code: {ret}")
            server["popen"] = proc
            # Register termination of the server
            atexit.register(Benchmark.shutdown_server,
                            self=self,
                            server=server)

            self.results["servers"].setdefault(
                alloc_name, {
                    s["name"]: {
                        "stdout": [],
                        "stderr": [],
                        "returncode": []
                    }
                    for s in self.servers
                })

            if not "prepare_cmds" in server:
                continue

            print_info(f"Preparing {server_name}")
            for prep_cmd in server["prepare_cmds"]:
                prep_cmd = prep_cmd.format(**substitutions)

                proc = run_cmd(prep_cmd.split(), output_verbosity=3)

    def shutdown_server(self, server):
        """Terminate a started server running its shutdown_cmds in advance"""
        if server["popen"].poll() is None:
            server_name = server.get("name", "Server")
            print_info(f"Shutting down {server_name}")

            substitutions = {}
            substitutions.update(self.__dict__)
            substitutions.update(server)

            if "shutdown_cmds" in server:
                for shutdown_cmd in server["shutdown_cmds"]:
                    shutdown_cmd = shutdown_cmd.format(**substitutions)

                    run_cmd(shutdown_cmd.split(), output_verbosity=3)

                # wait for server termination
                sleep(5)

            outs, errs = Benchmark.terminate_subprocess(server["popen"])
        else:
            outs, errs = "", ""
            if not server["popen"].stdout.closed:
                outs = server["popen"].stdout.read()
            if not server["popen"].stderr.closed:
                errs = server["popen"].stderr.read()

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
        os.environ[
            "PATH"] += f"{os.pathsep}{allocbench.globalvars.BUILDDIR}/benchmarks/{self.name}"

        # save one valid result to expand invalid results
        valid_result = {}

        self.results["facts"]["runs"] = runs

        total_executions = len(list(self.iterate_args())) * len(
            self.allocators)
        for run in range(1, runs + 1):
            print_status(run, ". run", sep='')

            i = 0
            for alloc_name, alloc in self.allocators.items():
                if alloc_name not in self.results:
                    self.results[alloc_name] = {}

                skip = False
                try:
                    self.start_servers(alloc_name=alloc_name,
                                       alloc=alloc,
                                       env=os.environ)
                except Exception as err:
                    print_debug(traceback.format_exc())
                    print_error(err)
                    print_error("Skipping", alloc_name)
                    skip = True

                # Preallocator hook
                if hasattr(self, "preallocator_hook"):
                    self.preallocator_hook(
                        (alloc_name, alloc),
                        run,  # pylint: disable=no-member
                        os.environ)

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

                    print_info0(i, "of", total_executions, "\r", end='')

                    # Available substitutions in cmd
                    substitutions = {"run": run, "alloc": alloc_name}
                    substitutions.update(self.__dict__)
                    substitutions.update(alloc)
                    if perm:
                        substitutions.update(perm._asdict())
                        substitutions["perm"] = "-".join(
                            [str(v) for v in perm])
                    else:
                        substitutions["perm"] = ""

                    # we measure the cmd -> prepare it accordingly
                    if not self.servers:
                        argv = self.prepare_argv(self.cmd, os.environ, alloc,
                                                 substitutions)
                    # we measure the server -> run cmd as it is
                    else:
                        argv = self.prepare_argv(self.cmd,
                                                 substitutions=substitutions,
                                                 prepend=False)

                    cwd = os.getcwd()
                    if hasattr(self, "run_dir"):
                        run_dir = self.run_dir.format(**substitutions)  # pylint: disable=no-member
                        os.chdir(run_dir)
                        print_debug("\nChange cwd to:", run_dir)

                    try:
                        res = run_cmd(argv, capture=True)
                    except subprocess.CalledProcessError as err:
                        res = err

                    result = {}

                    if (res.returncode != 0 or "ERROR: ld.so" in res.stderr
                            or "Segmentation fault" in res.stderr
                            or "Aborted" in res.stderr):
                        print()
                        print_debug("Stdout:\n" + res.stdout)
                        print_debug("Stderr:\n" + res.stderr)
                        if res.returncode != 0:
                            print_error(
                                f"{argv} failed with exit code {res.returncode} for {alloc_name}"
                            )
                        elif "ERROR: ld.so" in res.stderr:
                            print_error(
                                f"Preloading of {alloc['LD_PRELOAD']} failed for {alloc_name}"
                            )
                        else:
                            print_error(f"{argv} terminated abnormally")

                    # parse and store results
                    else:
                        if self.servers:
                            for server in self.servers:
                                Benchmark.save_server_status_and_values(
                                    result, server, ["VmHWM"])
                        else:
                            if os.path.isfile("status"):
                                # Read VmHWM from status file. If our benchmark
                                # didn't fork the first occurance of VmHWM is from
                                # our benchmark
                                Benchmark.save_values_from_proc_status(
                                    result, ["VmHWM"])
                                os.remove("status")

                            # parse perf output if available
                            if self.measure_cmd == Benchmark.measure_cmd or self.measure_cmd_csv:
                                Benchmark.parse_and_save_perf_output(
                                    result, res.stderr, alloc_name, perm)

                        if hasattr(self, "process_output"):  # pylint: disable=no-member
                            self.process_output(result, res.stdout, res.stderr,
                                                alloc_name, perm)

                        # save a valid result so we can expand invalid ones
                        if valid_result is None:
                            valid_result = result

                    print_debug(f"Resulting in: {result}")
                    self.results[alloc_name][perm].append(result)

                    if os.getcwd() != cwd:
                        os.chdir(cwd)

                if self.servers != [] and not skip:
                    self.shutdown_servers()

                    for server in self.servers:
                        server_result = self.results["servers"][alloc_name][
                            server['name']]
                        server_result["stdout"].append(server["stdout"])
                        server_result["stderr"].append(server["stderr"])
                        server_result["returncode"].append(
                            server["popen"].returncode)

                if hasattr(self, "postallocator_hook"):
                    self.postallocator_hook((alloc_name, alloc), run)  # pylint: disable=no-member

            print()

        # reset PATH
        os.environ["PATH"] = os.environ["PATH"].replace(
            f"{os.pathsep}{allocbench.globalvars.BUILDDIR}/benchmarks/{self.name}",
            "")

        # expand invalid results
        if valid_result != {}:
            for allocator in self.allocators:
                for perm in self.iterate_args():
                    for i, measure in enumerate(self.results[allocator][perm]):
                        if measure == {}:
                            self.results[allocator][perm][i] = {
                                k: np.NaN
                                for k in valid_result
                            }

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
                stats = {
                    s: {}
                    for s in [
                        "min", "max", "mean", "median", "std", "std_perc",
                        "lower_quartile", "upper_quartile", "lower_whisker",
                        "upper_whisker", "outliers"
                    ]
                }
                for key in self.results[alloc][perm][0]:
                    try:
                        data = [
                            float(m[key]) for m in self.results[alloc][perm]
                        ]
                    except (TypeError, ValueError):
                        continue
                    stats["min"][key] = np.min(data)
                    stats["max"][key] = np.max(data)
                    stats["mean"][key] = np.mean(data)
                    stats["median"][key] = np.median(data)
                    stats["std"][key] = np.std(data, ddof=1)
                    stats["std_perc"][
                        key] = stats["std"][key] / stats["mean"][key]
                    stats["lower_quartile"][key], stats["upper_quartile"][
                        key] = np.percentile(data, [25, 75])
                    trimmed_range = stats["upper_quartile"][key] - stats[
                        "lower_quartile"][key]
                    stats["lower_whisker"][
                        key] = stats["lower_quartile"][key] - trimmed_range
                    stats["upper_whisker"][
                        key] = stats["upper_quartile"][key] + trimmed_range
                    outliers = []
                    for value in data:
                        if value > stats["upper_whisker"][
                                key] or value < stats["lower_whisker"][key]:
                            outliers.append(value)
                    stats["outliers"][key] = outliers

                self.results["stats"][alloc][perm] = stats


def get_benchmark_object(benchmark_name: str) -> Benchmark:
    """Find the first Benchmark class in allocbench.benchmarks.{benchmark_name} and return an instance"""
    bench_module = importlib.import_module(
        f"allocbench.benchmarks.{benchmark_name}")
    # find Benchmark class
    for member in bench_module.__dict__.values():
        if (not isinstance(member, type) or member is Benchmark
                or not issubclass(member, Benchmark)):
            continue

        return member()
