from src.allocators.glibc import glibc, glibc_notc
from src.allocators.tcmalloc import tcmalloc
from src.allocators.jemalloc import jemalloc
from src.allocators.hoard import hoard

allocators = [glibc, glibc_notc, tcmalloc, jemalloc, hoard]
