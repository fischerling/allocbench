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
from subprocess import CalledProcessError
import sys

from src.artifact import ArchiveArtifact, GitArtifact
import src.globalvars
from src.util import print_status, print_debug, print_error, print_info2, run_cmd

LIBRARY_PATH = ""
for line in run_cmd(["ldconfig", "-v", "-N"],
                    capture=True).stdout.splitlines():

    if not line.startswith('\t'):
        LIBRARY_PATH += line

BUILDDIR = src.globalvars.allocbuilddir
SRCDIR = os.path.join(src.globalvars.allocbuilddir, "src")

if not os.path.isdir(SRCDIR):
    os.makedirs(SRCDIR)


class Allocator:
    """Allocator base class

    An Allocator can contain an Artifact which provides the allocator sources,
    patches, and instructions to build the allocator.
    Allocator.build will compile the allocator and produce a for allocbench usable
    allocator dict"""
    allowed_attributes = [
        "binary_suffix", "cmd_prefix", "LD_PRELOAD", "LD_LIBRARY_PATH",
        "color", "sources", "version", "patches", "prepare_cmds", "build_cmds"
    ]

    def __init__(self, name, **kwargs):
        self.class_file = inspect.getfile(self.__class__)
        self.name = name
        self.srcdir = os.path.join(SRCDIR, self.name)
        self.dir = os.path.join(BUILDDIR, self.name)
        self.patchdir = os.path.join(os.path.splitext(self.class_file)[0])

        # members known by the base class
        self.binary_suffix = self.binary_suffix if hasattr(self, "binary_suffix") else None
        self.cmd_prefix = self.cmd_prefix if hasattr(self, "cmd_prefix") else None
        self.LD_PRELOAD = self.LD_PRELOAD if hasattr(self, "LD_PRELOAD") else None
        self.LD_LIBRARY_PATH = self.LD_LIBRARY_PATH if hasattr(self, "LD_LIBRARY_PATH") else None
        self.color = self.color if hasattr(self, "color") else None
        self.sources = self.sources if hasattr(self, "sources") else None
        self.version = self.version if hasattr(self, "version") else None
        self.patches = self.patches if hasattr(self, "patches") else []
        self.prepare_cmds = self.prepare_cmds if hasattr(self, "prepare_cmds") else []
        self.build_cmds = self.build_cmds if hasattr(self, "build_cmds") else []

        # Update attributes
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def prepare(self):
        """Prepare the allocators sources"""
        if not self.sources and os.path.exists(self.srcdir):
            return

        print_status("Preparing", self.name, "...")
        if isinstance(self.sources, GitArtifact):
            self.sources.provide(self.version, self.srcdir)
        elif isinstance(self.sources, ArchiveArtifact):
            self.sources.provide(self.srcdir)

        if self.patches:
            cwd = os.path.join(SRCDIR, self.name)

            print_status(f"Patching {self.name} ...")
            for patch in self.patches:
                with open(patch.format(patchdir=self.patchdir),
                          "r") as patch_file:
                    patch_content = patch_file.read()

                # check if patch is already applied
                not_patched = run_cmd(
                    ["patch", "-R", "-p0", "-s", "-f", "--dry-run", "--verbose"],
                    cwd=cwd,
                    input=patch_content,
                    check=False).returncode
                if not_patched:
                    try:
                        run_cmd(["patch", "-p0", "--verbose"], cwd=cwd, input=patch_content)
                    except CalledProcessError as e:
                        print_debug(e.stderr, file=sys.stderr)
                        print_error(f"Patching of {self.name} failed.")
                        raise e

        if self.prepare_cmds:
            print_status(f"Run prepare commands {self.name} ...")
            for cmd in self.prepare_cmds:
                try:
                    run_cmd(cmd, shell=True, cwd=self.srcdir)
                except CalledProcessError as e:
                    print_debug(e.stderr, file=sys.stderr)
                    print_error(f"Prepare {self.name} failed")
                    raise e

    def build(self):
        """Build the allocator if needed and produce an allocator dict"""
        build_needed = not os.path.isdir(self.dir)
        buildtimestamp_path = os.path.join(self.dir, ".buildtime")

        if not build_needed:
            print_info2("Old build found. Comparing build time with mtime")

            with open(buildtimestamp_path, "r") as buildtimestamp_file:
                timestamp = datetime.fromtimestamp(
                    float(buildtimestamp_file.read()))

            modtime = os.stat(self.class_file).st_mtime
            modtime = datetime.fromtimestamp(modtime)

            build_needed = timestamp < modtime

            print_debug("Time of last build:", timestamp.isoformat())
            print_debug("Last modification of allocators file:",
                        modtime.isoformat())
            print_info2("" if build_needed else "No " + "build needed")

        if build_needed:
            self.prepare()
            print_status("Building", self.name, "...")

            if self.build_cmds:
                for cmd in self.build_cmds:
                    cmd = cmd.format(dir=self.dir, srcdir=self.srcdir)

                    try:
                        run_cmd(cmd, cwd=BUILDDIR, shell=True)
                    except CalledProcessError as e:
                        print_debug(e.stderr, file=sys.stderr)
                        print_error(f"Builing {self.name} failed")
                        shutil.rmtree(self.dir, ignore_errors=True)
                        raise e

                with open(buildtimestamp_path, "w") as buildtimestamp_file:
                    print_info2("Save build time to:", buildtimestamp_path)
                    buildtimestamp_file.write(str(datetime.now().timestamp()))

        print_info2("Create allocator dictionary")
        res_dict = {
            "cmd_prefix": self.cmd_prefix or "",
            "binary_suffix": self.binary_suffix or "",
            "LD_PRELOAD": self.LD_PRELOAD or "",
            "LD_LIBRARY_PATH": self.LD_LIBRARY_PATH or "",
            "color": self.color
        }

        for attr in ["LD_PRELOAD", "LD_LIBRARY_PATH", "cmd_prefix"]:
            value = getattr(self, attr, "") or ""
            if value != "":
                value = value.format(dir=self.dir, srcdir=self.srcdir)
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

    ret = {}
    for name in allocators:
        if name == "installed":
            print_status("Using system-wide installed allocators ...")
            importlib.import_module('src.allocators.installed_allocators')
            ret.update(src.allocators.installed_allocators.allocators)
        # file exists -> interpret as python file with a global variable allocators
        elif os.path.isfile(name):
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
            elif issubclass(
                    getattr(module, name).__class__, src.allocator.Allocator):
                ret[name] = getattr(module, name).build()
        else:
            print_error(
                name,
                "is neither a python file or a known allocator definition.")
    return ret
