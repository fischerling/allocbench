import src.allocator

version = "master"

snmalloc_src = src.allocator.Allocator_Sources("snmalloc",
                         ["git clone https://github.com/microsoft/snmalloc"],
                         ["git checkout ".format(version)],
                         ["git reset --hard"])


class Snmalloc (src.allocator.Allocator):
    """snmalloc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = snmalloc_src
        kwargs["LD_PRELOAD"] = "{dir}/libsnmallocshim.so"
        kwargs["build_cmds"] = ["mkdir -p {dir}",
                                "cd {dir}; cmake -G Ninja {srcdir} -DCMAKE_BUILD_TYPE=Release",
                                "cd {dir}; ninja"]
        kwargs["requirements"] = ["cmake", "ninja", "clang"]

        super().__init__(name, **kwargs)


snmalloc = Snmalloc("snmalloc")
