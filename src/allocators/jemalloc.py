import src.allocator


version = "5.1.0"

sources = src.allocator.Allocator_Sources("jemalloc",
            retrieve_cmds=["git clone https://github.com/jemalloc/jemalloc.git"],
            prepare_cmds=["git checkout {}".format(version), "./autogen.sh"])


class Jemalloc (src.allocator.Allocator):
    """jemalloc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{srcdir}/lib/libjemalloc.so"
        kwargs["build_cmds"] = ["cd {srcdir}; ./configure --prefix={dir}",
                                "cd {srcdir}; make -j4",
                                "mkdir -p {dir}"]

        super().__init__(name, **kwargs)


jemalloc = Jemalloc("jemalloc", color="xkcd:yellow")
