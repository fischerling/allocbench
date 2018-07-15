import csv
import io
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import pickle
import re
import shutil
import subprocess
from time import sleep

from common_targets import common_targets

cwd = os.getcwd()

prepare_cmd = ("sysbench oltp_read_only --db-driver=mysql --mysql-user=root "
              "--mysql-socket="+cwd+"/mysql_test/socket --table-size=1000000 prepare").split(" ")

cmd = ("sysbench oltp_read_only --threads={} --time=10 --max-requests=0 "
       "--db-driver=mysql --mysql-user=root --mysql-socket={}/mysql_test/socket run")

server_cmd = "mysqld -h {0}/mysql_test --socket={0}/mysql_test/socket".format(cwd).split(" ")


class Benchmark_MYSQL():
    def __init__(self):
        self.name = "MYSQL Stress Benchmark"
        self.descrition = """See sysbench documentation."""
        self.targets = common_targets
        del(self.targets["klmalloc"])
        self.nthreads = range(1, multiprocessing.cpu_count() * 2 + 1)
        
        self.results = {}
    
    def start_and_wait_for_server(self, env, verbose, log=None):
        if not log:
            log = os.devnull

        with open(log, "ab") as f:
            self.server = subprocess.Popen(server_cmd, env=env,
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
            with open(os.devnull, "w") as devnull:
                p = subprocess.run(["mysql_install_db", "--basedir=/usr",
                            "--datadir={}/mysql_test".format(os.getcwd())],
                            stdout=devnull, stderr=devnull)
            ret = ret and p.returncode == 0
            if not ret:
                return ret

            if not self.start_and_wait_for_server(None, verbose, "mysqld.log"):
                print("Starting mysqld failed")
                return False

            p = subprocess.run("mysql -u root -S {}/mysql_test/socket".format(cwd).split(" "),
                input = b"CREATE DATABASE sbtest;\n")
            ret = ret and p.returncode == 0
            if not ret:
                return ret

            print("Prepare test table")
            subprocess.run(prepare_cmd)
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
                env = {"LD_PRELOAD" : t[1]} if t[1] != "" else None

                if not self.start_and_wait_for_server(env, verbose, "mysqld.log"):
                    print("Can't start server for", tname + ".")
                    print("Aborting Benchmark.")
                    return False

                for i in self.nthreads:
                    print(tname + ":", i, "of", n, "\r", end='')

                    target_cmd = cmd.format(i, cwd).split(" ")
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

                    key = (tname, i)
                    if not key in self.results:
                        self.results[key] = [result]
                    else:
                        self.results[key].append(result)

                print()
                self.server.kill()
                self.server.wait()
                
                    # Strip all whitespace from memusage output
                    # result["memusage"] = [x.replace(" ", "").replace("\t", "")
                                            # for x in output[0].splitlines()]
                        # 
                    # # Handle perf output
                    # csvreader = csv.reader(output[1].splitlines(), delimiter=';')
                    # for row in csvreader:
                        # result[row[2].replace("\\", "")] = row[0].replace("\\", "")

        if save:
            with open(self.name + ".save", "wb") as f:
                pickle.dump(self.results, f)
        return True

    def summary(self):
        for target in self.targets:
            y_vals = [0] * len(self.nthreads)
            for mid, measures in self.results.items():
                if mid[0] == target:
                    d = []
                    for m in measures:
                        d.append(int(m["transactions"]))
                    y_vals[mid[1]-1] = np.mean(d)
            plt.plot(self.nthreads, y_vals, label=target)

        plt.legend()
        plt.xlabel("threads")
        plt.ylabel("transactions")
        plt.title("sysbench oltp read only")
        plt.savefig("mysql.ro.png")
        plt.clf()
        # MAXSIZE fixed
        # for size in self.maxsize:
            # for target in self.targets:
                # y_vals = [0] * len(self.nthreads)
                # for mid, measures in self.results.items():
                    # if mid[0] == target and mid[2] == size:
                        # d = []
                        # for m in measures:
                            # # nthreads/time = MOPS/S
                            # d.append(mid[1]/float(m["cpu-clock:ku"]))
                        # y_vals[mid[1]-1] = np.mean(d)
                # plt.plot(self.nthreads, y_vals, label=target)

            # plt.legend()
            # plt.xlabel("threads")
            # plt.ylabel("MOPS/s")
            # plt.title("Loop: " + str(size) + "B")
            # plt.savefig("Loop." + str(size) + "B.png")
            # plt.clf()

        # # NTHREADS fixed
        # y_mapping = {v : i for i, v in enumerate(self.maxsize)}
        # x_vals = [i + 1 for i in range(0, len(self.maxsize))]
        # for n in self.nthreads:
            # for target in self.targets:
                # y_vals = [0] * len(self.maxsize)
                # for mid, measures in self.results.items():
                    # if mid[0] == target and mid[1] == n:
                        # d = []
                        # for m in measures:
                            # # nthreads/time = MOPS/S
                            # d.append(n/float(m["cpu-clock:ku"]))
                        # y_vals[y_mapping[mid[2]]] = np.mean(d)
                # plt.plot(x_vals, y_vals, label=target)

            # plt.legend()
            # plt.xticks(x_vals, self.maxsize)
            # plt.xlabel("size in B")
            # plt.ylabel("MOPS/s")
            # plt.title("Loop: " + str(n) + "thread(s)")
            # plt.savefig("Loop." + str(n) + "thread.png")
            # plt.clf()
        
mysql = Benchmark_MYSQL()
