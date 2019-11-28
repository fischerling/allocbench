# allocbench - benchmark tool for POSIX memory allocators

allocbench is a POSIX memory allocator benchmarking framework and tooling.

To obtain allocbench run

```shell
git clone https://muhq.space/software/allocbench.git
```

## Requirements

* python >= 3.6
* make, find, gcc (build dependencies)
* perf (`perf stat -d` is the default command to measure benchmark results)
* util-linux (`whereis` is used to find system installed allocators)
* git, tar to handle external artifacts
* numpy and matplotlib to summarize results and generate plots


## Usage
allocbench consists of three small utilities: `bench.py`, `summarize.py` and `merge.py`.
`bench.py` is used to prepare, analyze and run benchmarks.

	usage: bench.py [-h] [--analyze] [-r RUNS] [-v]
	                [-b BENCHMARKS [BENCHMARKS ...]]
	                [-xb EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...]]
	                [-a ALLOCATORS [ALLOCATORS ...]] [-rd RESULTDIR] [--license]
	                [--version]

	benchmark memory allocators

	optional arguments:
	  -h, --help            show this help message and exit
	  --analyze             analyze benchmark behavior using malt
	  -r RUNS, --runs RUNS  how often the benchmarks run
	  -v, --verbose         more output
	  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
	                        benchmarks to run
	  -xb EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...], --exclude-benchmarks EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...]
	                        explicitly excluded benchmarks
	  -a ALLOCATORS [ALLOCATORS ...], --allocators ALLOCATORS [ALLOCATORS ...]
	                        allocators to test
	  -rd RESULTDIR, --resultdir RESULTDIR
	                        directory where all results go
	  --license             print license info and exit
	  --version             print version info and exit

`./summarize.py` is used to summarize results created with bench.py.
It groups the included allocators into categories to produce readable and not extremely noisy plots.

	usage: summarize.py [-h] [-t FILE_EXT] [--license] [--version]
	                    [-b BENCHMARKS [BENCHMARKS ...]]
	                    [-x EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...]]
	                    results

	Summarize allocbench results in allocator sets

	positional arguments:
	  results               path to results

	optional arguments:
	  -h, --help            show this help message and exit
	  -t FILE_EXT, --file-ext FILE_EXT
	                        file extension used for plots
	  --license             print license info and exit
	  --version             print version info and exit
	  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
	                        benchmarks to summarize
	  -x EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...], --exclude-benchmarks EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...]
	                        benchmarks to exclude


`./merge.py` can combine the results of different benchmark runs.

	usage: merge.py [-h] [--license] [--version] [-b BENCHMARKS [BENCHMARKS ...]]
	                [-x EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...]]
	                src dest

	Merge to allocbench results

	positional arguments:
	  src                   results which should be merged into dest
	  dest                  results in which src should be merged

	optional arguments:
	  -h, --help            show this help message and exit
	  --license             print license info and exit
	  --version             print version info and exit
	  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
	                        benchmarks to summarize
	  -x EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...], --exclude-benchmarks EXCLUDE_BENCHMARKS [EXCLUDE_BENCHMARKS ...]
	                        benchmarks to exclude

### Examples

	./bench.py -b loop

runs only the loop benchmark for all included allocators and will put its
results in `$PWD/results/$HOSTNAME/<time>/loop`.

	./bench.py -a BA_allocators

builds all allocators used in Florian Fischer's [BA thesis](https://muhq.space/ba.html)
and runs all benchmarks.

	./summarize.py <path/to/saved/results>

summarizes the previously created results.

## Benchmarks

You want to compare allocators with your own software or add a new benchmark,
have a look at [doc/Benchmarks.md](doc/Benchmarks.md).

## Allocators

By default all included allocators will be build and measured. For more precise control
about used allocators use the `-a` option.

For more details about what allocators are available, how they are used and how to
include new once have a look at [doc/Allocators.md](doc/Allocators.md).

## License

This program is released under GPLv3. You can find a copy of the license
in the LICENSE file in the programs root directory.
