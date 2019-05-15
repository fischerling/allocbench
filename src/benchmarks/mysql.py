import copy
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import re
import shutil
import subprocess
from subprocess import PIPE
import sys
from time import sleep

from src.globalvars import allocators
from src.benchmark import Benchmark
from src.util import *

cwd = os.getcwd()

prepare_cmd = ("sysbench oltp_read_only --db-driver=mysql --mysql-user=root "
               "--mysql-socket=" + cwd + "/mysql_test/socket --tables=5 "
               "--table-size=1000000 prepare").split()

cmd = ("sysbench oltp_read_only --threads={nthreads} --time=10 --tables=5 "
       "--db-driver=mysql --mysql-user=root --mysql-socket="
       + cwd + "/mysql_test/socket run")

server_cmd = ("mysqld -h {0}/mysql_test --socket={0}/mysql_test/socket "
              "--max-connections={1} --secure-file-priv=").format(cwd, multiprocessing.cpu_count())


class Benchmark_MYSQL(Benchmark):
    def __init__(self):
        self.name = "mysql"
        self.descrition = """See sysbench documentation."""

        # mysqld fails with hoard somehow
        self.allocators = copy.copy(allocators)
        if "Hoard" in self.allocators:
            del(self.allocators["Hoard"])

        self.args = {"nthreads": Benchmark.scale_threads_for_cpus(1)}
        self.cmd = cmd
        self.server_cmds = [server_cmd]
        self.measure_cmd = ""

        self.requirements = ["mysqld", "sysbench"]

        super().__init__()

    def prepare(self):
        super().prepare()

        # Setup Test Environment
        if not os.path.exists("mysql_test"):
            print_status("Prepare mysqld directory and database")
            os.makedirs("mysql_test")

            # Init database
            if b"MariaDB" in subprocess.run(["mysqld", "--version"],
                                            stdout=PIPE).stdout:
                init_db_cmd = ["mysql_install_db", "--basedir=/usr",
                               "--datadir="+cwd+"/mysql_test"]
                print_info2("MariaDB detected")
            else:
                init_db_cmd = ["mysqld", "-h", cwd+"/mysql_test",
                               "--initialize-insecure"]
                print_info2("Oracle MySQL detected")

            p = subprocess.run(init_db_cmd, stdout=PIPE, stderr=PIPE)

            if not p.returncode == 0:
                print_debug(p.stderr, file=sys.stderr)
                raise Exception("Creating test DB failed with:", p.returncode)

            self.start_servers()

            # Create sbtest TABLE
            p = subprocess.run(("mysql -u root -S "+cwd+"/mysql_test/socket").split(" "),
                               input=b"CREATE DATABASE sbtest;\n",
                               stdout=PIPE, stderr=PIPE)

            if not p.returncode == 0:
                print_debug("Stderr:", p.stderr, file=sys.stderr)
                self.terminate_server()
                raise Exception("Creating test tables failed with:", p.returncode)

            print_status("Prepare test tables ...")
            ret = True
            p = subprocess.run(prepare_cmd, stdout=PIPE, stderr=PIPE)
            if p.returncode != 0:
                print_debug("Stdout:", p.stdout, file=sys.stderr)
                print_debug("Stderr:", p.stderr, file=sys.stderr)
                self.terminate_server()
                raise Exception("Preparing test tables failed with:", p.returncode)

            self.shutdown_servers()

    def cleanup(self):
        if os.path.exists("mysql_test"):
            print_status("Delete mysqld directory")
            shutil.rmtree("mysql_test", ignore_errors=True)

    def process_output(self, result, stdout, stderr, allocator, perm, verbose):
        result["transactions"] = re.search("transactions:\s*(\d*)", stdout).group(1)
        result["queries"] = re.search("queries:\s*(\d*)", stdout).group(1)
        # Latency
        result["min"] = re.search("min:\s*(\d*.\d*)", stdout).group(1)
        result["avg"] = re.search("avg:\s*(\d*.\d*)", stdout).group(1)
        result["max"] = re.search("max:\s*(\d*.\d*)", stdout).group(1)

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
            for i, allocator in enumerate(allocators):
                t = [float(x["transactions"]) for x in self.results[allocator][perm]]
                m = np.mean(t)
                s = np.std(t)/m
                d[allocator][perm] = {"mean": m, "std": s}

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

            print("\end{tabular}", file=f)

        self.export_to_csv("transactions")
        self.export_to_dataref("transactions")


mysql = Benchmark_MYSQL()
