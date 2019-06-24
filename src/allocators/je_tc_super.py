from src.allocators.glibc import glibc
from src.allocators.tcmalloc import tcmalloc
from src.allocators.jemalloc import jemalloc
from src.allocators.supermalloc import supermalloc


allocators = [glibc, tcmalloc, jemalloc, supermalloc]
