from src.allocators.tcmalloc import tcmalloc, tcmalloc_nofs
from src.allocators.glibc import glibc, glibc_nofs


allocators = [glibc, glibc_nofs, tcmalloc, tcmalloc_nofs]
