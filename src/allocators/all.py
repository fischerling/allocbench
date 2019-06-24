from src.allocator import Allocator as Alloc
from src.allocator import Allocator_Sources as Alloc_Src

import src.allocators.glibcs
from src.allocators.tcmalloc import tcmalloc, tcmalloc_nofs
from src.allocators.jemalloc import jemalloc
from src.allocators.hoard import hoard
from src.allocators.mesh import mesh
from src.allocators.scalloc import scalloc
from src.allocators.supermalloc import supermalloc
from src.allocators.llalloc import llalloc


allocators = [*src.allocators.glibcs.allocators, tcmalloc, tcmalloc_nofs,
              jemalloc, hoard, mesh, supermalloc, scalloc, llalloc]
