import copy
import os
import pickle
import shutil
import subprocess
import sys

import src.globalvars
from src.util import *

library_path = ""
for l in subprocess.run(["ldconfig", "-v"], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True).stdout.splitlines():
    if not l.startswith('\t'):
        library_path += l

builddir = os.path.join(os.getcwd(), "build", "allocators")
srcdir = os.path.join(builddir, "src")

if not os.path.isdir(srcdir):
    os.makedirs(srcdir)


class Allocator_Sources (object):
    def __init__(self, name, retrieve_cmds=[], prepare_cmds=[], reset_cmds=[]):
        self.name = name
        self.dir = os.path.join(srcdir, self.name)
        self.retrieve_cmds = retrieve_cmds
        self.prepare_cmds = prepare_cmds
        self.reset_cmds = reset_cmds

    def run_cmds(self, function, cwd=srcdir):
        print_status(function, self.name, "...", flush=True)

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

        print_status("Patching", self.name, "...", flush=True)
        for patch in patches:
            with open(patch, "rb") as f:
                p = subprocess.run("patch -p1", shell=True, cwd=cwd,
                                   stderr=subprocess.PIPE, stdout=stdout,
                                   input=f.read())

                if p.returncode:
                    print_error("Patching of", self.name, "failed.", file=sys.stderr)
                    print_debug(p.stderr, file=sys.stderr)
                    exit(1)


class Allocator (object):
    allowed_attributes = ["binary_suffix", "version", "sources", "build_cmds",
                          "LD_PRELOAD", "cmd_prefix", "color", "patches"]

    def __init__(self, name, **kwargs):
        self.name = name
        self.dir = os.path.join(builddir, self.name)
        # Update attributes
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.allowed_attributes)

        # create all unset attributes
        for attr in self.allowed_attributes:
            if not hasattr(self, attr):
                setattr(self, attr, None)

    def build(self):
        build_needed = not os.path.isdir(self.dir)
        builddef_file = os.path.join(self.dir, ".builddef")

        if not build_needed:
            print_info2("Old build found. Comparing builddefs")

            old_def = ""
            with open(builddef_file, "rb") as f:
                old_def = pickle.dumps(pickle.load(f))
            build_needed = old_def != pickle.dumps(self)

            print_debug("Old Def.:", old_def)
            print_debug("New Def.:", pickle.dumps(self))
            print_info2("Build needed:", build_needed)

        if build_needed:
            if self.sources:
                self.sources.prepare()
                self.sources.patch(self.patches)

            if self.build_cmds:
                print_status("Building", self.name, "...", flush=True)

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

                with open(builddef_file, "wb") as f:
                    print_info2("Save build definition to:", builddef_file)
                    pickle.dump(self, f)

        print_info2("Create allocator dictionary")
        for attr in ["LD_PRELOAD", "cmd_prefix"]:
            try:
                value = getattr(self, attr)
                setattr(self, attr, value.format(**{"dir": self.dir,
                                                  "srcdir": self.sources.dir}))
            except AttributeError:
                setattr(self, attr, "")

        res_dict =  {"cmd_prefix": self.cmd_prefix,
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

