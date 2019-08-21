import src.allocator


sources = src.allocator.Allocator_Sources("Hoard",
            retrieve_cmds=["git clone https://github.com/emeryberger/Hoard.git"],
            reset_cmds=["git reset --hard"])


class Hoard (src.allocator.Allocator):
    """Hoard definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{dir}/libhoard.so"
        kwargs["build_cmds"] = ["cd {srcdir}/src; make",
                                "mkdir -p {dir}",
                                "ln -f -s {srcdir}/src/libhoard.so {dir}/libhoard.so"]
        kwargs["requirements"] = ["clang"]

        super().__init__(name, **kwargs)


hoard = Hoard("Hoard", color="xkcd:brown")
