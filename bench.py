#!/usr/bin/env python3

from bench_loop import loop
from bench_conprod import conprod
from bench_mysql import mysql

benchmarks = [loop, conprod, mysql]

def main():
    for bench in benchmarks:
        print("Preparing", bench.name)
        if not bench.prepare():
            continue
        print("Running", bench.name)
        if not bench.run(runs=1):
            continue
        print("Summarizing", bench.name)
        bench.summary()
        if hasattr(bench, "cleanup"):
            print("Cleaning after", bench.name)
            bench.cleanup()

if __name__ == "__main__":
    main()
