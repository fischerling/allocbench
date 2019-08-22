import os
from src.allocator import Allocator, builddir

chattymalloc = Allocator("chattymalloc",
                         LD_PRELOAD=os.path.join(builddir, "chattymalloc.so"),
                         cmd_prefix="env CHATTYMALLOC_FILE={{result_dir}}/chatty_{{perm}}.txt")
