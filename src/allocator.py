import copy
import os
import shutil
import subprocess
import sys

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
    # indicate if this source was patched
    available = False
    clean = True

    def __init__(self, name, retrieve_cmds=[], prepare_cmds=[], reset_cmds=[]):
        self.name = name
        self.dir = os.path.join(srcdir, self.name)
        self.retrieve_cmds = retrieve_cmds
        self.prepare_cmds = prepare_cmds
        self.reset_cmds = reset_cmds

    def run_cmds(self, function, verbose, cwd=srcdir):
        print(function, self.name, "...")
        cmds = getattr(self, function+"_cmds")
        for cmd in cmds:
            stdout = subprocess.PIPE if not verbose else None
            stderr = subprocess.PIPE if not verbose else None
            p = subprocess.run(cmd, shell=True, cwd=cwd, stderr=stderr,
                               stdout=stdout)
            
            if p.returncode:
                print(function, self.name, "failed with", p.returncode,
                      file=sys.stderr)
                print(p.stderr, file=sys.stderr)
                return False
        return True

    def prepare(self, verbose):
        if not os.path.isdir(self.dir):
            if (not self.run_cmds("retrieve", verbose) or
                    not self.run_cmds("prepare", verbose, cwd=self.dir)):

                shutil.rmtree(self.dir, ignore_errors=True)
                exit(1)
        
        self.available = True
        return True

    def reset(self, verbose):
        if not self.run_cmds("reset", verbose, cwd=self.dir):
            exit(1)
        self.clean = True

    def patch(self, patches, verbose):
        self.prepare(verbose)
        stdout = subprocess.PIPE if not verbose else None
        stderr = subprocess.PIPE
        cwd = os.path.join(srcdir, self.name)

        print("Patching", self.name, "...")
        for patch in patches:
            with open(patch, "rb") as f:
                p = subprocess.run("patch -p1", shell=True, cwd=cwd, stderr=stderr,
                                   stdout=stdout, input=f.read())
        
                if p.returncode:
                    print("Patching of", self.name, "failed.", file=sys.stderr)
                    exit(1)
        

class Allocator (object):
    allowed_attributes = ["binary_suffix", "version", "sources", "build_cmds",
                          "LD_PRELOAD", "cmd_prefix", "color"]

    def __init__(self, name, **kwargs):
        self.name = name
        self.dir = os.path.join(builddir, self.name)
        # Update attributes
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.allowed_attributes)

        # create all unset attributes
        for attr in self.allowed_attributes:
            if not hasattr(self, attr):
                setattr(self, attr, None)

    def build(self, verbose=False):
        if not os.path.isdir(self.dir):
            if self.sources:
                if not self.sources.available:
                    self.sources.prepare(verbose)
                if not self.sources.clean:
                    self.sources.reset(verbose)
                
            if self.build_cmds:
                print("Building", self.name, "...")
                for cmd in self.build_cmds:
                    cmd = cmd.format(**{"dir": self.dir,
                                        "srcdir": self.sources.dir})
                    stdout = subprocess.PIPE if not verbose else None
                    stderr = subprocess.PIPE
                    p = subprocess.run(cmd, cwd=builddir, shell=True,
                                       stderr=stderr, stdout=stdout)
                    if p.returncode:
                        print(cmd)
                        print(p.stderr)
                        print("Building", self.name, "failed ...")
                        shutil.rmtree(self.dir, ignore_errors=True)
                        exit(1)

        for attr in ["LD_PRELOAD", "cmd_prefix"]:
            try:
                value = getattr(self, attr)
                setattr(self, attr, value.format(**{"dir": self.dir,
                                                  "srcdir": self.sources.dir}))
            except AttributeError:
                setattr(self, attr, "")
        
        return {"cmd_prefix": self.cmd_prefix,
                "binary_suffix": self.binary_suffix or "",
                "LD_PRELOAD": self.LD_PRELOAD,
                "color": self.color}


class Allocator_Patched (object):
    def __init__(self, name, alloc, patches, **kwargs):
        self.name = name
        self.patches = patches

        self.alloc = copy.deepcopy(alloc)
        self.alloc.name = self.name
        self.alloc.dir = os.path.join(builddir, self.name)
        self.alloc.__dict__.update((k, v) for k, v in kwargs.items() if k in self.alloc.allowed_attributes)

    def build(self, verbose=False):

        if not os.path.isdir(self.alloc.dir):
            self.alloc.sources.patch(self.patches, verbose)

        return self.alloc.build(verbose=verbose)
