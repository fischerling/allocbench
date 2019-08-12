from src.allocator import Allocator, Allocator_Sources, library_path
from src.util import print_error


version = "v1.0.0"

scalloc_src = Allocator_Sources("scalloc",
                      retrieve_cmds=["git clone https://github.com/cksystemsgroup/scalloc"],
                      prepare_cmds=["git checkout {}".format(version),
                                    "cd {srcdir}; tools/make_deps.sh",
                                    "cd {srcdir}; build/gyp/gyp --depth=. scalloc.gyp"],
                      reset_cmds=["git reset --hard"]


class Scalloc (Allocator):
    """Scalloc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = scalloc_src

        kwargs["build_cmds"] = ["cd {srcdir}; BUILDTYPE=Release make",
                                "mkdir -p {dir}"]

        kwargs["LD_PRELOAD"] = "{srcdir}/out/Release/lib.target/libscalloc.so"

        kwargs["patches"] = ["{patchdir}/scalloc_fix_log.patch"]

        super().__init__(name, **kwargs)

    def build(self):
        with open("/proc/sys/vm/overcommit_memory", "r") as f:
            if f.read()[0] != "1":
                raise AssertionError("""\
vm.overcommit_memory not set
Scalloc needs permission to overcommit_memory.
sysctl vm.overcommit_memory=1
""")
        return super().build()


scalloc = Scalloc("scalloc", color="xkcd:magenta")
