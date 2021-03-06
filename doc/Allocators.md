# Allocators

allocbench supports three mechanisms to change the used allocator for program
run with exec. The easiest is using `LD_PRELOAD` to overwrite `malloc/free`
with the functions of a shared library like libtcmalloc.so. If LD_PRELOAD
can't be used you can specify a command prefix to somehow load and use your allocator.
This command prefix is used for different versions of glibc. The command is
prefixed with the loader of the glibc version to test. *Note that the whole glibc
is changed maybe tampering with the results*. Additionally binary suffixes are
supported. This could be used to use with  `patchelf` patched binaries to
use different `rpath` or `linker`.

The used allocators are stored in a global python dictionary associating
their names with the fields: `cmd_prefix, binary_suffix, LD_PRELOAD` and `color`.

By default this dictionary is build from locally installed allocators found by `whereis`.

You can overwrite the default allocators with the `-a | --allocators` option
and a python script exporting a global dictionary with the name `allocators`.

## Included Allocators

* lockless allocator
* supermalloc
* glibc
* mesh
* scalloc
* tbbmalloc
* bumpptr
* jemalloc
* mimalloc
* scalloc
* hoard
* snmalloc
* tcmalloc

## Building Allocators

To reproducible build allocators and patched version you can use the
classes `Allocator` and any `Artifact` subclass provided in `allocbench/allocator.py`
and `allocbench/artifact.py`.
See [allocators/no_falsesharing.py](allocators/no_falsesharing.py) or
[allocators/ba_allocators.py](allocators/ba_allocators.py) for examples.
