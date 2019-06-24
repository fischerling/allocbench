from src.allocator import Allocator, Allocator_Sources, library_path


version = "v1.0.0"

scalloc_src = Allocator_Sources("scalloc",
                      retrieve_cmds=["git clone https://github.com/cksystemsgroup/scalloc"],
                      prepare_cmds=["git checkout {}".format(version),
                                    "cd {srcdir}; tools/make_deps.sh",
                                    "cd {srcdir}; build/gyp/gyp --depth=. scalloc.gyp"],
                      reset_cmds=["git stash"])


class Scalloc (Allocator):
    """Scalloc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = scalloc_src

        kwargs["build_cmds"] = ["cd {srcdir}; BUILDTYPE=Release make",
                                "mkdir -p {dir}"]

        kwargs["LD_PRELOAD"] = "{srcdir}/out/Release/lib.target/libscalloc.so"

        kwargs["patches"] = ["{patchdir}/scalloc_fix_log.patch"]

        super().__init__(name, **kwargs)


scalloc = Scalloc("scalloc")
