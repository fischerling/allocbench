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
"""llvm-lld speed benchmark

This benchmark runs the lld speed benchmark provided by the llvm project.
The archive contains compiled object files and linker instructions
for prominent software projects.
The benchmark starts lld in each project and measures lld's execution time.
Lld uses all available execution units.

Included workloads are (allocator functions with call count < 100 are neglected):
Checksum: 2d449a11109c7363f67fd45513b42270f5ba2a92
* chromium
    * Version: 50.0.2638.0
    * allocator calls: 728968
        * malloc: 585155 (80%)
        * free:   143660 (20%)
    * Approximate allocator ratios:
        * malloc: 1.33%
        * free:   0.22%
    * Top 10 allocation sizes 66.59% of all allocations
      1. 32 B occurred 96691 times
      2. 64 B occurred 84242 times
      3. 128 B occurred 51477 times
      4. 96 B occurred 36551 times
      5. 256 B occurred 29329 times
      6. 160 B occurred 22882 times
      7. 192 B occurred 20409 times
      8. 16 B occurred 16843 times
      9. 224 B occurred 15886 times
      10. 512 B occurred 15448 times

      allocations <= 64:› 217964› 37.24%
      allocations <= 1024:›   542138› 92.62%
      allocations <= 4096:›   572589› 97.83%

* mozilla
    * allocator calls: 565923
        * malloc: 446864 (79%)
        * free:   118928 (21%)
    * Approximate allocator ratios:
        * malloc: 0.19%
        * free:   0.07%
    * Top 10 allocation sizes 86.56% of all allocations
      1. 32 B occurred 161545 times
      2. 64 B occurred 70863 times
      3. 24 B occurred 46400 times
      4. 40 B occurred 34304 times
      5. 96 B occurred 25742 times
      6. 128 B occurred 16993 times
      7. 160 B occurred 10670 times
      8. 256 B occurred 9157 times
      9. 192 B occurred 6357 times
      10. 224 B occurred 4878 times

      allocations <= 64:   317816 71.10%
      allocations <= 1024: 419747 93.90%
      allocations <= 4096: 430815 96.38%

* linux kernel
    * Linux version 4.14.0-rc1+ (fedora@ip-172-31-12-81.us-west-2.compute.internal)
      (gcc version 7.2.1 20170915 (Red Hat 7.2.1-2) (GCC)) #2 SMP Wed Sep 20 21:57:18 UTC 2017
    * allocator calls:  8607279
        * malloc: 4328149 (50%)
        * free:   4279068 (50%)
    * Approximate allocator ratios:
        * malloc: 3.82%
        * free:   6.03%
    * Top 10 allocation sizes 77.95% of all allocations
      1. 57 B occurred 1420196 times
      2. 29 B occurred 1368747 times
      3. 50 B occurred 89909 times
      4. 48 B occurred 76702 times
      5. 56 B occurred 73398 times
      6. 55 B occurred 71073 times
      7. 51 B occurred 70718 times
      8. 53 B occurred 69945 times
      9. 49 B occurred 67552 times
      10. 52 B occurred 65639 times

      allocations <= 64:   4114410 95.06%
      allocations <= 1024: 4320775 99.83%
      allocations <= 4096: 4325016 99.93%

* scylla - NoSQL data store https://github.com/scylladb/scylla
    * allocator calls: 106968
        * malloc: 66984 (63%)
        * free:   39884 (37%)
    * Approximate allocator ratios:
        * malloc: 0.06%
        * free:   0.04%
    * Top 10 allocation sizes 73.65% of all allocations
      1. 24 B occurred 18005 times
      2. 40 B occurred 13089 times
      3. 96 B occurred 3693 times
      4. 128 B occurred 3280 times
      5. 32 B occurred 2827 times
      6. 64 B occurred 2728 times
      7. 256 B occurred 1596 times
      8. 160 B occurred 1553 times
      9. 192 B occurred 1371 times
      10. 4096 B occurred 1268 times

      allocations <= 64:   38375 57.20%
      allocations <= 1024: 59302 88.40%
      allocations <= 4096: 63005 93.92%

* llvm variants (as-fsds, as)
    * allocator calls: 21074 | 23508
        * malloc:      61%   | 58%
        * free:        38%   | 41%
    * Approximate allocator ratios:
        * malloc: 1.26% | 0.93%
        * free:   1.13% | 0.69%)
    * Top 10 allocation sizes 74.77%    | Top 10 allocation sizes 82.64% of all allocations
      1. 24 B occurred 4453 times       | 1. 24 B occurred 5742 times
      2. 40 B occurred 3067 times       | 2. 40 B occurred 3908 times
      3. 4096 B occurred 581 times      | 3. 4096 B occurred 535 times
      4. 32 B occurred 291 times        | 4. 80 B occurred 240 times
      5. 8192 B occurred 260 times      | 5. 64 B occurred 196 times
      6. 64 B occurred 252 times        | 6. 32 B occurred 191 times
      7. 96 B occurred 233 times        | 7. 8192 B occurred 189 times
      8. 80 B occurred 227 times        | 8. 8 B occurred 180 times
      9. 128 B occurred 197 times       | 9. 128 B occurred 163 times
      10. 256 B occurred 178 times      | 10. 96 B occurred 159 times

      allocations <= 64:   8668  66.55% | allocations <= 64:>.10722>..77.03%
      allocations <= 1024: 11646 89.41% | allocations <= 1024:>...12783>..91.83%
      allocations <= 4096: 12597 96.71% | allocations <= 4096:>...13543>..97.29%

* llvm gold LTO plugin (gold, gold-fsds)
    * allocator calls: 66302 | 87841
        * malloc:        64% | 71%
        * free:          35% | 29%
    * Approximate allocator ratios:
        * malloc: 0.69% | 1.02%
        * free:   0.32% | 0.37%
    * Top 10 allocation sizes 62.19%    | Top 10 allocation sizes 57.24%
      1. 24 B occurred 7574 times       | 1. 24 B occurred 9563 times
      2. 40 B occurred 5406 times       | 2. 40 B occurred 6833 times
      3. 32 B occurred 2587 times       | 3. 32 B occurred 3843 times
      4. 64 B occurred 2350 times       | 4. 64 B occurred 3740 times
      5. 128 B occurred 2233 times      | 5. 128 B occurred 2974 times
      6. 256 B occurred 1621 times      | 6. 160 B occurred 2092 times
      7. 16 B occurred 1551 times       | 7. 256 B occurred 2055 times
      8. 512 B occurred 1316 times      | 8. 512 B occurred 1586 times
      9. 4096 B occurred 1198 times     | 9. 96 B occurred 1579 times
      10. 160 B occurred 818 times      | 10. 16 B occurred 1424 times

      allocations <= 64:   20501 47.83% | allocations <= 64:   26093 41.85%
      allocations <= 1024: 37224 86.85% | allocations <= 1024: 53860 86.38%
      allocations <= 4096: 40646 94.83% | allocations <= 4096: 59821 95.94%

* clang (clang, clang-fsds, clang-gdb-index)
    * allocator calls: 70378 | 111081 | 1271367
        * malloc:        70% |    81% | 59%
        * free:          30% |    19% | 29%
        * realloc:       0%  |    0%  | 11%
    * Approximate allocator ratios:
        * malloc:  0.68% | 0.95% | 0.82%
        * free:    0.29% | 0.20% | 0.32%
        * realloc: 0%    | 0%    | 0.10%
    * Top 10 allocation sizes 52.99%    | Top 10 allocation sizes 49.91%    | Top 10 allocation sizes 83.46%
      1. 24 B occurred 7916 times       | 1. 24 B occurred 8503 times       | 1. 32 B occurred 205122 times
      2. 40 B occurred 5788 times       | 2. 40 B occurred 6286 times       | 2. 4 B occurred 127071 times
      3. 32 B occurred 2192 times       | 3. 32 B occurred 5507 times       | 3. 16 B occurred 110454 times
      4. 128 B occurred 1969 times      | 4. 64 B occurred 5289 times       | 4. 24 B occurred 61859 times
      5. 64 B occurred 1958 times       | 5. 128 B occurred 4306 times      | 5. 64 B occurred 58384 times
      6. 256 B occurred 1505 times      | 6. 160 B occurred 3743 times      | 6. 80 B occurred 53354 times
      7. 4096 B occurred 1318 times     | 7. 96 B occurred 3319 times       | 7. 40 B occurred 44931 times
      8. 160 B occurred 1305 times      | 8. 256 B occurred 2762 times      | 8. 8 B occurred 36572 times
      9. 320 B occurred 1140 times      | 9. 192 B occurred 2592 times      | 9. 96 B occurred 25162 times
      10. 512 B occurred 1099 times     | 10. 320 B occurred 2433 times     | 10. 160 B occurred 23729 times

      allocations <= 64:   19989 40.44% | allocations <= 64:   26994 30.11% | allocations <= 64:   649038 72.55%
      allocations <= 1024: 41806 84.58% | allocations <= 1024: 75184 83.87% | allocations <= 1024: 847322 94.72%
      allocations <= 4096: 46102 93.28% | allocations <= 4096: 85490 95.37% | allocations <= 4096: 871017 97.37%

Interpretation:

The raw speed of the allocator likewise is not a huge factor because of the small
small portion of the total execution time (around 1% except scylla and linux).
So data locality and scalability should be the most important factor for those workloads.
"""

import os

import matplotlib.pyplot as plt

from allocbench.artifact import ArchiveArtifact
from allocbench.benchmark import Benchmark
import allocbench.facter as facter
import allocbench.plots
from allocbench.globalvars import SUMMARY_FILE_EXT


class BenchmarkLld(Benchmark):
    """LLVM-lld speed benchmark definition"""
    def __init__(self):
        name = "lld"

        self.run_dir = "{test_dir}/lld-speed-test/{test}"
        # TODO: don't hardcode ld.lld location
        self.cmd = "/usr/bin/ld.lld @response.txt"

        self.args = {
            "test": [
                "chrome", "clang-fsds", "gold", "linux-kernel", "llvm-as-fsds",
                "scylla", "clang", "clang-gdb-index", "gold-fsds", "llvm-as",
                "mozilla"
            ]
        }

        self.measure_cmd = "perf stat -x, -d time -f %M,KB,VmHWM"
        self.measure_cmd_csv = True
        self.requirements = ["ld.lld"]

        self.tests_artifact = ArchiveArtifact(
            "lld-speed-test",
            "https://s3-us-west-2.amazonaws.com/linker-tests/lld-speed-test.tar.xz",
            "tar", "2d449a11109c7363f67fd45513b42270f5ba2a92")
        self.test_dir = None

        super().__init__(name)

    def prepare(self):
        """Download and extract lld test files"""
        super().prepare()

        # save lld version
        self.results["facts"]["versions"]["lld"] = facter.exe_version(
            "ld.lld", "-v")

        self.test_dir = self.tests_artifact.provide()

    def cleanup(self):
        for perm in self.iterate_args():
            a_out = os.path.join(self.test_dir, "lld-speed-test", perm.test,
                                 "a.out")
            if os.path.isfile(a_out):
                os.remove(a_out)

    def summary(self):
        args = self.results["args"]
        allocators = self.results["allocators"]
        stats = self.results["stats"]

        for perm in self.iterate_args(args=args):
            for i, allocator in enumerate(allocators):

                plt.bar([i],
                        stats[allocator][perm]["mean"]["task-clock"],
                        yerr=stats[allocator][perm]["std"]["task-clock"],
                        label=allocator,
                        color=allocators[allocator]["color"])

            plt.legend(loc="best")
            plt.ylabel("time in ms")
            plt.title(f"Runtime {perm.test}")
            plt.savefig(f"{self.name}.{perm.test}.runtime.{SUMMARY_FILE_EXT}")
            plt.clf()

            for i, alloc in enumerate(allocators):
                plt.bar([i],
                        stats[alloc][perm]["mean"]["VmHWM"] / 1000,
                        yerr=stats[alloc][perm]["std"]["VmHWM"] / 1000,
                        label=alloc,
                        color=allocators[alloc]["color"])

            plt.legend(loc="best")
            plt.ylabel("Max RSS in MB")
            plt.title(f"Max RSS {perm.test}")
            plt.savefig(f"{self.name}.{perm.test}.rss.{SUMMARY_FILE_EXT}")
            plt.clf()

        # self.export_stats_to_csv("VmHWM")
        allocbench.plots.export_stats_to_csv(self, "task-clock")

        # self.export_stats_to_dataref("VmHWM")
        allocbench.plots.export_stats_to_dataref(self, "task-clock")

        allocbench.plots.write_tex_table(self, [{
            "label": "Runtime [ms]",
            "expression": "{task-clock}",
            "sort": "<"
        }],
                                         file_postfix="table")
