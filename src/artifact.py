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

"""Artifact classes

An Artifact is a external ressource downloaded from the internet.
There are two flavours of artifacts available: archives and git repositories.
Both flavours are version controlled archive with a checksum and git repositories
with a specific checkout.
"""

import os
import subprocess

import src.globalvars
from src.util import print_info, print_debug

ARTIFACT_STORE_DIR = os.path.join(src.globalvars.allocbenchdir, "cache")

class Artifact:
    """Base class for external ressources"""
    store = {}

    def __init__(self, name):
        if name in Artifact.store:
            raise Exception(f'duplicate artifact "{name}"')

        Artifact.store[name] = self
        self.name = name
        self.basedir = os.path.join(ARTIFACT_STORE_DIR, name)

    def retrieve(self, cmd):
        """Run cmd to retrieve the artifact"""
        os.makedirs(self.basedir, exist_ok=True)

        print_info(f'Retrieving artifact "{self.name}"')
        print_debug(f"By running: {cmd} in {self.basedir}")
        proc = subprocess.run(cmd, cwd=self.basedir,
                              # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
        if proc.returncode != 0:
            raise Exception(f"Failed to retrieve {self.name}")


class GitArtifact(Artifact):
    """External git repository"""
    def __init__(self, name, url):
        super().__init__(name)
        self.url = url
        self.repo = os.path.join(self.basedir, "repo")

    def retrieve(self):
        """clone the git repo"""
        super().retrieve(["git", "clone", "--recursive", "--bare", self.url, "repo"])

    def provide(self, checkout, location=None):
        """checkout new worktree at location"""
        if not location:
            location = os.path.join(self.basedir, checkout)

        # check if we have already provided this checkout
        if os.path.exists(location):
            return

        # check if we have already retrieved the repo
        if not os.path.exists(self.repo):
            self.retrieve()

        print_debug("create new worktree. By running: ",
                    ["git", "worktree", "add", location, checkout], f"in {self.repo}")
        proc = subprocess.run(["git", "worktree", "add", location, checkout], cwd=self.repo,
                              # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
        if proc.returncode != 0:
            raise Exception(f"Failed to provide {self.name}")
