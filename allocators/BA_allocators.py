import os
import subprocess

from src.allocator import *
from src.allocator import Allocator as Alloc
from src.allocator import Allocator_Sources as Alloc_Src

optimisation_flag = "-O2"

glibc_src = Alloc_Src("glibc",
                      retrieve_cmds=["git clone git://sourceware.org/git/glibc.git"],
                      prepare_cmds=["git checkout release/2.28/master"])

glibc = Alloc("glibc", sources=glibc_src,
              build_cmds=["mkdir -p glibc-build",
                          "cd glibc-build; {srcdir}/configure --prefix={dir}",
                          "cd glibc-build; make",
                          "cd glibc-build; make install"],
              cmd_prefix="{dir}/lib/ld-linux-x86-64.so.2 --library-path {dir}/lib:"+library_path,
              color="C1")

glibc_notc = Alloc("glibc-notc", sources=glibc_src,
              build_cmds=["mkdir -p glibc-build",
                          "cd glibc-build; {srcdir}/configure --prefix={dir} --disable-experimental-malloc",
                          "cd glibc-build; make",
                          "cd glibc-build; make install"],
              cmd_prefix="{dir}/lib/ld-linux-x86-64.so.2 --library-path {dir}/lib:"+library_path,
              color="C2")

tcmalloc = Alloc("tcmalloc",
                 sources=Alloc_Src("gperftools",
                          retrieve_cmds=["git clone https://github.com/gperftools/gperftools.git"],
                          prepare_cmds=["git checkout gperftools-2.7", "./autogen.sh"]),
                 LD_PRELOAD="{dir}/lib/libtcmalloc.so",
                 build_cmds=["cd {srcdir}; ./configure --prefix={dir} CXXFLAGS=" + optimisation_flag,
                             "cd {srcdir}; make install -j4"],
                 color="C3")

jemalloc = Alloc("jemalloc",
                 sources=Alloc_Src("jemalloc",
                          retrieve_cmds=["git clone https://github.com/jemalloc/jemalloc.git"],
                          prepare_cmds=["git checkout 5.1.0", "./autogen.sh"]),
                 LD_PRELOAD="{srcdir}/lib/libjemalloc.so",
                 build_cmds=["cd {srcdir}; ./configure --prefix={dir} CFLAGS=" + optimisation_flag,
                             "cd {srcdir}; make -j4",
                             "mkdir {dir}"],
                 color="C4")

hoard = Alloc("Hoard", sources=Alloc_Src("Hoard",
                                        retrieve_cmds=["git clone https://github.com/emeryberger/Hoard.git"]),
                            LD_PRELOAD="{srcdir}/src/libhoard.so",
                            build_cmds=["cd {srcdir}/src; make",
                                        "mkdir {dir}"],
                            color="C5",
                            patches=["allocators/hoard_make.patch"])



allocators_to_build = [glibc, glibc_notc, tcmalloc, jemalloc, hoard]

allocators = {a.name: a.build() for a in allocators_to_build}
