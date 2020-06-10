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
"""sysbench SQL read-only benchmark

This benchmark is heavily inspired by a blog post from Alexey Stroganov from Percona:
https://web.archive.org/web/20190706104404/https://www.percona.com/blog/2012/07/05/impact-of-memory-allocators-on-mysql-performance/

It uses the read-only database benchmark from sysbench, a commonly used system
benchmarking tool to measure the performance of mysqld per allocator.
The read-only benchmark on a relatively small database (~1GB) is used to omit
I/O latency and be cpu-bound, maximizing the allocators influence on performance.

Behavior per allocator:
* Start mysqld using the allocator
* Run sysbench oltp_read_only once per thread count
* Shutdown mysqld

40 Thread workload:

* allocator calls: 1519226
    * malloc:       722421 (47.55%)
    * free:         795231 (52.34%)
    * calloc:         1501 (0.10%)
    * realloc:          73 (0.004%)
* Approximate allocator ratios:
    * malloc:  0.69%
    * free:    0.36%
    * calloc:  0.04%

* Top 10 allocation sizes 71.36% of all allocations
  1. 288 B occurred 112556 times
  2. 4064 B occurred 112552 times
  3. 9 B occurred 61978 times
  4. 328 B occurred 56275 times
  5. 64 B occurred 48498 times
  6. 1040 B occurred 28174 times
  7. 360 B occurred 28140 times
  8. 65544 B occurred 28136 times
  9. 104 B occurred 25794 times
  10. 992 B occurred 14521 times

  allocations <= 64:   131723 18.19%
  allocations <= 1024: 423315 58.47%
  allocations <= 4096: 622732 86.01%

mysqld starts one thread per connection, which produce roughly the same
allocator workload (checked with a malt trace).

Interpretation:

The mysql benchmark tries to be as near as possible to a real world workload.
So all non-functional characteristics of an allocator are measured.
This means the results can give hints on how each allocator performs
for a similar workload.
But the results don't directly explain why an allocator performs
this way. To obtain a more complete understanding deeper analysis of the
allocators algorithm, host system and workload is needed.
"""

import multiprocessing
import os
import re
import shutil
from subprocess import CalledProcessError
import sys

import numpy as np

from allocbench.benchmark import Benchmark
import allocbench.facter as facter
import allocbench.plots as plt
from allocbench.util import print_status, print_debug, print_info2, print_warn, run_cmd

MYSQL_USER = "root"
RUN_TIME = 300
TABLES = 5

PREPARE_CMD = (
    f"sysbench oltp_read_only --db-driver=mysql --mysql-user={MYSQL_USER} "
    f"--threads={multiprocessing.cpu_count()} "
    f"--mysql-socket={{build_dir}}/socket --tables={TABLES} --table-size=1000000 prepare"
)

CMD = (
    f"sysbench oltp_read_only --threads={{nthreads}} --time={RUN_TIME} --tables={TABLES} "
    f"--db-driver=mysql --mysql-user={MYSQL_USER} --mysql-socket={{build_dir}}/socket run"
)

SERVER_CMD = (
    "mysqld --no-defaults -h {build_dir} --socket={build_dir}/socket --port=123456 "
    f"--max-connections={multiprocessing.cpu_count()} --secure-file-priv=")


class BenchmarkMYSQL(Benchmark):
    """Mysql bechmark definition"""
    def __init__(self):
        name = "mysql"

        self.args = {"nthreads": Benchmark.scale_threads_for_cpus(1)}
        self.cmd = CMD
        self.servers = [{"name": "mysqld", "cmd": SERVER_CMD}]
        self.measure_cmd = ""

        self.requirements = ["mysqld", "sysbench"]

        super().__init__(name)

    def reset_preparations(self):
        """Reset self.build_dir if preparing fails"""
        if os.path.exists(self.build_dir):
            print_warn("Reset mysql test directory")
            shutil.rmtree(self.build_dir, ignore_errors=True)

    def prepare(self):
        """Setup mysql database containing random test data"""
        self.results["facts"]["runtime [s]"] = RUN_TIME

        # save mysqld and sysbench versions
        for exe in self.requirements:
            self.results["facts"]["versions"][exe] = facter.exe_version(
                exe, "--version")

        # Setup Test Environment
        if not os.path.exists(self.build_dir):
            print_status("Prepare mysqld directory and database")
            os.makedirs(self.build_dir)

            # Init database
            if "MariaDB" in self.results["facts"]["versions"]["mysqld"]:
                init_db_cmd = [
                    "mysql_install_db", "--basedir=/usr",
                    f"--datadir={self.build_dir}"
                ]
                print_info2("MariaDB detected")
            else:
                init_db_cmd = [
                    "mysqld", "-h", self.build_dir, "--initialize-insecure"
                ]
                print_info2("Oracle MySQL detected")

            try:
                run_cmd(init_db_cmd, capture=True)
            except CalledProcessError as err:
                print_debug("Stdout:", err.stdout, file=sys.stderr)
                print_debug("Stderr:", err.stderr, file=sys.stderr)
                self.reset_preparations()
                raise

            self.start_servers()

            # Create sbtest TABLE
            try:
                run_cmd(f"mysql -u {MYSQL_USER} -S {self.build_dir}/socket".
                        split(),
                        input="CREATE DATABASE sbtest;\n",
                        capture=True,
                        cwd=self.build_dir)
            except CalledProcessError as err:
                print_debug("Stderr:", err.stderr, file=sys.stderr)
                self.reset_preparations()
                raise

            print_status("Prepare test tables ...")
            prepare_cmd = PREPARE_CMD.format(build_dir=self.build_dir).split()
            try:
                run_cmd(prepare_cmd, capture=True)
            except CalledProcessError as err:
                print_debug("Stdout:", err.stdout, file=sys.stderr)
                print_debug("Stderr:", err.stderr, file=sys.stderr)
                self.reset_preparations()
                raise

            self.shutdown_servers()

    @staticmethod
    def process_output(result, stdout, stderr, allocator, perm):  # pylint: disable=too-many-arguments, unused-argument
        result["transactions"] = re.search("transactions:\\s*(\\d*)",
                                           stdout).group(1)
        result["queries"] = re.search("queries:\\s*(\\d*)", stdout).group(1)
        # Latency
        result["min"] = re.search("min:\\s*(\\d*.\\d*)", stdout).group(1)
        result["avg"] = re.search("avg:\\s*(\\d*.\\d*)", stdout).group(1)
        result["max"] = re.search("max:\\s*(\\d*.\\d*)", stdout).group(1)

    def summary(self):
        allocators = self.results["allocators"]
        args = self.results["args"]

        # linear plot
        plt.plot(self,
                 "{transactions}",
                 fig_options={
                     'xlabel': 'threads',
                     'ylabel': 'transactions',
                     'title': 'sysbench oltp read only',
                 },
                 file_postfix="l")

        # normalized linear plot
        ref_alloc = list(allocators)[0]
        plt.plot(self,
                 "{transactions}",
                 fig_options={
                     'xlabel': 'threads',
                     'ylabel': 'transactions scaled at {scale}',
                     'title': 'sysbench oltp read only',
                 },
                 file_postfix="norm.l",
                 scale=ref_alloc)

        # bar plot
        plt.plot(self,
                 "{transactions}",
                 plot_type='bar',
                 fig_options={
                     'xlabel': 'threads',
                     'ylabel': 'transactions',
                     'title': 'sysbench oltp read only',
                 },
                 file_postfix="b")

        # normalized bar plot
        plt.plot(self,
                 "{transactions}",
                 plot_type='bar',
                 fig_options={
                     'xlabel': 'threads',
                     'ylabel': 'transactions scaled at {scale}',
                     'title': 'sysbench oltp read only',
                 },
                 file_postfix="norm.b",
                 scale=ref_alloc)

        # Memusage
        plt.plot(self,
                 "{mysqld_VmHWM}",
                 plot_type='bar',
                 fig_options={
                     'xlabel': 'threads',
                     'ylabel': 'VmHWM in kB',
                     'title': 'Memusage sysbench oltp read only',
                 },
                 file_postfix="mem")

        plt.write_tex_table(self, [{
            "label": "Transactions",
            "expression": "{transactions}",
            "sort": ">"
        }, {
            "label": "Memusage [KB]",
            "expression": "{mysqld_VmHWM}",
            "sort": "<"
        }],
                            file_postfix="table")

        # Colored latex table showing transactions count
        data = {allocator: {} for allocator in allocators}
        for perm in self.iterate_args(args=args):
            for allocator in allocators:
                mean = plt.get_y_data(self, "{transactions}", allocator,
                                      perm)[0]
                std = plt.get_y_data(self,
                                     "{transactions}",
                                     allocator,
                                     perm,
                                     stat="std")[0]
                data[allocator][perm] = {"mean": mean, "std": std}

        mins = {}
        maxs = {}
        for perm in self.iterate_args(args=args):
            cmax = None
            cmin = None
            for allocator in allocators:
                mean = data[allocator][perm]["mean"]
                if not cmax or mean > cmax:
                    cmax = mean
                if not cmin or mean < cmin:
                    cmin = mean
            maxs[perm] = cmax
            mins[perm] = cmin

        fname = ".".join([self.name, "transactions.tex"])
        headers = [perm.nthreads for perm in self.iterate_args(args=args)]
        with open(fname, "w") as table_file:
            print("\\begin{tabular}{| l" + " l" * len(headers) + " |}",
                  file=table_file)
            print("Fäden / Allokator ", end=" ", file=table_file)
            for head in headers:
                print("& {}".format(head), end=" ", file=table_file)
            print("\\\\\n\\hline", file=table_file)

            for allocator in allocators:
                print(allocator, end=" ", file=table_file)
                for perm in self.iterate_args(args=args):
                    mean = data[allocator][perm]["mean"]
                    entry_string = "& \\textcolor{{{}}}{{{:.3f}}}"
                    if mean == maxs[perm]:
                        color = "green"
                    elif mean == mins[perm]:
                        color = "red"
                    else:
                        color = "black"
                    print(entry_string.format(color, mean),
                          end=" ",
                          file=table_file)
                print("\\\\", file=table_file)

            print("\\end{tabular}", file=table_file)

        plt.export_stats_to_csv(self, "transactions")
        plt.export_stats_to_dataref(self, "transactions")
