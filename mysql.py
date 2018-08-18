import copy
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import psutil
import re
import shutil
import subprocess
from subprocess import PIPE
from time import sleep

from benchmark import Benchmark
from common_targets import common_targets

cwd = os.getcwd()

prepare_cmd = ("sysbench oltp_read_only --db-driver=mysql --mysql-user=root "
              "--mysql-socket="+cwd+"/mysql_test/socket --table-size=1000000 prepare").split()

cmd = ("sysbench oltp_read_only --threads={} --time=100 "
       "--db-driver=mysql --mysql-user=root --mysql-socket={}/mysql_test/socket run")

server_cmd = ("mysqld -h {0}/mysql_test --socket={0}/mysql_test/socket "
             "--secure-file-priv=").format(cwd).split()


class Benchmark_MYSQL( Benchmark ):
    def __init__(self):
        self.name = "mysql"
        self.descrition = """See sysbench documentation."""
        self.targets = copy.copy(common_targets)
        if "klmalloc" in self.targets:
            del(self.targets["klmalloc"])
        self.nthreads = range(1, psutil.cpu_count() * 4 + 1, 2)

        self.results = {"args": {"nthreads" : self.nthreads},
                        "targets" : self.targets,
                        "memusage": {t : [] for t in self.targets}}

    def start_and_wait_for_server(self, verbose, log=None):
        if not log:
            log = os.devnull

        with open(log, "wb") as f:
            self.server = psutil.Popen(server_cmd, env=os.environ,
                                               stdout=f,
                                               stderr=f,
                                               universal_newlines=True)
        #TODO make sure server comes up !!!!
        sleep(5)
        return self.server.poll() == None

    def prepare(self, verbose=False):
        # Setup mysqld
        if not os.path.exists("mysql_test"):
            print("Prepare mysqld directory and database")
            os.makedirs("mysql_test")

            # Init database
            if b"MariaDB" in subprocess.run(["mysqld", "--version"],
                                            stdout=PIPE).stdout:
                init_db_cmd = ["mysql_install_db", "--basedir=/usr",
                                "--datadir={}/mysql_test".format(os.getcwd())]
                if verbose:
                    print("MariaDB detected")
            else:
                init_db_cmd = ["mysqld", "-h", "{}/mysql_test".format(os.getcwd()),
                                "--initialize-insecure"]
                if verbose:
                    print("Oracle MySQL detected")

            p = subprocess.run(init_db_cmd, stdout=PIPE, stderr=PIPE)

            if not p.returncode == 0:
                print(p.stderr)
                return False

            if not self.start_and_wait_for_server(verbose, "mysqld.log"):
                print("Starting mysqld failed")
                return False

            p = subprocess.run("mysql -u root -S {}/mysql_test/socket".format(cwd).split(" "),
                input = b"CREATE DATABASE sbtest;\n", stdout=PIPE, stderr=PIPE)

            if not p.returncode == 0:
                print(p.stderr)
                self.server.kill()
                self.server.wait()
                return False

            print("Prepare test table")
            ret = True
            p = subprocess.run(prepare_cmd, stdout=PIPE, stderr=PIPE)
            if p.returncode != 0:
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

    def run(self, verbose=False, save=False, runs=3):
        cwd = os.getcwd()
        for run in range(1, runs + 1):
            print(str(run) + ". run")

            # run cmd for each target
            n = len(self.nthreads)
            for tname, t in self.targets.items():
                os.environ["LD_PRELOAD"] = t["LD_PRELOAD"] # set LD_PRELOAD

                log = "mysqld.log"
                if tname == "chattymalloc":
                    log = "chattymalloc.data"
                if not self.start_and_wait_for_server(verbose, log):
                    print("Can't start server for", tname + ".")
                    print("Aborting Benchmark.")
                    return False

                # Get initial memory footprint
                heap_size = {"heap_start": 0, "heap_end": 0}
                for m in self.server.memory_maps():
                    if "[heap]" in m:
                        heap_size["heap_start"] = m.size

                for i, thread in enumerate(self.nthreads):
                    print(tname + ":", i + 1, "of", n, "\r", end='')

                    target_cmd = cmd.format(thread, cwd).split(" ")
                    p = subprocess.run(target_cmd, stderr=PIPE, stdout=PIPE,
                                        universal_newlines=True)

                    if p.returncode != 0:
                        print("\n" + " ".join(target_cmd), "exited with", p.returncode, ".\n Aborting Benchmark.")
                        print(tname, t)
                        print(p.stderr)
                        print(p.stdout)
                        self.server.kill()
                        self.server.wait()
                        return False

                    result = {}

                    if tname == "chattymalloc":
                        with open(log, "rb") as f:
                            hist = {}
                            for l in f.readlines():
                                l = str(l, "utf-8").replace("chattymalloc: ", "")
                                try:
                                    n = int(l)
                                except ValueError:
                                    continue

                                if not n in hist:
                                    hist[n] = 0
                                hist[n] += 1
                        result["hist"] = hist
                    else:
                        result["transactions"] = re.search("transactions:\s*(\d*)", p.stdout).group(1)
                        result["queries"] = re.search("queries:\s*(\d*)", p.stdout).group(1)
                        # Latency
                        result["min"] = re.search("min:\s*(\d*.\d*)", p.stdout).group(1)
                        result["avg"] = re.search("avg:\s*(\d*.\d*)", p.stdout).group(1)
                        result["max"] = re.search("max:\s*(\d*.\d*)", p.stdout).group(1)

                    key = (tname, thread)
                    if not key in self.results:
                        self.results[key] = [result]
                    else:
                        self.results[key].append(result)

                print()

                # Get final memory footprint
                for m in self.server.memory_maps():
                    if "[heap]" in m:
                        heap_size["heap_end"] = m.size

                if tname != "chattymalloc":
                    self.results["memusage"][tname].append(heap_size)

                self.server.kill()
                self.server.wait()

        if save:
            with open(self.name + ".save", "wb") as f:
                pickle.dump(self.results, f)
        return True

    def summary(self):
        # linear plot
        nthreads = self.results["args"]["nthreads"]
        targets = self.results["targets"]
        y_mapping = {v: i for i, v in enumerate(nthreads)}

        for target in targets:
            if target == "chattymalloc":
                continue
            y_vals = [0] * len(nthreads)
            for mid, measures in self.results.items():
                if mid[0] == target:
                    d = []
                    for m in measures:
                        d.append(int(m["transactions"]))
                    y_vals[y_mapping[mid[1]]] = np.mean(d)
            plt.plot(nthreads, y_vals, label=target, linestyle='-', marker='.', color=targets[target]["color"])

        plt.legend()
        plt.xlabel("threads")
        plt.ylabel("transactions")
        plt.title("sysbench oltp read only")
        plt.savefig(self.name + ".l.ro.png")
        plt.clf()

        # bar plot
        nthreads = list(self.results["args"]["nthreads"])
        targets = self.results["targets"]
        y_mapping = {v: i for i, v in enumerate(nthreads)}

        for i, target in enumerate(targets):
            if target == "chattymalloc":
                continue
            x_vals = [x-i/8 for x in range(1, len(nthreads) + 1)]
            y_vals = [0] * len(nthreads)
            for mid, measures in self.results.items():
                if mid[0] == target:
                    d = []
                    for m in measures:
                        d.append(int(m["transactions"]))
                    y_vals[y_mapping[mid[1]]] = np.mean(d)
            plt.bar(x_vals, y_vals, width=0.2, label=target, align="center",  color=targets[target]["color"])

        plt.legend()
        plt.xlabel("threads")
        plt.xticks(range(1, len(nthreads) + 1), nthreads)
        plt.ylabel("transactions")
        plt.title("sysbench oltp read only")
        plt.savefig(self.name + ".b.ro.png")
        plt.clf()

        for mid, measures in self.results.items():
            if mid[0] == "chattymalloc":
                hist = [(n, s) for s,n in measures[0]["hist"].items()]
                hist.sort()
                print("Histogram for", mid[1], "threads:")
                print(hist)

        # memusage
        for target, measures in self.results["memusage"].items():
            heap_growth = []
            for m in measures:
                heap_growth.append(int(m["heap_end"]) - int(m["heap_start"]))
            print(target, "memory footprint:")
            print("\t avg heap growth:", np.mean(heap_growth))


mysql = Benchmark_MYSQL()
