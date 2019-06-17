import src.allocator


version = 2.7
sources = src.allocator.Allocator_Sources("Hoard",
            retrieve_cmds=["git clone https://github.com/emeryberger/Hoard.git"],
            reset_cmds=["git stash"])

class Hoard (src.allocator.Allocator):
    """Hoard definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = sources
        kwargs["LD_PRELOAD"] = "{srcdir}/src/libhoard.so"
        kwargs["build_cmds"] = ["cd {srcdir}/src; make", "mkdir -p {dir}"]
        kwargs["patches"] = ["{patchdir}/hoard_make.patch"]

        super().__init__(name, **kwargs)
