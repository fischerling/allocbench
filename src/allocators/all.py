from src.allocator import Allocator as Alloc
from src.allocator import Allocator_Sources as Alloc_Src

import src.allocators.glibcs
from src.allocators.tcmalloc import tcmalloc, tcmalloc_nofs
from src.allocators.jemalloc import jemalloc
from src.allocators.hoard import hoard
from src.allocators.supermalloc import supermalloc
from src.allocators.llalloc import llalloc


mesh = Alloc("Mesh", sources=Alloc_Src("Mesh",
                                       retrieve_cmds=["git clone https://github.com/plasma-umass/Mesh"],
                                       reset_cmds=["git stash"]),
                            LD_PRELOAD="{srcdir}/libmesh.so",
                            build_cmds=["cd {srcdir}; git submodule update --init",
                                        "cd {srcdir}; ./configure",
                                        "cd {srcdir}; make -j 4",
                                        "mkdir {dir}"])

allocators = [*src.allocators.glibcs.allocators, tcmalloc, tcmalloc_nofs,
              jemalloc, hoard, mesh, supermalloc, llalloc]
