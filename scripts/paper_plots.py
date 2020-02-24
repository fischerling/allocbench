#!/usr/bin/env python3

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
"""Create pgfplots used in our paper"""

import argparse
import importlib
import inspect
import os
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import src.allocators.paper
import src.facter
import src.globalvars
import src.plots as plt
from src.util import print_status, print_debug, print_error
from src.util import print_license_and_exit

ALLOCATOR_NAMES = [a.name for a in src.allocators.paper.allocators]
SURVEY_ALLOCATORS = [a.name for a in src.allocators.paper.allocators if not '-' in a.name]
TCMALLOCS = [a.name for a in src.allocators.paper.allocators if a.name.startswith("TCMalloc")]
ALIGNED_ALLOCATORS = [a.name for a in src.allocators.paper.allocators if a.name.endswith("-Aligned")]

COLORS=True

def falsesharing_plots(falsesharing):
    args = falsesharing.results["args"]
    nthreads = args["threads"]

    falsesharing.results["allocators"] = {k: v for k, v in falsesharing.results["allocators"].items() if k in ALLOCATOR_NAMES}

    plt.pgfplot_legend(falsesharing, colors=COLORS, columns=5)

    # calculate relevant datapoints: speedup, l1-cache-misses
    for bench in falsesharing.results["args"]["bench"]:
        for allocator in falsesharing.results["allocators"]:

            sequential_perm = falsesharing.Perm(bench=bench, threads=1)
            for perm in falsesharing.iterate_args_fixed({"bench": bench}, args=args):
                speedup = []
                l1chache_misses = []
                for i, measure in enumerate(falsesharing.results[allocator][perm]):
                    sequential_time = float(falsesharing.results[allocator]
                            [sequential_perm][i]["time"])
                    measure["speedup"] = sequential_time / float(
                            measure["time"])
                    measure["l1chache_misses"] = eval(
                            "({L1-dcache-load-misses}/{L1-dcache-loads})*100".
                            format(**measure))

    # delete and recalculate stats
    del falsesharing.results["stats"]
    falsesharing.calc_desc_statistics()

    # pgfplots
    for bench in args["bench"]:
        plt.pgfplot(falsesharing,
                    falsesharing.iterate_args_fixed({"bench": bench}, args=args),
                    "int(perm.threads)",
                    "{speedup}",
                    xlabel="Threads",
                    ylabel="Speedup",
                    title=f"{bench}: Speedup",
                    postfix=f"{bench}.speedup",
                    colors=COLORS)

def blowup_plots(blowup):
    args = blowup.results["args"]
    blowup.results["allocators"] = {k: v for k, v in blowup.results["allocators"].items() if k in ALLOCATOR_NAMES}

    # hack ideal rss in data set
    blowup.results["allocators"]["Ideal-RSS"] = {"color": "xkcd:gold"}
    blowup.results["stats"]["Ideal-RSS"] = {}
    for perm in blowup.iterate_args(args=args):
        blowup.results["stats"]["Ideal-RSS"][perm] = {
                "mean": {
                    "VmHWM": 1024 * 100
                    },
                "std": {
                    "VmHWM": 0
                    }
                }

    plt.pgfplot(blowup,
                blowup.iterate_args(args),
                "'blowup'",
                "{VmHWM}/1000",
                xlabel="",
                ylabel="VmHWM in MB",
                title="blowup test",
                postfix="vmhwm",
                axis_attr="\txtick=data,\n\tsymbolic x coords={blowup}",
                bar=True,
                colors=COLORS)

def mysqld_plots(mysql):
    args = mysql.results["args"]
    mysql.results["allocators"] = {k: v for k, v in mysql.results["allocators"].items() if k in SURVEY_ALLOCATORS}

    plt.pgfplot(mysql,
                mysql.iterate_args(args),
                "int(perm.nthreads)",
                "{mysqld_vmhwm}/1000",
                xlabel="threads",
                ylabel="VmHWM in MB",
                title="Memusage sysbench mysql benchmark",
                postfix="vmhwm",
                axis_attr="\tybar=0, \tbar width=3",
                colors=COLORS)

    plt.pgfplot(mysql,
                mysql.iterate_args(args),
                "int(perm.nthreads)",
                "{transactions}",
                xlabel="threads",
                ylabel="transactions",
                title="Transactions sysbench mysql benchmark",
                postfix="transactions",
                axis_attr="\tybar=0, \tbar width=3",
                colors=COLORS)

def keydb_plots(keydb):
    args = keydb.results["args"]
    keydb.results["allocators"] = {k: v for k, v in keydb.results["allocators"].items() if k in SURVEY_ALLOCATORS}

    for fixed_arg in args:
        loose_arg = [a for a in args if a != fixed_arg][0]
        for arg_value in args[fixed_arg]:
            plt.pgfplot(keydb,
                        keydb.iterate_args_fixed({fixed_arg: arg_value}, args),
                        f"int(perm.{loose_arg})",
                        "{totals_ops}",
                        xlabel=f"{loose_arg}",
                        ylabel="Total Operations",
                        title=f"KeyDB Operations: {fixed_arg} {arg_value}",
                        postfix=f"{fixed_arg}.{arg_value}",
                        bar=True,
                        colors=COLORS)


def summarize(benchmarks=None, exclude_benchmarks=None):
    """summarize the benchmarks in the resdir"""

    cwd = os.getcwd()

    for benchmark, func in {"blowup": blowup_plots, "falsesharing": falsesharing_plots,
                            "mysql": mysqld_plots, "keydb": keydb_plots}.items():
        if benchmarks and not benchmark in benchmarks:
            continue
        if exclude_benchmarks and benchmark in exclude_benchmarks:
            continue

        bench_module = importlib.import_module(f"src.benchmarks.{benchmark}")

        if not hasattr(bench_module, benchmark):
            print_error(f"{benchmark} has no member {benchmark}")
            print_error(f"Skipping {benchmark}.")

        bench = getattr(bench_module, benchmark)

        try:
            bench.load(src.globalvars.resdir)
        except FileNotFoundError:
            print_warn(f"Skipping {bench.name}. No results found")
            continue

        print_status(f"Summarizing {bench.name} ...")

        res_dir = os.path.join(src.globalvars.resdir, bench.name, "paper")
        if not os.path.isdir(res_dir):
            os.makedirs(res_dir)
        os.chdir(res_dir)
        func(bench)
        os.chdir(cwd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Summarize allocbench results in allocator sets")
    parser.add_argument("results", help="path to results", type=str)
    parser.add_argument("--license",
                        help="print license info and exit",
                        action='store_true')
    parser.add_argument("--version",
                        help="print version info and exit",
                        action='version',
                        version=f"allocbench {src.facter.allocbench_version()}")
    parser.add_argument("-v", "--verbose", help="more output", action='count')
    parser.add_argument("-b",
                        "--benchmarks",
                        help="benchmarks to summarize",
                        nargs='+')
    parser.add_argument("-x",
                        "--exclude-benchmarks",
                        help="benchmarks to exclude",
                        nargs='+')
    parser.add_argument("--latex-preamble",
                        help="latex code to include in the preamble of generated standalones",
                        type=str)
    parser.add_argument("--no-colors",
                        help="don't use matplotlib colors for pgfplots",
                        action="store_true")

    args = parser.parse_args()

    if args.verbose:
        src.globalvars.verbosity = args.verbose

    if args.latex_preamble:
        src.globalvars.latex_custom_preamble = args.latex_preamble

    if not os.path.isdir(args.results):
        print_error(f"{args.results} is no directory")
        sys.exit(1)

    if args.no_colors:
        COLORS=False

    src.globalvars.resdir = args.results

    # Load facts
    src.facter.load_facts(src.globalvars.resdir)

    summarize(benchmarks=args.benchmarks,
              exclude_benchmarks=args.exclude_benchmarks)
