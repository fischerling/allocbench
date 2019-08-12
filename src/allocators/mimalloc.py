import src.allocator

version = "master"

mimalloc_src = src.allocator.Allocator_Sources("mimalloc",
                         ["git clone https://github.com/microsoft/mimalloc"],
                         ["git checkout ".format(version)],
                         ["git reset --hard"])


class Mimalloc (src.allocator.Allocator):
    """mimalloc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = mimalloc_src
        kwargs["LD_PRELOAD"] = "{dir}/libmimalloc.so"
        kwargs["build_cmds"] = ["cd {srcdir}; mkdir -p {dir}",
                                "cd {dir}; cmake {srcdir}",
                                "cd {dir}; make"]

        super().__init__(name, **kwargs)


mimalloc = Mimalloc("mimalloc")
