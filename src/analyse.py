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
"""Analyze benchmarks and allocators"""

import importlib
import os
import traceback

from src.util import find_cmd
from src.util import print_status, print_warn, print_error
from src.util import print_info2, print_debug

ANALYZSE_ALLOC_NAME = None
ANALYZSE_ALLOC_DICT = None


def build_analyze_alloc():
    """Select and build available analysis allocator"""
    global ANALYZSE_ALLOC_NAME
    global ANALYZSE_ALLOC_DICT
    if ANALYZSE_ALLOC_DICT is not None:
        return

    if find_cmd("malt") is not None:
        ANALYZSE_ALLOC_NAME = "malt"
    else:
        print_warn("malt not found. Using chattymalloc.")
        ANALYZSE_ALLOC_NAME = "chattymalloc"

    analyze_alloc_module = importlib.import_module(
        f"src.allocators.{ANALYZSE_ALLOC_NAME}")

    ANALYZSE_ALLOC_DICT = getattr(analyze_alloc_module,
                                  ANALYZSE_ALLOC_NAME).build()


def analyze_bench(bench):
    """Analyse a single benchmark"""
    print_status("Analysing {} ...".format(bench))

    # Create benchmark result directory
    if not os.path.isdir(bench.result_dir):
        print_info2("Creating benchmark result dir:", bench.result_dir)
        os.makedirs(bench.result_dir, exist_ok=True)

    build_analyze_alloc()

    old_allocs = bench.allocators
    old_measure_cmd = bench.measure_cmd
    bench.measure_cmd = ""
    bench.allocators = {ANALYZSE_ALLOC_NAME: ANALYZSE_ALLOC_DICT}

    try:
        bench.run(runs=1)
    except Exception:
        print_debug(traceback.format_exc())
        print_error("Skipping analysis of", bench, "!")

    bench.measure_cmd = old_measure_cmd

    # Remove results for analyze_alloc
    if ANALYZSE_ALLOC_NAME in bench.results:
        del bench.results[ANALYZSE_ALLOC_NAME]
    if "stats" in bench.results and ANALYZSE_ALLOC_NAME in bench.results[
            "stats"]:
        del bench.results["stats"][ANALYZSE_ALLOC_NAME]

    # restore allocs
    bench.allocators = old_allocs


def analyze_allocators(bench, allocators):
    """Analyse a single benchmark for each allocator in allocators"""
    for name, alloc in allocators.items():
        print_status(f"Analysing {name} during {bench} ...")
        os.environ["LD_PRELOAD"] = alloc["LD_PRELOAD"]
        analyze_bench(bench)

        # save the resulting trace
        for perm in bench.iterate_args():
            if bench.servers == []:
                if perm:
                    perm_fmt = ("{}-" * (len(perm) - 1) + "{}").format(*perm)
                else:
                    perm_fmt = ""
            else:
                perm_fmt = ANALYZSE_ALLOC_NAME

            old_trace = os.path.join(bench.result_dir, f"{perm_fmt}.trace")
            new_trace = os.path.join(bench.result_dir,
                                     f"{name}_{perm_fmt}.trace")
            os.rename(old_trace, new_trace)
