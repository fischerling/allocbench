import os
import subprocess

from src.allocator import library_path
from src.allocator import Allocator as Alloc
from src.allocator import Allocator_Patched as Alloc_Patched
from src.allocator import Allocator_Sources as Alloc_Src
from src.allocator import builddir

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

glibc_nofs = Alloc_Patched("glibc_nofs", glibc,
                           ["allocators/glibc_2.28_no_passive_falsesharing.patch"])

tcmalloc_src = Alloc_Src("gperftools",
                         ["git clone https://github.com/gperftools/gperftools.git"],
                         ["git checkout gperftools-2.7", "./autogen.sh"],
                         ["git stash"])

tcmalloc = Alloc("tcmalloc", sources=tcmalloc_src,
                 LD_PRELOAD="{dir}/lib/libtcmalloc.so",
                 build_cmds=["cd {srcdir}; ./configure --prefix={dir} CXXFLAGS=" + optimisation_flag,
                             "cd {srcdir}; make install -j4"],
                 color="C3")

tcmalloc_nofs = Alloc_Patched("tcmalloc_nofs", tcmalloc,
                              ["allocators/tcmalloc_2.7_no_active_falsesharing.patch"],
                              color="C4")

allocators_to_build = [glibc, glibc_nofs, tcmalloc, tcmalloc_nofs]

allocators = {a.name: a.build(verbose=verbose) for a in allocators_to_build}
