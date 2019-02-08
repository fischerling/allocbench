# allocbench - benchmark tool for memory allocators

to download allocbench just run

```shell
git clone https://muhq.space/software/allocbench.git
```

## Usage

	usage: bench.py [-h] [-s] [-l LOAD] [-a ALLOCATORS] [-r RUNS] [-v]
	                [-b BENCHMARKS [BENCHMARKS ...]] [-ns] [-sd RESULTDIR]
	                [--license]

	benchmark memory allocators

	optional arguments:
	  -h, --help            show this help message and exit
	  -s, --save            save benchmark results to disk
	  -l LOAD, --load LOAD  load benchmark results from directory
	  -a ALLOCATORS, --allocators ALLOCATORS
	                        load allocator definitions from file
	  -r RUNS, --runs RUNS  how often the benchmarks run
	  -v, --verbose         more output
	  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
	                        benchmarks to run
	  -ns, --nosum          don't produce plots
	  -sd RESULTDIR, --resultdir RESULTDIR
	                        directory where all results go
	  --license             print license info and exit

## License

This program is released under GPLv3. You can find a copy of the license
in the LICENSE file in the programs root directory.
