import src.allocator

version = "709663fb81ba091b0a78058869a644a272f4163d"

sources = src.allocator.Allocator_Sources("SuperMalloc",
            retrieve_cmds=["git clone https://github.com/kuszmaul/SuperMalloc"],
            prepare_cmds=["git checkout {}".format(version)])


class SuperMalloc (src.allocator.Allocator):
    """SuperMalloc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{srcdir}/release/lib/libsupermalloc.so"
        kwargs["build_cmds"] = ["cd {srcdir}/release; make",
                                "mkdir -p {dir}"]

        super().__init__(name, **kwargs)


supermalloc = SuperMalloc("SuperMalloc", color="xkcd:lime")
