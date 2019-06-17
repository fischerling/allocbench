from src.allocator import Allocator as Alloc
from src.allocator import Allocator_Sources as Alloc_Src

from src.allocators.glibc import Glibc
from src.allocators.tcmalloc import TCMalloc
from src.allocators.jemalloc import Jemalloc
from src.allocators.hoard import Hoard

glibc = Glibc("glibc", color="C1")

glibc_notc = Glibc("glibc-notc",
                configure_args="--disable-experimental-malloc",
                color="C2")

glibc_nofs = Glibc("glibc_nofs",
                   patches=["allocators/glibc_2.28_no_passive_falsesharing.patch"],
                   color="C3")

glibc_nofs_fancy = Glibc("glibc_nofs_fancy",
                         patches=["allocators/glibc_2.28_no_passive_falsesharing_fancy.patch"],
                         color="C4")

tcmalloc = TCMalloc("tcmalloc", color="C5")

tcmalloc_nofs = TCMalloc("tcmalloc_nofs",
                         patches= ["{patchdir}/tcmalloc_2.7_no_active_falsesharing.patch"],
                         color="C5")

jemalloc = Jemalloc("jemalloc", color="C6")

hoard = Hoard("Hoard", color="C7", patches=["allocators/hoard_make.patch"])

mesh = Alloc("Mesh", sources=Alloc_Src("Mesh",
                                        retrieve_cmds=["git clone https://github.com/plasma-umass/Mesh"],
                                        reset_cmds=["git stash"]),
                            LD_PRELOAD="{srcdir}/libmesh.so",
                            build_cmds=["cd {srcdir}; git submodule update --init",
                                        "cd {srcdir}; ./configure",
                                        "cd {srcdir}; make -j 4",
                                        "mkdir {dir}"])

allocators_to_build = [glibc, glibc_notc, glibc_nofs, glibc_nofs_fancy, tcmalloc, tcmalloc_nofs, jemalloc, hoard, mesh]

allocators = {a.name: a.build() for a in allocators_to_build}
