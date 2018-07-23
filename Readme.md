# allocbench - benchmark tool for memory allocators

to download allocbench just run

```shell
git clone https://muhq.space/software/allocbench.git
```

## Usage

	usage: bench.py [-h] [-s] [-l] [-r RUNS] [-v] [-b BENCHMARKS [BENCHMARKS ...]]

	benchmark memory allocators

	optional arguments:
	  -h, --help            show this help message and exit
	  -s, --save            save benchmark results to disk
	  -l, --load            load benchmark results from disk
	  -r RUNS, --runs RUNS  how often the benchmarks run
	  -v, --verbose         more output
	  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
	                        benchmarks to run
