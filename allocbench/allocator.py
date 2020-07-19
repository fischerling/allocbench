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
import fnmatch
import inspect
import importlib
import os
from pathlib import Path
import shutil
from subprocess import CalledProcessError
from typing import List, Optional, Dict, Iterable

from allocbench.artifact import Artifact, ArchiveArtifact, GitArtifact
from allocbench.util import print_status, run_cmd, get_logger
from allocbench.directories import (get_allocbench_build_dir,
                                    get_allocbench_allocator_src_dir,
                                    get_allocbench_allocator_build_dir)

logger = get_logger(__file__)

LIBRARY_PATH = ""
for line in run_cmd(["ldconfig", "-v", "-N"],
                    capture=True).stdout.splitlines():

    if not line.startswith('\t'):
        LIBRARY_PATH += line

SRCDIR = Path(get_allocbench_build_dir()) / "src"

SRCDIR.mkdir(parents=True, exist_ok=True)

AllocatorDict = Dict[str, Optional[str]]
AllocatorCollection = Dict[str, AllocatorDict]


class Allocator:
    """Allocator base class

    An Allocator can contain an Artifact which provides the allocator sources,
    patches, and instructions to build the allocator.
    Allocator.build will compile the allocator and produce a for allocbench usable
    allocator dict"""

    binary_suffix = ''
    cmd_prefix = ''
    ld_preload = ''
    ld_library_path = ''
    color = None
    sources: Optional[Artifact] = None
    version = ''
    patches: List[str] = []
    prepare_cmds: List[str] = []
    build_cmds: List[str] = []
    analyze_alloc = False

    def __init__(self, name, **kwargs):
        self.class_file = Path(inspect.getfile(self.__class__))
        self.name = name
        self.srcdir = SRCDIR / self.name
        self.dir = get_allocbench_allocator_build_dir() / self.name
        self.patchdir = Path(self.class_file.parent, self.class_file.stem)

        # Update attributes
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def prepare(self):
        """Prepare the allocators sources"""
        if not self.sources and self.srcdir.exists():
            return

        print_status("Preparing", self.name, "...")
        if isinstance(self.sources, GitArtifact):
            self.sources.provide(self.version, self.srcdir)
        elif isinstance(self.sources, ArchiveArtifact):
            self.sources.provide(self.srcdir)

        if self.patches:
            cwd = self.srcdir

            print_status(f"Patching {self.name} ...")
            for patch in self.patches:
                with open(patch.format(patchdir=self.patchdir),
                          "r") as patch_file:
                    patch_content = patch_file.read()

                # check if patch is already applied
                not_patched = run_cmd([
                    "patch", "-R", "-p0", "-s", "-f", "--dry-run", "--verbose"
                ],
                                      cwd=cwd,
                                      input=patch_content,
                                      check=False).returncode
                if not_patched:
                    try:
                        run_cmd(["patch", "-p0", "--verbose"],
                                cwd=cwd,
                                input=patch_content)
                    except CalledProcessError as err:
                        logger.debug("%s", err.stderr)
                        logger.error("Patching of %s failed.", self.name)
                        raise

        if self.prepare_cmds:
            print_status(f"Run prepare commands {self.name} ...")
            for cmd in self.prepare_cmds:
                try:
                    run_cmd(cmd, shell=True, cwd=self.srcdir)
                except CalledProcessError as err:
                    logger.debug("%s", err.stderr)
                    logger.error("Prepare %s failed", self.name)
                    raise

    def build(self) -> AllocatorDict:
        """Build the allocator if needed and produce an allocator dict"""
        if self.build_cmds:
            build_needed = not self.dir.is_dir()
            buildtimestamp_path = self.dir / ".buildtime"

            if not build_needed:
                logger.info("Old build found. Comparing build time with mtime")

                with open(buildtimestamp_path, "r") as buildtimestamp_file:
                    timestamp = datetime.fromtimestamp(
                        float(buildtimestamp_file.read()))

                st_mtime = os.stat(self.class_file).st_mtime
                modtime = datetime.fromtimestamp(st_mtime)

                build_needed = timestamp < modtime

                logger.debug("Time of last build: %s", timestamp.isoformat())
                logger.debug("Last modification of allocators file: %s",
                             modtime.isoformat())
                logger.info("%sbuild needed", "" if build_needed else "No ")

            if build_needed:
                self.prepare()
                print_status("Building", self.name, "...")

                for cmd in self.build_cmds:
                    cmd = cmd.format(dir=self.dir, srcdir=self.srcdir)

                    try:
                        run_cmd(cmd,
                                cwd=get_allocbench_allocator_build_dir(),
                                shell=True)
                    except CalledProcessError as err:
                        logger.debug("%s", err.stderr)
                        logger.error("Building %s failed", self.name)
                        shutil.rmtree(self.dir, ignore_errors=True)
                        raise

                with open(buildtimestamp_path, "w") as buildtimestamp_file:
                    logger.info("Save build time to: %s", buildtimestamp_path)
                    buildtimestamp_file.write(str(datetime.now().timestamp()))

        logger.info("Create allocator dictionary")
        res_dict = {
            "cmd_prefix": self.cmd_prefix,
            "binary_suffix": self.binary_suffix,
            "LD_PRELOAD": self.ld_preload,
            "LD_LIBRARY_PATH": self.ld_library_path,
            "color": self.color,
            "version": self.version
        }

        for attr in ["LD_PRELOAD", "LD_LIBRARY_PATH", "cmd_prefix"]:
            value = getattr(self, attr.lower(), "")
            if value != "":
                value = value.format(dir=self.dir, srcdir=self.srcdir)
                res_dict[attr] = value

        logger.debug("Resulting dictionary: %s", res_dict)
        return res_dict


def collect_installed_allocators() -> AllocatorCollection:
    """Collect allocators using installed system libraries"""

    maybe_allocators = list(collect_available_allocators().keys())

    allocators = {
        "libc": {
            "cmd_prefix": "",
            "binary_suffix": "",
            "LD_PRELOAD": "",
            "LD_LIBRARY_PATH": "",
            "color": None
        }
    }

    for alloc in maybe_allocators:
        try:
            path = run_cmd(f'whereis lib{alloc} | cut -d":" -f2',
                           shell=True,
                           capture=True).stdout.strip()
        except CalledProcessError:
            continue

        if path != "":
            allocators[alloc] = {
                "cmd_prefix": "",
                "binary_suffix": "",
                "LD_PRELOAD": path,
                "LD_LIBRARY_PATH": "",
                "color": None,
            }

    return allocators


def collect_available_allocators() -> Dict[str, Allocator]:
    """Collect all allocator definitions shipped with allocbench"""

    available_allocators = {}

    for alloc_def_path in get_allocbench_allocator_src_dir().glob('*.py'):
        alloc_module_name = f'allocbench.allocators.{alloc_def_path.stem}'
        module = importlib.import_module(alloc_module_name)
        for name, obj in module.__dict__.items():
            if issubclass(obj.__class__, Allocator) and not obj.analyze_alloc:
                available_allocators[name] = obj

    return available_allocators


def read_allocators_collection_file(alloc_path) -> AllocatorCollection:
    """Read and evaluate a python file looking for an exported dict called allocators"""

    exec_globals = {"__file__": alloc_path}
    with open(alloc_path, "r") as alloc_file:
        exec(compile(alloc_file.read(), alloc_path, 'exec'), exec_globals)  #pylint: disable=exec-used

    if "allocators" not in exec_globals:
        logger.error("No global dictionary 'allocators' in %s", alloc_path)
        return {}

    res = {}
    for name, alloc in exec_globals["allocators"]:
        if issubclass(alloc.__class__, Allocator):
            res[name] = alloc.build()
        else:
            # TODO: check v's type
            res[name] = alloc

    return res


def collect_allocators(
        allocators: Optional[Iterable[str]]) -> AllocatorCollection:
    """Collect allocators to benchmark

    If allocators is None we use either the allocators exported in the default
    allocators file at build/allocators/allocators.py or the ones installed.

    Otherwise allocators is interpreted as a sequence of names or files. If an entry in
    allocators is a file it is handled as a allocator collection file exporting
    a allocators variable. If the entry is no file it is interpreted as an allocator
    name and is searched for in our allocator definitions located at allocbench/allocators.
    """

    # Default allocators definition file
    default_allocators_file = "build/allocators/allocators.py"

    if allocators is None:
        if os.path.isfile(default_allocators_file):
            return read_allocators_collection_file(default_allocators_file)

        print_status("Using system-wide installed allocators ...")
        return collect_installed_allocators()

    available_allocators = collect_available_allocators()

    ret = {}
    for name in allocators:
        if name == "all":
            return {
                alloc_name: alloc.build()
                for alloc_name, alloc in available_allocators.items()
            }

        # file exists -> interpret as python file with a global variable allocators
        if os.path.isfile(name):
            print_status("Sourcing allocators definitions at", name, "...")
            ret.update(read_allocators_collection_file(name))

        # interpret name as allocator name or wildcard
        else:
            matched_allocators = fnmatch.filter(available_allocators.keys(),
                                                name)
            if matched_allocators:
                ret.update({
                    a: available_allocators[a].build()
                    for a in matched_allocators
                })
            else:
                logger.error(
                    '"%s" is neither a python file or a known allocator definition.',
                    name)
    return ret
