# allocbench - benchmark tool for POSIX memory allocators

To download allocbench run

```shell
git clone https://muhq.space/software/allocbench.git
```

## Requirements

* python3
* perf (`perf stat -d` is the default command to measure benchmark results)
* util-linux (`whereis` is used to find system installed allocators)
* (git to clone allocators in `allocators/{no_falsesharing, BA_allocators}.py`)


## Usage

	usage: bench.py [-h] [-s] [-l LOAD] [-a ALLOCATORS] [-r RUNS] [-v]
	                [-b BENCHMARKS [BENCHMARKS ...]] [-ns] [-rd RESULTDIR]
	                [--license]

	benchmark memory allocators

	optional arguments:
	  -h, --help            show this help message and exit
	  -s, --save            save benchmark results in RESULTDIR
	  -l LOAD, --load LOAD  load benchmark results from directory
	  -a ALLOCATORS, --allocators ALLOCATORS
	                        load allocator definitions from file
	  -r RUNS, --runs RUNS  how often the benchmarks run
	  -v, --verbose         more output
	  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
	                        benchmarks to run
	  -ns, --nosum          don't produce plots
	  -rd RESULTDIR, --resultdir RESULTDIR
	                        directory where all results go
	  --license             print license info and exit

### Examples

	./bench.py -b loop

runs only the loop benchmark for some installed allocators and will put its
results in `$PWD/results/$HOSTNAME/<time>/loop`

	./bench.py -a allocators/BA_allocators.py

builds all allocators used in my [BA thesis](https://muhq.space/ba.html) and runs all
default benchmarks

	./bench.py -r 0 -l <path/to/saved/results>

doesn't run any benchmark just summarizes the loaded results

## Benchmarks

You want to compare allocators with your own software or add a new benchmark,
have a look at [](doc/Benchmarks.md).

## Allocators

By default tcmalloc, jemalloc, Hoard and your libc's allocator will be used
if found and the `-a` option is not used.

For more control about used allocators have a look at [](doc/Allocators.md).

## License

This program is released under GPLv3. You can find a copy of the license
in the LICENSE file in the programs root directory.
