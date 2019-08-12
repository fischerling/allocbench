import src.allocator

version = 2.7

tcmalloc_src = src.allocator.Allocator_Sources("tcmalloc",
                         ["git clone https://github.com/gperftools/gperftools.git tcmalloc"],
                         ["git checkout gperftools-{}".format(version), "./autogen.sh"],
                         ["git reset --hard"])


class TCMalloc (src.allocator.Allocator):
    """TCMalloc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = tcmalloc_src
        kwargs["LD_PRELOAD"] = "{dir}/lib/libtcmalloc.so"
        kwargs["build_cmds"] = ["cd {srcdir}; ./configure --prefix={dir} CXXFLAGS=-O2",
                                "cd {srcdir}; make install -j4"]

        super().__init__(name, **kwargs)


tcmalloc = TCMalloc("TCMalloc", color="xkcd:blue")

tcmalloc_nofs = TCMalloc("TCMalloc-NoFalsesharing",
                         patches=["{patchdir}/tcmalloc_2.7_no_active_falsesharing.patch"],
                         color="xkcd:navy")
