from src.allocators.glibc import Glibc
from src.allocators.tcmalloc import TCMalloc
from src.allocators.jemalloc import Jemalloc
from src.allocators.hoard import Hoard

glibc = Glibc("glibc", color="C1")

glibc_notc = Glibc("glibc-notc",
                   configure_args="--disable-experimental-malloc",
                   color="C2")

tcmalloc = TCMalloc("tcmalloc", color="C3")

jemalloc = Jemalloc("jemalloc", color="C4")

hoard = Hoard("Hoard", color="C5", patches=["allocators/hoard_make.patch"])

allocators_to_build = [glibc, glibc_notc, tcmalloc, jemalloc, hoard]

allocators = {a.name: a.build() for a in allocators_to_build}
