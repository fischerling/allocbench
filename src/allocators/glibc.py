from src.allocator import Allocator, Allocator_Sources, library_path


version = 2.29

glibc_src = Allocator_Sources("glibc",
                      retrieve_cmds=["git clone git://sourceware.org/git/glibc.git"],
                      prepare_cmds=["git checkout release/{}/master".format(version)],
                      reset_cmds=["git stash"])


class Glibc (Allocator):
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
                                + library_path)

        super().__init__(name, **kwargs)


glibc = Glibc("glibc", color="xkcd:red")

glibc_notc = Glibc("glibc-noThreadCache",
                   configure_args="--disable-experimental-malloc",
                   color="xkcd:maroon")

glibc_nofs = Glibc("glibc-noFalsesharing",
                   patches=["{patchdir}/glibc_2.29_no_passive_falsesharing.patch"],
                   color="xkcd:pink")

glibc_nofs_fancy = Glibc("glibc-noFalsesharingClever",
                         patches=["{patchdir}/glibc_2.29_no_passive_falsesharing_fancy.patch"],
                         color="xkcd:orange")
