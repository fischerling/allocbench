# Copyright 2018-2019 Florian Fischer <florian.fl.fischer@fau.de>
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

"""Definition of the mysql read only benchmark using sysbench"""

import multiprocessing
import os
import re
import shutil
import subprocess
from subprocess import PIPE
import sys

from src.benchmark import Benchmark
from src.util import print_status, print_debug, print_info2

TESTDIR = os.path.join(os.getcwd(), "mysql_test")
MYSQL_USER = "root"
RUN_TIME = 300
TABLES = 5

PREPARE_CMD = (f"sysbench oltp_read_only --db-driver=mysql --mysql-user={MYSQL_USER} "
               f"--mysql-socket={TESTDIR}/socket --tables={TABLES} --table-size=1000000 prepare")

CMD = (f"sysbench oltp_read_only --threads={{nthreads}} --time={RUN_TIME} --tables={TABLES} "
       f"--db-driver=mysql --mysql-user={MYSQL_USER} --mysql-socket={TESTDIR}/socket run")

SERVER_CMD = (f"mysqld --no-defaults -h {TESTDIR} --socket={TESTDIR}/socket --port=123456 "
              f"--max-connections={multiprocessing.cpu_count()} --secure-file-priv=")


class BenchmarkMYSQL(Benchmark):
    """Mysql bechmark definition

    See sysbench documentation for more details about the oltp_read_only benchmark
    """

    def __init__(self):
        self.name = "mysql"

        self.args = {"nthreads": Benchmark.scale_threads_for_cpus(1)}
        self.cmd = CMD
        self.server_cmds = [SERVER_CMD]
        self.measure_cmd = ""

        self.requirements = ["mysqld", "sysbench"]

        super().__init__()

        self.results["facts"]["runtime [s]"] = RUN_TIME
        self.results["facts"]["sysbench"] = subprocess.run(["sysbench", "--version"],
                                                           stdout=PIPE,
                                                           universal_newlines=True).stdout[:-1]

    def prepare(self):
        super().prepare()

        # Setup Test Environment
        if not os.path.exists("mysql_test"):
            print_status("Prepare mysqld directory and database")
            os.makedirs("mysql_test")

            # Init database
            self.results["facts"]["mysqld"] = subprocess.run(["mysqld", "--version"],
                                                             stdout=PIPE,
                                                             universal_newlines=True).stdout[:-1]
            if "MariaDB" in self.results["facts"]["mysqld"]:
                init_db_cmd = ["mysql_install_db", "--basedir=/usr",
                               f"--datadir={TESTDIR}"]
                print_info2("MariaDB detected")
            else:
                init_db_cmd = ["mysqld", "-h", f"{TESTDIR}",
                               "--initialize-insecure"]
                print_info2("Oracle MySQL detected")

            p = subprocess.run(init_db_cmd, stdout=PIPE, stderr=PIPE)

            if not p.returncode == 0:
                print_debug(init_db_cmd)
                print_debug("Stdout:", p.stdout, file=sys.stdout)
                print_debug("Stderr:", p.stderr, file=sys.stderr)
                raise Exception("Creating test DB failed with:", p.returncode)

            self.start_servers()

            # Create sbtest TABLE
            p = subprocess.run(f"mysql -u {MYSQL_USER} -S {TESTDIR}/socket".split(),
                               input=b"CREATE DATABASE sbtest;\n",
                               stdout=PIPE, stderr=PIPE)

            if p.returncode != 0:
                print_debug("Stderr:", p.stderr, file=sys.stderr)
                raise Exception("Creating test tables failed with:", p.returncode)

            print_status("Prepare test tables ...")
            p = subprocess.run(PREPARE_CMD.split(), stdout=PIPE, stderr=PIPE)
            if p.returncode != 0:
                print_debug("Stdout:", p.stdout, file=sys.stderr)
                print_debug("Stderr:", p.stderr, file=sys.stderr)
                raise Exception("Preparing test tables failed with:", p.returncode)

            self.shutdown_servers()

    @staticmethod
    def cleanup():
        if os.path.exists("mysql_test"):
            print_status("Delete mysqld directory")
            shutil.rmtree("mysql_test", ignore_errors=True)

    def process_output(self, result, stdout, stderr, allocator, perm):
        result["transactions"] = re.search("transactions:\\s*(\\d*)", stdout).group(1)
        result["queries"] = re.search("queries:\\s*(\\d*)", stdout).group(1)
        # Latency
        result["min"] = re.search("min:\\s*(\\d*.\\d*)", stdout).group(1)
        result["avg"] = re.search("avg:\\s*(\\d*.\\d*)", stdout).group(1)
        result["max"] = re.search("max:\\s*(\\d*.\\d*)", stdout).group(1)

        with open("/proc/"+str(self.servers[0].pid)+"/status", "r") as f:
            for l in f.readlines():
                if l.startswith("VmHWM:"):
                    result["rssmax"] = int(l.replace("VmHWM:", "").strip().split()[0])
                    break

    def summary(self):
        allocators = self.results["allocators"]
        args = self.results["args"]

        # linear plot
        self.plot_single_arg("{transactions}",
                             xlabel='"threads"',
                             ylabel='"transactions"',
                             title='"sysbench oltp read only"',
                             filepostfix="l")

        # normalized linear plot
        ref_alloc = list(allocators)[0]
        self.plot_single_arg("{transactions}",
                             xlabel='"threads"',
                             ylabel='"transactions scaled at " + scale',
                             title='"sysbench oltp read only"',
                             filepostfix="norm.l",
                             scale=ref_alloc)

        # bar plot
        self.barplot_single_arg("{transactions}",
                                xlabel='"threads"',
                                ylabel='"transactions"',
                                title='"sysbench oltp read only"',
                                filepostfix="b")

        # normalized bar plot
        self.barplot_single_arg("{transactions}",
                                xlabel='"threads"',
                                ylabel='"transactions scaled at " + scale',
                                title='"sysbench oltp read only"',
                                filepostfix="norm.b",
                                scale=ref_alloc)

        # Memusage
        self.barplot_single_arg("{rssmax}",
                                xlabel='"threads"',
                                ylabel='"VmHWM in kB"',
                                title='"Memusage sysbench oltp read only"',
                                filepostfix="mem")

        # Colored latex table showing transactions count
        d = {allocator: {} for allocator in allocators}
        for perm in self.iterate_args(args=args):
            for allocator in allocators:
                transactions = [float(measure["transactions"])
                                for measure in self.results[allocator][perm]]
                mean = np.mean(transactions)
                std = np.std(transactions)/mean
                d[allocator][perm] = {"mean": mean, "std": std}

        mins = {}
        maxs = {}
        for perm in self.iterate_args(args=args):
            cmax = None
            cmin = None
            for i, allocator in enumerate(allocators):
                m = d[allocator][perm]["mean"]
                if not cmax or m > cmax:
                    cmax = m
                if not cmin or m < cmin:
                    cmin = m
            maxs[perm] = cmax
            mins[perm] = cmin

        fname = ".".join([self.name, "transactions.tex"])
        headers = [perm.nthreads for perm in self.iterate_args(args=args)]
        with open(fname, "w") as f:
            print("\\begin{tabular}{| l" + " l"*len(headers) + " |}", file=f)
            print("Fäden / Allokator ", end=" ", file=f)
            for head in headers:
                print("& {}".format(head), end=" ", file=f)
            print("\\\\\n\\hline", file=f)

            for allocator in allocators:
                print(allocator, end=" ", file=f)
                for perm in self.iterate_args(args=args):
                    m = d[allocator][perm]["mean"]
                    s = "& \\textcolor{{{}}}{{{:.3f}}}"
                    if m == maxs[perm]:
                        color = "green"
                    elif m == mins[perm]:
                        color = "red"
                    else:
                        color = "black"
                    print(s.format(color, m), end=" ", file=f)
                print("\\\\", file=f)

            print("\\end{tabular}", file=f)

        self.export_stats_to_csv("transactions")
        self.export_stats_to_dataref("transactions")


mysql = BenchmarkMYSQL()
