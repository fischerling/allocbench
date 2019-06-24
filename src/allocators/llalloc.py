from src.allocator import Allocator, Allocator_Sources, library_path


source = Allocator_Sources("lockless_allocator",
                      retrieve_cmds=["wget https://locklessinc.com/downloads/lockless_allocator_src.tgz",
                                     "tar xf lockless_allocator_src.tgz"],
                      prepare_cmds=[],
                      reset_cmds=[])


class Lockless_Allocator (Allocator):
    """Lockless allocator definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = source

        kwargs["build_cmds"] = ["cd {srcdir}; make", "mkdir -p {dir}"]
        
        kwargs["LD_PRELOAD"] = "{srcdir}/libllalloc.so.1.3"

        super().__init__(name, **kwargs)


llalloc = Lockless_Allocator("llalloc")

