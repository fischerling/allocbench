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

allocators_to_build = [glibc, glibc_notc, glibc_nofs, glibc_nofs_fancy]

allocators = {a.name: a.build() for a in allocators_to_build}
