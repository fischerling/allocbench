import os
from src.allocator import Allocator, builddir

bumpptr = Allocator("bumpptr", LD_PRELOAD=os.path.join(builddir, "bumpptr_alloc.so"), color="xkcd:black")
