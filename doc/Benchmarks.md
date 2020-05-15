# Benchmarks

A benchmark in the context of allocbench is a command usable with exec and a
list of all possible arguments. The command is executed and measured for each
permutation of the specified arguments and for each allocator to test.

Benchmarks are implemented as python objects that have a function `run(runs)`.
Other non mandatory functions are:

* load
* prepare
* save
* summary
* cleanup

## Included Benchmarks

### loop

A really simple benchmark that allocates and frees one randomly sized block per
iteration. This benchmark measures mostly the fastpaths of the allocators.
Allocations are not written or read because this is done by the next benchmark.

### falsesharing

This benchmark consists of two similar programs written by Emery Berger for
his [Hoard](https://github.com/emeryberger/Hoard/tree/master/benchmarks) allocator.
They test allocator introduced false sharing.

### larson server benchmark

A benchmark simulating a server application written by Paul Larson at
Microsoft for its research on memory allocators [[paper]](https://dl.acm.org/citation.cfm?id=286880).

### mysql

Read-only SQL benchmark using mysqld and sysbench to simulate "real" workloads.

### DJ Delorie traces

Rerun of [traces](http://www.delorie.com/malloc/) collected and provided by DJ
Delorie using the tools from dj/malloc branch of the glibc.

## Add your own Benchmark

1. Make sure your command is deterministic and allocator behavior is a significant
	part of your measured results
2. Create a new Python class for your benchmark. You can inherit from the
	provided class allocbench.Benchmark.
3. Implement your custom functionality
4. Export a object of your class in a python file under allocbench/benchmarks named
	like your exported object and allocbench will find it automatically.

#### loop.py as Example

```python
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

"""Definition of the loop micro benchmark"""

from allocbench.benchmark import Benchmark


class BenchmarkLoop(Benchmark):
    """Loop micro benchmark

    This benchmark allocates and frees n blocks in t concurrent threads.
    """

    def __init__(self):
        name = "loop"

        self.cmd = "loop{binary_suffix} {nthreads} 1000000 {maxsize}"

        self.args = {"maxsize":  [2 ** x for x in range(6, 16)],
                     "nthreads": Benchmark.scale_threads_for_cpus(2)}

        self.requirements = ["loop"]
        super().__init__(name)

    def summary(self):
        # Speed
        self.plot_fixed_arg("perm.nthreads / ({task-clock}/1000)",
                            ylabel='"MOPS/cpu-second"',
                            title='"Loop: " + arg + " " + str(arg_value)',
                            filepostfix="time",
                            autoticks=False)

        scale = list(self.results["allocators"].keys())[0]
        self.plot_fixed_arg("perm.nthreads / ({task-clock}/1000)",
                            ylabel='"MOPS/cpu-second normalized {}"'.format(scale),
                            title=f'"Loop: " + arg + " " + str(arg_value) + " normalized {scale}"',
                            filepostfix="time.norm",
                            scale=scale,
                            autoticks=False)

        # L1 cache misses
        self.plot_fixed_arg("({L1-dcache-load-misses}/{L1-dcache-loads})*100",
                            ylabel='"L1 misses in %"',
                            title='"Loop l1 cache misses: " + arg + " " + str(arg_value)',
                            filepostfix="l1misses",
                            autoticks=False)

        # Speed Matrix
        self.write_best_doublearg_tex_table("perm.nthreads / ({task-clock}/1000)",
                                            filepostfix="time.matrix")

        self.export_stats_to_csv("task-clock")
        self.export_stats_to_dataref("task-clock")


loop = BenchmarkLoop()
```

## The Benchmark class

The class Benchmark defined in the allocbench/benchmark.py implements most
common operations for a benchmark.
It provides load and save functions using pythons json module,
helpers generating plots using matplotlib and most importantly a run method using
the attributes `cmd` and `args` to execute your benchmark. To not enforce some
output format hooks are available to parse the output of your benchmark yourself.

### run

```
for number_of_runs
	for each allocator
		preallocator_hook

		for each permutation of args
			buildup command
			run command

			process_output

		postallocator_hook
```

#### run hooks

* `preallocator_hook((alloc_name, alloc_definition), current_run, environment)` is called
	if available once per allocator before any command is executed. This hook may
	be useful if you want to prepare stuff for each allocator. The mysql benchmark
	uses this hook to start the mysql server with the current allocator.

* `process_output(result_dict, stdout, stderr, allocator_name, permutation)`
	is called after each run of your command. Store relevant data in result_dict
	to use it for your summary.

* `postallocator_hook((alloc_name, alloc_definition), current_run)`
	is called after all permutations are done for the current allocator.
	The mysql benchmark uses this hook to terminate the in preallocator_hook started
	mysql server.

### plot helpers
