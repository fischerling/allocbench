# allocbench - benchmark tool for POSIX memory allocators

To download allocbench run

```shell
git clone https://muhq.space/software/allocbench.git
```

## Requirements

* python3
* make, find, gcc (build dependencies)
* perf (`perf stat -d` is the default command to measure benchmark results)
* util-linux (`whereis` is used to find system installed allocators)
* (git to clone allocators in `src/allocators/*.py`)


## Usage

	usage: bench.py [-h] [-ds, --dont-save] [-l LOAD] [--analyse] [-r RUNS] [-v]
	                [-vdebug] [-b BENCHMARKS [BENCHMARKS ...]]
	                [-xb EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...]]
	                [-a ALLOCATORS [ALLOCATORS ...]] [-ns] [-rd RESULTDIR]
	                [--license]

	benchmark memory allocators

	optional arguments:
	  -h, --help            show this help message and exit
	  -ds, --dont-save      don't save benchmark results in RESULTDIR
	  -l LOAD, --load LOAD  load benchmark results from directory
	  --analyse             analyse benchmark behaviour using malt
	  -r RUNS, --runs RUNS  how often the benchmarks run
	  -v, --verbose         more output
	  -vdebug, --verbose-debug
	                        debug output
	  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
	                        benchmarks to run
	  -xb EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...], --exclude-benchmarks EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...]
	                        explicitly excluded benchmarks
	  -a ALLOCATORS [ALLOCATORS ...], --allocators ALLOCATORS [ALLOCATORS ...]
	                        allocators to test
	  -ns, --nosum          don't produce plots
	  -rd RESULTDIR, --resultdir RESULTDIR
	                        directory where all results go
	  --license             print license info and exit

### Examples

	./bench.py -b loop

runs only the loop benchmark for some installed allocators and will put its
results in `$PWD/results/$HOSTNAME/<time>/loop`

	./bench.py -a BA_allocators

builds all allocators used in Florian Fischer's [BA thesis](https://muhq.space/ba.html)
and runs all benchmarks

	./bench.py -r 0 -l <path/to/saved/results>

doesn't run any benchmark just summarizes the loaded results

## Benchmarks

You want to compare allocators with your own software or add a new benchmark,
have a look at [doc/Benchmarks.md](doc/Benchmarks.md).

## Allocators

By default tcmalloc, jemalloc, Hoard and your libc's allocator will be used
if found and the `-a` option is not used.

For more control about used allocators have a look at [doc/Allocators.md](doc/Allocators.md).

## License

This program is released under GPLv3. You can find a copy of the license
in the LICENSE file in the programs root directory.
