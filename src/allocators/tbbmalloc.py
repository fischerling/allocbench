import src.allocator

version = "2019_U8"

source = src.allocator.Allocator_Sources("tbb",
                         ["git clone https://github.com/intel/tbb.git"],
                         ["git checkout {}".format(version)],
                         ["git stash"])


class TBBMalloc (src.allocator.Allocator):
    """TCMalloc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = source
        kwargs["LD_PRELOAD"] = "{dir}/libtbbmalloc.so"
        kwargs["build_cmds"] = ["cd {srcdir}; make tbbmalloc -j4",
                                "mkdir -p {dir}",
                                'ln -f -s $(find {srcdir} -executable -name "*libtbbmalloc.so*") {dir}/libtbbmalloc.so']

        super().__init__(name, **kwargs)


tbbmalloc = TBBMalloc("tbbmalloc", color="xkcd:green")
