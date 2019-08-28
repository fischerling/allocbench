# Copyright 2018-2019 Florian Fischer <florian.fl.fischer@fau.de>
#
# This file is part of allocbench.
#
# allocbench is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# allocbench is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with allocbench.  If not, see <http://www.gnu.org/licenses/>.

"""Alloactor related class definitions and helpers"""

from datetime import datetime
import inspect
import importlib
import os
import shutil
import subprocess
import sys

import src.globalvars
from src.util import print_status, print_debug, print_error, print_info2


LIBRARY_PATH = ""
for line in subprocess.run(["ldconfig", "-v"], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True).stdout.splitlines():

    if not line.startswith('\t'):
        LIBRARY_PATH += line

BUILDDIR = os.path.join(src.globalvars.builddir, "allocators")
SRCDIR = os.path.join(src.globalvars.allocbuilddir, "src")

if not os.path.isdir(SRCDIR):
    os.makedirs(SRCDIR)


class AllocatorSources:
    """Class representing sources an allocator is build from

    AllocatorSources can retrieve, prepare and reset their managed sources
    """
    def __init__(self, name, retrieve_cmds=None, prepare_cmds=None, reset_cmds=None):
        self.name = name
        self.dir = os.path.join(SRCDIR, self.name)
        self.patchdir = os.path.join(src.globalvars.allocsrcdir, self.name)
        self.retrieve_cmds = retrieve_cmds or []
        self.prepare_cmds = prepare_cmds or []
        self.reset_cmds = reset_cmds or []

    def run_cmds(self, function, cwd=SRCDIR):
        """Helper to run retrieve, prepare or reset commands"""
        print_status(function, self.name, "...")

        cmds = getattr(self, function+"_cmds")

        stdout = subprocess.PIPE if src.globalvars.verbosity < 2 else None

        for cmd in cmds:
            proc = subprocess.run(cmd, shell=True, cwd=cwd,
                                  stderr=subprocess.PIPE, stdout=stdout,
                                  universal_newlines=True)

            if proc.returncode:
                print_error(function, self.name, "failed with", proc.returncode,
                            file=sys.stderr)
                print_debug(proc.stderr, file=sys.stderr)
                return False
        return True

    def prepare(self):
        """Prepare the managed sources for building

        If the sources aren't available yet they are retrieved.
        Otherwise they are reset.
        """
        if not os.path.isdir(self.dir):
            if (not self.run_cmds("retrieve") or
                    not self.run_cmds("prepare", cwd=self.dir)):

                shutil.rmtree(self.dir, ignore_errors=True)
                exit(1)
        else:
            self.reset()

    def reset(self):
        """Reset the managed sources"""
        if not self.run_cmds("reset", cwd=self.dir):
            exit(1)

    def patch(self, patches):
        """Patch the managed sources using patch(1)"""
        if not patches:
            return

        stdout = subprocess.PIPE if src.globalvars.verbosity < 2 else None
        cwd = os.path.join(SRCDIR, self.name)

        print_status("Patching", self.name, "...")
        for patch in patches:
            print(self.patchdir)
            print(patch)
            with open(patch.format(patchdir=self.patchdir), "rb") as patch_file:
                proc = subprocess.run("patch -p1", shell=True, cwd=cwd,
                                      stderr=subprocess.PIPE, stdout=stdout,
                                      input=patch_file.read())

                if proc.returncode:
                    print_error("Patching of", self.name, "failed.",
                                file=sys.stderr)
                    print_debug(proc.stderr, file=sys.stderr)
                    exit(1)


class Allocator:
    """Allocator base class

    It builds the allocator and produces a for allocbench usable allocator dict"""
    allowed_attributes = ["binary_suffix", "version", "sources", "build_cmds",
                          "LD_PRELOAD", "cmd_prefix", "color", "patches",
                          "LD_LIBRARY_PATH"]

    def __init__(self, name, **kwargs):
        self.name = name
        self.dir = os.path.join(BUILDDIR, self.name)
        # Update attributes
        self.__dict__.update((k, v) for k, v in kwargs.items()
                             if k in self.allowed_attributes)

        # create all unset attributes
        for attr in self.allowed_attributes:
            if not hasattr(self, attr):
                setattr(self, attr, None)

    def build(self):
        """Build the allocator if needed and produce allocator dict"""
        build_needed = not os.path.isdir(self.dir)
        buildtimestamp_path = os.path.join(self.dir, ".buildtime")

        if not build_needed:
            print_info2("Old build found. Comparing build time with mtime")

            with open(buildtimestamp_path, "r") as buildtimestamp_file:
                timestamp = datetime.fromtimestamp(float(buildtimestamp_file.read()))

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

                    proc = subprocess.run(cmd, cwd=BUILDDIR, shell=True,
                                          stderr=subprocess.PIPE, stdout=stdout,
                                          universal_newlines=True)
                    if proc.returncode:
                        print_error(cmd, "failed with:", proc.returncode)
                        print_debug(proc.stderr, file=sys.stderr)
                        print_error("Building", self.name, "failed ...")
                        shutil.rmtree(self.dir, ignore_errors=True)
                        exit(2)

                with open(buildtimestamp_path, "w") as buildtimestamp_file:
                    print_info2("Save build time to:", buildtimestamp_path)
                    buildtimestamp_file.write(str(datetime.now().timestamp()))

        print_info2("Create allocator dictionary")
        res_dict = {"cmd_prefix": self.cmd_prefix or "",
                    "binary_suffix": self.binary_suffix or "",
                    "LD_PRELOAD": self.LD_PRELOAD or "",
                    "LD_LIBRARY_PATH": self.LD_LIBRARY_PATH or "",
                    "color": self.color}

        paths = {"dir": self.dir}
        paths["srcdir"] = self.sources.dir if self.sources is not None else ""

        for attr in ["LD_PRELOAD", "LD_LIBRARY_PATH", "cmd_prefix"]:
            value = getattr(self, attr, "") or ""
            if value != "":
                value = value.format(**paths)
                res_dict[attr] = value

        print_debug("Resulting dictionary:", res_dict)
        return res_dict


def read_allocators_collection_file(alloc_path):
    """Read and evaluate a python file looking for an exported dict called allocators"""

    exec_globals = {"__file__": alloc_path}
    with open(alloc_path, "r") as alloc_file:
        exec(compile(alloc_file.read()), exec_globals)

    if "allocators" in exec_globals:
        return exec_globals["allocators"]

    print_error("No global dictionary 'allocators' in", alloc_path)
    return {}

def collect_allocators(allocators):
    """Collect allocators to benchmark

    If allocators is None we use either the allocators exported in the default
    allocators file at build/allocators/allocators.py or the ones installed.

    Otherwise allocators is interpreted as a list of names or files. If an entry in
    allocators is a file it is handled as a allocator collection file exporting
    a allocators variable. If the entry is no file it is interpreted as an allocator
    name and is searched for in our allocator definitions located at src/allocators.
    """

    # Default allocators definition file
    default_allocators_file = "build/allocators/allocators.py"

    if allocators is None and os.path.isfile(default_allocators_file):
        return read_allocators_collection_file(default_allocators_file)

    if allocators is not None:
        ret = {}
        for name in allocators:
            # file exists -> interpret as python file with a global variable allocators
            if os.path.isfile(name):
                print_status("Sourcing allocators definitions at", name, "...")
                ret.update(read_allocators_collection_file(name))

            # file is one of our allocator definitions import it
            elif os.path.isfile("src/allocators/" + name + ".py"):
                module = importlib.import_module('src.allocators.' + name)
                # name is collection
                if hasattr(module, "allocators"):
                    for alloc in module.allocators:
                        ret[alloc.name] = alloc.build()
                # name is single allocator
                elif issubclass(getattr(module, name).__class__, src.allocator.Allocator):
                    ret[name] = getattr(module, name).build()
            else:
                print_error(name, "is neither a python file or a known allocator definition.")
        return ret

    print_status("Using system-wide installed allocators ...")
    importlib.import_module('src.allocators.installed_allocators')
    return src.allocators.installed_allocators.allocators
