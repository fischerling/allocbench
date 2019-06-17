import src.allocator


version = 2.29

glibc_src = src.allocator.Allocator_Sources("glibc",
                      retrieve_cmds=["git clone git://sourceware.org/git/glibc.git"],
                      prepare_cmds=["git checkout release/{}/master".format(version)],
                      reset_cmds=["git stash"])

class Glibc (src.allocator.Allocator):
    """Glibc definition for allocbench"""
    def __init__(self, name, **kwargs):

        kwargs["sources"] = glibc_src

        configure_args = ""
        if "configure_args" in kwargs:
            configure_args = kwargs["configure_args"]
            del(kwargs["configure_args"])

        kwargs["build_cmds"] = ["mkdir -p glibc-build",
                                "cd glibc-build; {srcdir}/configure --prefix={dir} " + configure_args,
                                "cd glibc-build; make",
                                "cd glibc-build; make install"]
        kwargs["cmd_prefix"] = ("{dir}/lib/ld-linux-x86-64.so.2 --library-path {dir}/lib:"
                              + src.allocator.library_path)

        super().__init__(name, **kwargs)
