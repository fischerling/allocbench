from src.allocator import Allocator as Alloc
from src.allocator import Allocator_Sources as Alloc_Src

from src.allocators.glibc import Glibc
from src.allocators.tcmalloc import TCMalloc
from src.allocators.jemalloc import Jemalloc
from src.allocators.supermalloc import SuperMalloc

glibc = Glibc("glibc", color="C1")

tcmalloc = TCMalloc("tcmalloc", color="C5")

jemalloc = Jemalloc("jemalloc", color="C6")

supermalloc = SuperMalloc("SuperMalloc", color="C8")

allocators_to_build = [glibc, tcmalloc, jemalloc, supermalloc]

allocators = {a.name: a.build() for a in allocators_to_build}
