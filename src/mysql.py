import copy
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import re
import shutil
import subprocess
from subprocess import PIPE
from time import sleep

from src.benchmark import Benchmark
from src.targets import targets

cwd = os.getcwd()

prepare_cmd = ("sysbench oltp_read_only --db-driver=mysql --mysql-user=root "
               "--mysql-socket=" + cwd + "/mysql_test/socket --tables=5 "
               "--table-size=1000000 prepare").split()

cmd = ("sysbench oltp_read_only --threads={nthreads} --time=60 --tables=5 "
       "--db-driver=mysql --mysql-user=root --mysql-socket="
       + cwd + "/mysql_test/socket run")

server_cmd = ("{0} -h {1}/mysql_test --socket={1}/mysql_test/socket "
              "--secure-file-priv=").format(shutil.which("mysqld"), cwd).split()


class Benchmark_MYSQL(Benchmark):
    def __init__(self):
        self.name = "mysql"
        self.descrition = """See sysbench documentation."""

        # mysqld fails with hoard somehow
        self.targets = copy.copy(targets)
        if "hoard" in self.targets:
            del(self.targets["hoard"])

        self.args = {"nthreads": range(1, multiprocessing.cpu_count() + 1)}
        self.cmd = cmd
        self.measure_cmd = ""

        self.requirements = ["mysqld", "sysbench"]
        super().__init__()

    def start_and_wait_for_server(self, verbose, cmd_prefix=""):
        actual_cmd = cmd_prefix.split() + server_cmd
        if verbose:
            print("Starting server with:", actual_cmd)

        self.server = subprocess.Popen(actual_cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
        # TODO make sure server comes up !
        sleep(10)
        return self.server.poll() is None

    def prepare(self, verbose=False):
        if not super().prepare(verbose=verbose):
            return False
        # Setup Test Environment
        if not os.path.exists("mysql_test"):
            print("Prepare mysqld directory and database")
            os.makedirs("mysql_test")

            # Init database
            if b"MariaDB" in subprocess.run(["mysqld", "--version"],
                                            stdout=PIPE).stdout:
                init_db_cmd = ["mysql_install_db", "--basedir=/usr",
                               "--datadir="+cwd+"/mysql_test"]
                if verbose:
                    print("MariaDB detected")
            else:
                init_db_cmd = ["mysqld", "-h", cwd+"/mysql_test",
                               "--initialize-insecure"]
                if verbose:
                    print("Oracle MySQL detected")

            p = subprocess.run(init_db_cmd, stdout=PIPE, stderr=PIPE)

            if not p.returncode == 0:
                print(p.stderr)
                return False

            if not self.start_and_wait_for_server(verbose):
                print("Starting mysqld failed")
                return False

            # Create sbtest TABLE
            p = subprocess.run("mysql -u root -S "+cwd+"/mysql_test/socket".split(" "),
                               input=b"CREATE DATABASE sbtest;\n",
                               stdout=PIPE, stderr=PIPE)

            if not p.returncode == 0:
                print(p.stderr)
                self.server.kill()
                self.server.wait()
                return False

            print("Prepare test tables")
            ret = True
            p = subprocess.run(prepare_cmd, stdout=PIPE, stderr=PIPE)
            if p.returncode != 0:
                print(p.stout)
                print(p.stderr)
                ret = False

            self.server.kill()
            self.server.wait()

            return ret

        return True

    def cleanup(self):
        if os.path.exists("mysql_test"):
            print("Delete mysqld directory")
            shutil.rmtree("mysql_test")

    def pretarget_hook(self, target, run, verbose):
        if not self.start_and_wait_for_server(verbose,
                                              cmd_prefix=target[1]["cmd_prefix"]):
            print("Can't start server for", target[0] + ".")
            print("Aborting Benchmark.")
            print(target[1]["cmd_prefix"])
            print(self.server.stderr.read())
            return False

    def posttarget_hook(self, target, run, verbose):
        self.server.kill()
        self.server.wait()

    def process_output(self, result, stdout, stderr, target, perm, verbose):
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

    def analyse(self, verbose=False, nolibmemusage=""):
        import chattyparser

        nthreads = [0] + list(self.args["nthreads"])
        failed = False

        runs = len(nthreads)
        for i, t in enumerate(nthreads):
            print("analysing", i + 1, "of", runs, "\r", end='')

            os.environ["LD_PRELOAD"] = "build/chattymalloc.so"
            if not self.start_and_wait_for_server(verbose):
                print("Can't start server.")
                print("Aborting analysing.")
                failed = True
            os.environ["LD_PRELOAD"] = ""

            if not failed and t != 0:
                target_cmd = self.cmd.format(nthreads=t).split(" ")
                p = subprocess.run(target_cmd,
                                   stderr=PIPE,
                                   stdout=PIPE,
                                   universal_newlines=True)

                if p.returncode != 0:
                    print("\n" + " ".join(target_cmd), "exited with",
                          p.returncode, ".\n Aborting analysing.")
                    print(p.stderr)
                    print(p.stdout)
                    failed = True

            self.server.kill()
            self.server.wait()

            hist, calls, reqsize, top5reqsize = chattyparser.parse()
            chattyparser.plot_hist_ascii(hist, calls,
                                         ".".join([self.name, str(t),
                                                  "memusage", "hist"]))

            if failed:
                print(self.server.stdout.read())
                print(self.server.stderr.read())
                return False
        print()

    def summary(self):
        targets = self.results["targets"]
        args = self.results["args"]

        # linear plot
        self.plot_single_arg("{transactions}",
                             xlabel='"threads"',
                             ylabel='"transactions"',
                             title='"sysbench oltp read only"',
                             filepostfix="l.ro")

        # bar plot
        for i, target in enumerate(targets):
            y_vals = []
            for perm in self.iterate_args(args=self.results["args"]):
                d = [int(m["transactions"]) for m in self.results[target][perm]]
                y_vals.append(np.mean(d))
            x_vals = [x-i/8 for x in range(1, len(y_vals) + 1)]
            plt.bar(x_vals, y_vals, width=0.2, label=target, align="center",
                    color=targets[target]["color"])

        plt.legend()
        plt.xlabel("threads")
        plt.xticks(range(1, len(y_vals) + 1), self.results["args"]["nthreads"])
        plt.ylabel("transactions")
        plt.title("sysbench oltp read only")
        plt.savefig(self.name + ".b.ro.png")
        plt.clf()

        # Memusage
        self.plot_single_arg("{rssmax}",
                             xlabel='"threads"',
                             ylabel='"VmHWM in kB"',
                             title='"Memusage sysbench oltp read only"',
                             filepostfix="ro.mem")

        # Colored latex table showing transactions count
        d = {target: {} for target in targets}
        for perm in self.iterate_args(args=args):
            for i, target in enumerate(targets):
                t = [float(x["transactions"]) for x in self.results[target][perm]]
                m = np.mean(t)
                s = np.std(t)/m
                d[target][perm] = {"mean": m, "std": s}

        mins = {}
        maxs = {}
        for perm in self.iterate_args(args=args):
            cmax = None
            cmin = None
            for i, target in enumerate(targets):
                m = d[target][perm]["mean"]
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

            for target in targets:
                print(target, end=" ", file=f)
                for perm in self.iterate_args(args=args):
                    m = d[target][perm]["mean"]
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
