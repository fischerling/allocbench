import copy
import csv
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import pickle
import re
import shutil
import subprocess
from time import sleep

from benchmark import Benchmark
from common_targets import common_targets

cwd = os.getcwd()

prepare_cmd = ("sysbench oltp_read_only --db-driver=mysql --mysql-user=root "
              "--mysql-socket="+cwd+"/mysql_test/socket --table-size=1000000 prepare").split()

cmd = ("sysbench oltp_read_only --threads={} --time=10 "
       "--db-driver=mysql --mysql-user=root --mysql-socket={}/mysql_test/socket run")

server_cmd = ("mysqld -h {0}/mysql_test --socket={0}/mysql_test/socket "
             "--secure-file-priv=").format(cwd).split()


class Benchmark_MYSQL( Benchmark ):
    def __init__(self):
        self.name = "mysql"
        self.descrition = """See sysbench documentation."""
        self.targets = copy.copy(common_targets)
        del(self.targets["klmalloc"])
        self.nthreads = range(1, multiprocessing.cpu_count() * 2 + 1)

        self.results = {"args": {"nthreads" : self.nthreads},
                        "targets" : self.targets,
                        "memusage": {t : [] for t in self.targets}}

    def start_and_wait_for_server(self, verbose, log=None):
        if not log:
            log = os.devnull

        with open(log, "ab") as f:
            self.server = subprocess.Popen(server_cmd, env=os.environ,
                                               stdout=f,
                                               stderr=f,
                                               universal_newlines=True)
        #TODO make sure server comes up !!!!
        sleep(5)
        return True

    def prepare(self, verbose=False):
        ret = True
        # Setup mysqld
        if not os.path.exists("mysql_test"):
            print("Prepare mysqld directory and database")
            os.makedirs("mysql_test")

            # Init database
            if b"MariaDB" in subprocess.run(["mysqld", "--version"],
                                            stdout=subprocess.PIPE).stdout:
                init_db_cmd = ["mysql_install_db", "--basedir=/usr",
                                "--datadir={}/mysql_test".format(os.getcwd())]
                if verbose:
                    print("MariaDB detected")
            else:
                init_db_cmd = ["mysqld", "-h", "{}/mysql_test".format(os.getcwd()),
                                "--initialize-insecure"]
                if verbose:
                    print("Oracle MySQL detected")

            with open(os.devnull, "w") as devnull:
                p = subprocess.run(init_db_cmd,
                            stdout=devnull, stderr=devnull)
            ret = ret and p.returncode == 0
            if not ret:
                print(p.stderr)
                return ret

            if not self.start_and_wait_for_server(verbose, "mysqld.log"):
                print("Starting mysqld failed")
                return False

            p = subprocess.run("mysql -u root -S {}/mysql_test/socket".format(cwd).split(" "),
                input = b"CREATE DATABASE sbtest;\n")
            ret = ret and p.returncode == 0
            if not ret:
                print(p.stderr)
                self.server.kill()
                self.server.wait()
                return ret

            print("Prepare test table")
            p = subprocess.run(prepare_cmd)
            ret = ret == p.returncode == 0
            self.server.kill()
            ret = ret and self.server.wait() == -9

        return ret

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
                # No custom build mysqld server supported yet.
                os.environ["LD_PRELOAD"] = t[1] # set LD_PRELOAD

                if not self.start_and_wait_for_server(verbose, "mysqld.log"):
                    print("Can't start server for", tname + ".")
                    print("Aborting Benchmark.")
                    return False

                # Get initial memory footprint
                ps = subprocess.run(["ps", "-F", str(self.server.pid)], stdout=subprocess.PIPE)
                tokens = str(ps.stdout.splitlines()[1]).split()
                self.results["memusage"][tname].append({"VSZ_start" : tokens[4], "RSS_start" : tokens[5]})

                for i, thread in enumerate(self.nthreads):
                    print(tname + ":", i + 1, "of", n, "\r", end='')

                    target_cmd = cmd.format(thread, cwd).split(" ")
                    p = subprocess.run(target_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
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
                ps = subprocess.run(["ps", "-F", str(self.server.pid)], stdout=subprocess.PIPE)
                tokens = str(ps.stdout.splitlines()[1]).split()
                self.results["memusage"][tname][run-1].update({"VSZ_end" : tokens[4], "RSS_end" : tokens[5]})

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
            y_vals = [0] * len(nthreads)
            for mid, measures in self.results.items():
                if mid[0] == target:
                    d = []
                    for m in measures:
                        d.append(int(m["transactions"]))
                    y_vals[y_mapping[mid[1]]] = np.mean(d)
            plt.plot(nthreads, y_vals, label=target, linestyle='-', marker='.')

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
            y_vals = [0] * len(nthreads)
            for mid, measures in self.results.items():
                if mid[0] == target:
                    d = []
                    for m in measures:
                        d.append(int(m["transactions"]))
                    y_vals[y_mapping[mid[1]]] = np.mean(d)
            plt.bar([x-i/8 for x in range(1, len(nthreads) + 1)], y_vals, width=0.2, label=target, align="center")

        plt.legend()
        plt.xlabel("threads")
        plt.xticks(range(1, len(nthreads) + 1), nthreads)
        plt.ylabel("transactions")
        plt.title("sysbench oltp read only")
        plt.savefig(self.name + ".b.ro.png")
        plt.clf()

        # memusage
        for target, measures in self.results["memusage"].items():
            vsz_growth = []
            rss_growth = []
            for m in measures:
                vsz_growth.append(int(m["VSZ_end"]) - int(m["VSZ_start"]))
                rss_growth.append(int(m["RSS_end"]) - int(m["RSS_start"]))
            print(target, "memory footprint:")
            print("\t avg vsz growth:", np.mean(vsz_growth))
            print("\t avg rss growth:", np.mean(rss_growth))
            

mysql = Benchmark_MYSQL()
