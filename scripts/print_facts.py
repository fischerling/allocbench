#!/usr/bin/env python3

# Copyright 2018-2020 Florian Fischer <florian.fl.fischer@fau.de>
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
"""Print facts about an allocbench result directory"""

import argparse
import os
import sys

CURRENTDIR = os.path.dirname(os.path.abspath(__file__))
PARENTDIR = os.path.dirname(CURRENTDIR)
sys.path.insert(0, PARENTDIR)

# pylint: disable=wrong-import-position
from allocbench.benchmark import AVAIL_BENCHMARKS, get_benchmark_object
import allocbench.facter as facter
from allocbench.plots import print_facts, print_common_facts
# pylint: enable=wrong-import-position


def main():
    """Print facts about an allocbench benchmark results"""
    parser = argparse.ArgumentParser(
        description="Print facts about an allocbench result directory")
    parser.add_argument("results", help="path to allocbench results", type=str)
    args = parser.parse_args()

    # Load common facts
    facter.load_facts(args.results)

    print_common_facts()

    cwd = os.getcwd()
    os.chdir(args.results)

    for benchmark in AVAIL_BENCHMARKS:
        bench = get_benchmark_object(benchmark)

        try:
            bench.load()
        except FileNotFoundError:
            continue

        print_facts(bench, print_allocators=True, print_common=False)

    os.chdir(cwd)


if __name__ == "__main__":
    main()
