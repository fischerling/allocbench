# Benchmark result

The results of each benchmark run by allocbench are stored in the member variable
benchmark.results. This variable is an dictionary containing following keys:

## Keys

### "args"
dictionary containing all arguments mapped to their possible values

### "facts"
list of facts about the benchmark (libc versions, ...)

### "allocators"
dict of the measured allocators

### <allocname>
dict for each allocator mapping each argument permutation to a list of measurements.
Measurements are dicts matching data point names to values.

Example:
```python
"glibc": {Perm(threads=1, size=8): [{"time": 1.22, "RSS": 200},
                                    {"time": 1.33, "RSS": 200}],
          Perm(threads=2, size=8): [{"time": 2.44, "RSS": 400},
                                    {"time": 2.63, "RSS": 402}],
         }
```

### "stats"
dict mapping each allocator to the descriptive statistics of its measurements.
Available statistics are:
min, max, mean, median, std (standard deviation), std_perc (std/mean), lower_/upper_quartile, ...

Example:
```python
"stats": {"glibc": {Perm(threads=1, size=8): {"mean": 1.22, "min": 1, "std":0.1, ...},
                    Perm(threads=2, size=8): {"mean": 2.44, "min": 2, "median": 2.44, ...}}
         }
```

## Disk format

The disk format uses JSON and nearly identical to how the results are stored in the python object.
Because Python namedtuples used for the argument permutations are not directly serializable into JSON.
all permutations are converted to dicts and dictionaries using those tuples as keys are converted to lists.
This means the allocator dict mapping permutations to measurements becomes a 2-element list
containing the permutation as a dict and the list of measurements.

Example:
```json
"glibc": [[{"threads":1, "size":8}, [{"time": 1.22, "RSS": 200},
                                    {"time": 1.33, "RSS": 200}]],
          [{"threads":2, "size":8}, [{"time": 2.44, "RSS": 400},
                                    {"time": 2.63, "RSS": 402}]]
         ]
```
