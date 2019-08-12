import src.allocator

sources = src.allocator.Allocator_Sources("Mesh",
            retrieve_cmds=["git clone https://github.com/plasma-umass/Mesh"],
            reset_cmds=["git reset --hard"])

# sources = src.allocator.GitAllocatorSources("Mesh",
#             "https://github.com/plasma-umass/Mesh",
#             "adsf0982345")


class Mesh (src.allocator.Allocator):
    """Mesh definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{srcdir}/libmesh.so"
        kwargs["build_cmds"] = ["cd {srcdir}; git submodule update --init",
                                "cd {srcdir}; ./configure",
                                "cd {srcdir}; make -j 4",
                                "mkdir -p {dir}"]

        super().__init__(name, **kwargs)


mesh = Mesh("Mesh", color="xkcd:mint")
