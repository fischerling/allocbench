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
import logging
import os
import traceback

from allocbench.util import find_cmd, print_status

logger = logging.getLogger(__file__)


def build_analyze_alloc():
    """Select and build available analysis allocator"""
    if find_cmd("malt") is not None:
        alloc_name = "malt"
    else:
        logger.warning("malt not found. Using chattymalloc.")
        alloc_name = "chattymalloc"

    analyze_alloc_module = importlib.import_module(
        f"allocbench.allocators.{alloc_name}")

    return alloc_name, getattr(analyze_alloc_module, alloc_name).build()


def analyze_bench(bench):
    """Analyse a single benchmark"""
    print_status("Analysing {} ...".format(bench))

    # Create benchmark result directory
    if not os.path.isdir(bench.result_dir):
        logger.info("Creating benchmark result dir: %s", bench.result_dir)
        os.makedirs(bench.result_dir, exist_ok=True)

    alloc_name, alloc_dict = build_analyze_alloc()

    old_allocs = bench.allocators
    old_measure_cmd = bench.measure_cmd
    bench.measure_cmd = ""
    bench.allocators = {alloc_name: alloc_dict}

    try:
        bench.run(runs=1)
    except Exception:  #pylint: disable=broad-except
        logger.debug("%s", traceback.format_exc())
        logger.error("Skipping analysis of %s!", bench)

    bench.measure_cmd = old_measure_cmd

    # Remove results for analyze_alloc
    if alloc_name in bench.results:
        del bench.results[alloc_name]
    if "stats" in bench.results and alloc_name in bench.results["stats"]:
        del bench.results["stats"][alloc_name]

    # restore allocs
    bench.allocators = old_allocs


def analyze_allocators(bench, allocators):
    """Analyse a single benchmark for each allocator in allocators"""
    # build analyzse allocator before globaly setting LD_PRELOAD
    alloc_name, _ = build_analyze_alloc()

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
                perm_fmt = alloc_name

            old_trace = os.path.join(bench.result_dir, f"{perm_fmt}.trace")
            new_trace = os.path.join(bench.result_dir,
                                     f"{name}_{perm_fmt}.trace")
            os.rename(old_trace, new_trace)
