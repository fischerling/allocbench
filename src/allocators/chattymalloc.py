import os
from src.allocator import Allocator, builddir

chattymalloc = Allocator("chattymalloc", LD_PRELOAD=os.path.join(builddir, "chattymalloc.so"), color="xkcd:black")
