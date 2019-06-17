from src.allocators.tcmalloc import TCMalloc
from src.allocators.glibc import Glibc

glibc = Glibc("glibc", color="C1")

glibc_nofs = Glibc("glibc_nofs",
                   patches=["{patchdir}/glibc_2.28_no_passive_falsesharing.patch"],
                   color="C2")

tcmalloc = TCMalloc("tcmalloc", color="C3")

tcmalloc_nofs = TCMalloc("tcmalloc_nofs",
                         patches= ["{patchdir}/tcmalloc_2.7_no_active_falsesharing.patch"],
                         color="C4")

allocators_to_build = [glibc, glibc_nofs, tcmalloc, tcmalloc_nofs]

allocators = {a.name: a.build() for a in allocators_to_build}
