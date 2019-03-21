import atexit
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

cmd = ("sysbench oltp_read_only --threads={nthreads} --time=60 --tables=5 "
       "--db-driver=mysql --mysql-user=root --mysql-socket="
       + cwd + "/mysql_test/socket run")

server_cmd = ("{0} -h {2}/mysql_test --socket={2}/mysql_test/socket "
              "--max-connections={1} "
              "--secure-file-priv=").format(shutil.which("mysqld"),
                                            multiprocessing.cpu_count(), cwd).split()


class Benchmark_MYSQL(Benchmark):
    def __init__(self):
        self.name = "mysql"
        self.descrition = """See sysbench documentation."""

        # mysqld fails with hoard somehow
        self.allocators = copy.copy(allocators)
        if "hoard" in self.allocators:
            del(self.allocators["hoard"])

        self.args = {"nthreads": Benchmark.scale_threads_for_cpus(1)}
        self.cmd = cmd
        self.measure_cmd = ""

        self.requirements = ["mysqld", "sysbench"]

        atexit.register(self.terminate_server)

        super().__init__()

    def start_and_wait_for_server(self, cmd_prefix=""):
        actual_cmd = cmd_prefix.split() + server_cmd
        print_info("Starting server with:", actual_cmd)

        self.server = subprocess.Popen(actual_cmd, stdout=PIPE, stderr=PIPE,
                                       universal_newlines=True)
        # TODO make sure server comes up !
        sleep(10)
        if self.server.poll() is not None:
            print_debug("cmd_prefix:", cmd_prefix, file=sys.stderr)
            print_debug("Stderr:", self.server.stderr, file=sys.stderr)
            return False

        return True

    def terminate_server(self):
        if hasattr(self, "server"):
            if self.server.poll() is None:
                print_info("Terminating mysql server")
                self.server.terminate()

            for i in range(0,10):
                sleep(1)
                if self.server.poll() is not None:
                    return

            print_info("Killing still running mysql server")
            self.server.kill()
            self.server.wait()

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

            if not self.start_and_wait_for_server():
                raise Exception("Starting mysql server failed with {}".format(self.server.returncode))

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
                raise("Preparing test tables failed with:", p.returncode)

            self.terminate_server()

    def cleanup(self):
        if os.path.exists("mysql_test"):
            print_status("Delete mysqld directory")
            shutil.rmtree("mysql_test", ignore_errors=True)

    def preallocator_hook(self, allocator, run, verbose):
        if not self.start_and_wait_for_server(cmd_prefix=allocator[1]["cmd_prefix"]):
            print_debug(allocator[1]["cmd_prefix"], file=sys.stderr)
            raise Exception("Starting mysql server for {} failed with".format(allocator[0], self.server.returncode))

    def postallocator_hook(self, allocator, run, verbose):
        self.terminate_server()

    def process_output(self, result, stdout, stderr, allocator, perm, verbose):
        result["transactions"] = re.search("transactions:\s*(\d*)", stdout).group(1)
        result["queries"] = re.search("queries:\s*(\d*)", stdout).group(1)
        # Latency
        result["min"] = re.search("min:\s*(\d*.\d*)", stdout).group(1)
        result["avg"] = re.search("avg:\s*(\d*.\d*)", stdout).group(1)
        result["max"] = re.search("max:\s*(\d*.\d*)", stdout).group(1)

        with open("/proc/"+str(self.server.pid)+"/status", "r") as f:
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
                             filepostfix="l.ro")


        # linear plot
        ref_alloc = list(allocators)[0]
        self.plot_single_arg("{transactions}",
                             xlabel='"threads"',
                             ylabel='"transactions scaled at " + scale',
                             title='"sysbench oltp read only"',
                             filepostfix="norm.l.ro",
                             scale=ref_alloc)

        # bar plot
        for i, allocator in enumerate(allocators):
            y_vals = []
            for perm in self.iterate_args(args=self.results["args"]):
                d = [int(m["transactions"]) for m in self.results[allocator][perm]]
                y_vals.append(np.mean(d))
            x_vals = [x-i/8 for x in range(1, len(y_vals) + 1)]
            plt.bar(x_vals, y_vals, width=0.2, label=allocator, align="center",
                    color=allocators[allocator]["color"])

        plt.legend()
        plt.xlabel("threads")
        plt.xticks(range(1, len(y_vals) + 1), self.results["args"]["nthreads"])
        plt.ylabel("transactions")
        plt.title("sysbench oltp read only")
        plt.savefig(self.name + ".b.ro.png")
        plt.clf()

        # normalized bar plot
        norm_y_vals = []
        for perm in self.iterate_args(args=self.results["args"]):
            d = [int(m["transactions"]) for m in self.results[ref_alloc][perm]]
            norm_y_vals.append(np.mean(d))

        nallocs = len(allocators)
        x_vals = [x for x in range(1, len(norm_y_vals)*nallocs + 1, nallocs)]
        plt.bar(x_vals, [1]*len(norm_y_vals), width=0.7, label=ref_alloc,
                align="center", color=allocators[ref_alloc]["color"])

        for i, allocator in enumerate(list(allocators)[1:]):
            y_vals = []
            for y, perm in enumerate(self.iterate_args(args=self.results["args"])):
                d = [int(m["transactions"]) for m in self.results[allocator][perm]]
                y_vals.append(np.mean(d) / norm_y_vals[y])

            x_vals = [x+i+1 for x in range(1, len(norm_y_vals)*nallocs + 1, nallocs)]

            plt.bar(x_vals, y_vals, width=0.7, label=allocator, align="center",
                    color=allocators[allocator]["color"])

        plt.legend()
        plt.xlabel("threads")
        plt.xticks(range(1, len(norm_y_vals)*nallocs + 1, nallocs), self.results["args"]["nthreads"])
        plt.ylabel("transactions normalized")
        plt.title("sysbench oltp read only")
        plt.savefig(self.name + ".norm.b.ro.png")
        plt.clf()

        # Memusage
        self.plot_single_arg("{rssmax}",
                             xlabel='"threads"',
                             ylabel='"VmHWM in kB"',
                             title='"Memusage sysbench oltp read only"',
                             filepostfix="ro.mem")

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


mysql = Benchmark_MYSQL()
