import os
import subprocess

from src.allocator import *
from src.allocator import Allocator as Alloc
from src.allocator import Allocator_Sources as Alloc_Src

optimisation_flag = "-O2"

glibc_src = Alloc_Src("glibc",
                      retrieve_cmds=["git clone git://sourceware.org/git/glibc.git"],
                      prepare_cmds=["git checkout release/2.29/master"],
                      reset_cmds=["git stash"])

glibc = Alloc("glibc", sources=glibc_src,
              build_cmds=["mkdir -p glibc-build",
                          "cd glibc-build; {srcdir}/configure --prefix={dir}",
                          "cd glibc-build; make",
                          "cd glibc-build; make install"],
              cmd_prefix="{dir}/lib/ld-linux-x86-64.so.2 --library-path {dir}/lib:"+library_path)

glibc_notc = Alloc("glibc_notc", sources=glibc_src,
              build_cmds=["mkdir -p glibc-build",
                          "cd glibc-build; {srcdir}/configure --prefix={dir} --disable-experimental-malloc",
                          "cd glibc-build; make",
                          "cd glibc-build; make install"],
              cmd_prefix="{dir}/lib/ld-linux-x86-64.so.2 --library-path {dir}/lib:"+library_path)

glibc_nofs = patch_alloc("glibc_nofs", glibc,
                           ["allocators/glibc_2.28_no_passive_falsesharing.patch"])

glibc_nofs_fancy = patch_alloc("glibc_nofs_fancy", glibc,
                           ["allocators/glibc_2.28_no_passive_falsesharing_fancy.patch"])

tcmalloc_src = Alloc_Src("gperftools",
                         ["git clone https://github.com/gperftools/gperftools.git"],
                         ["git checkout gperftools-2.7", "./autogen.sh"],
                         ["git stash"])

tcmalloc = Alloc("tcmalloc", sources=tcmalloc_src,
                 LD_PRELOAD="{dir}/lib/libtcmalloc.so",
                 build_cmds=["cd {srcdir}; ./configure --prefix={dir} CXXFLAGS=" + optimisation_flag,
                             "cd {srcdir}; make install -j4"],
                 color="C3")

tcmalloc_nofs = patch_alloc("tcmalloc_nofs", tcmalloc,
                              ["allocators/tcmalloc_2.7_no_active_falsesharing.patch"],
                              color="C4")

jemalloc = Alloc("jemalloc",
                 sources=Alloc_Src("jemalloc",
                          retrieve_cmds=["git clone https://github.com/jemalloc/jemalloc.git"],
                          prepare_cmds=["git checkout 5.1.0", "./autogen.sh"]),
                 LD_PRELOAD="{dir}/lib/libjemalloc.so",
                 build_cmds=["cd {srcdir}; ./configure --prefix={dir} CFLAGS=" + optimisation_flag,
                             "mkdir {dir}"],
                 color="C4")

hoard = Alloc("Hoard", sources=Alloc_Src("Hoard",
                                        retrieve_cmds=["git clone https://github.com/emeryberger/Hoard.git"]),
                            LD_PRELOAD="{srcdir}/src/libhoard.so",
                            build_cmds=["cd {srcdir}/src; make",
                                        "mkdir {dir}"],
                            color="C5",
                            patches=["allocators/hoard_make.patch"])

allocators_to_build = [glibc, glibc_notc, glibc_nofs, glibc_nofs_fancy, tcmalloc, tcmalloc_nofs, jemalloc, hoard]

allocators = {a.name: a.build() for a in allocators_to_build}
