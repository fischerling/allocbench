import copy
from datetime import datetime
import inspect
import os
import shutil
import subprocess
import sys

import src.globalvars
from src.util import print_status, print_debug, print_error, print_info2


library_path = ""
for l in subprocess.run(["ldconfig", "-v"], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True).stdout.splitlines():

    if not l.startswith('\t'):
        library_path += l

builddir = os.path.join(src.globalvars.builddir, "allocators")
srcdir = os.path.join(builddir, "src")

if not os.path.isdir(srcdir):
    os.makedirs(srcdir)


class Allocator_Sources (object):
    def __init__(self, name, retrieve_cmds=[], prepare_cmds=[], reset_cmds=[]):
        self.name = name
        self.dir = os.path.join(srcdir, self.name)
        self.retrieve_cmds = retrieve_cmds
        self.patchdir = os.path.join("src/allocators/", self.name)
        self.prepare_cmds = prepare_cmds
        self.reset_cmds = reset_cmds

    def run_cmds(self, function, cwd=srcdir):
        print_status(function, self.name, "...")

        cmds = getattr(self, function+"_cmds")

        stdout = subprocess.PIPE if src.globalvars.verbosity < 2 else None

        for cmd in cmds:
            p = subprocess.run(cmd, shell=True, cwd=cwd, stderr=subprocess.PIPE,
                               stdout=stdout)

            if p.returncode:
                print_error(function, self.name, "failed with", p.returncode,
                            file=sys.stderr)
                print_debug(p.stderr, file=sys.stderr)
                return False
        return True

    def prepare(self):
        if not os.path.isdir(self.dir):
            if (not self.run_cmds("retrieve") or
                    not self.run_cmds("prepare", cwd=self.dir)):

                shutil.rmtree(self.dir, ignore_errors=True)
                exit(1)
        else:
            self.reset()

    def reset(self):
        if not self.run_cmds("reset", cwd=self.dir):
            exit(1)

    def patch(self, patches):
        if not patches:
            return

        stdout = subprocess.PIPE if src.globalvars.verbosity < 2 else None
        cwd = os.path.join(srcdir, self.name)

        print_status("Patching", self.name, "...")
        for patch in patches:
            with open(patch.format(patchdir=self.patchdir), "rb") as f:
                p = subprocess.run("patch -p1", shell=True, cwd=cwd,
                                   stderr=subprocess.PIPE, stdout=stdout,
                                   input=f.read())

                if p.returncode:
                    print_error("Patching of", self.name, "failed.",
                                file=sys.stderr)
                    print_debug(p.stderr, file=sys.stderr)
                    exit(1)


class Allocator (object):
    allowed_attributes = ["binary_suffix", "version", "sources", "build_cmds",
                          "LD_PRELOAD", "cmd_prefix", "color", "patches"]

    def __init__(self, name, **kwargs):
        self.name = name
        self.dir = os.path.join(builddir, self.name)
        # Update attributes
        self.__dict__.update((k, v) for k, v in kwargs.items()
                             if k in self.allowed_attributes)

        # create all unset attributes
        for attr in self.allowed_attributes:
            if not hasattr(self, attr):
                setattr(self, attr, None)

    def build(self):
        build_needed = not os.path.isdir(self.dir)
        buildtimestamp_file = os.path.join(self.dir, ".buildtime")

        if not build_needed:
            print_info2("Old build found. Comparing build time with mtime")

            with open(buildtimestamp_file, "r") as f:
                timestamp = datetime.fromtimestamp(float(f.read()))

            modtime = os.stat(inspect.getfile(self.__class__)).st_mtime
            modtime = datetime.fromtimestamp(modtime)

            build_needed = timestamp < modtime

            print_debug("Time of last build:", timestamp.isoformat())
            print_debug("Last modification of allocators file:",
                        modtime.isoformat())
            print_info2("Build needed:", build_needed)

        if build_needed:
            if self.sources:
                self.sources.prepare()
                self.sources.patch(self.patches)

            if self.build_cmds:
                print_status("Building", self.name, "...")

                stdout = subprocess.PIPE if src.globalvars.verbosity < 2 else None

                for cmd in self.build_cmds:
                    cmd = cmd.format(**{"dir": self.dir,
                                        "srcdir": self.sources.dir})

                    p = subprocess.run(cmd, cwd=builddir, shell=True,
                                       stderr=subprocess.PIPE, stdout=stdout)
                    if p.returncode:
                        print_error(cmd, "failed with:", p.returncode)
                        print_debug(p.stderr, file=sys.stderr)
                        print_error("Building", self.name, "failed ...")
                        shutil.rmtree(self.dir, ignore_errors=True)
                        exit(2)

                with open(buildtimestamp_file, "w") as f:
                    print_info2("Save build time to:", buildtimestamp_file)
                    f.write(str(datetime.now().timestamp()))

        print_info2("Create allocator dictionary")
        for attr in ["LD_PRELOAD", "cmd_prefix"]:
            try:
                value = getattr(self, attr)
                setattr(self, attr, value.format(**{"dir": self.dir,
                                                 "srcdir": self.sources.dir}))
            except AttributeError:
                setattr(self, attr, "")

        res_dict = {"cmd_prefix": self.cmd_prefix,
                    "binary_suffix": self.binary_suffix or "",
                    "LD_PRELOAD": self.LD_PRELOAD,
                    "color": self.color}
        print_debug("Resulting dictionary:", res_dict)
        return res_dict


def patch_alloc(name, alloc, patches, **kwargs):
    new_alloc = copy.deepcopy(alloc)
    new_alloc.name = name
    new_alloc.patches = patches

    new_alloc.dir = os.path.join(builddir, name)
    new_alloc.__dict__.update((k, v) for k, v in kwargs.items() if k in alloc.allowed_attributes)

    return new_alloc


bumpptr = Allocator("bumpptr", LD_PRELOAD=os.path.join(builddir, "bumpptr_alloc.so"), color="xkcd:black")
