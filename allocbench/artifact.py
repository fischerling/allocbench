# Copyright 2018-2020 Florian Fischer <florian.fl.fischer@fau.de>
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

import logging
from subprocess import CalledProcessError

from allocbench.directories import get_allocbench_base_dir
from allocbench.util import print_status, run_cmd, sha1sum

ARTIFACT_STORE_DIR = get_allocbench_base_dir() / "cache"

logger = logging.getLogger(__file__)


class Artifact:
    """Base class for external ressources"""
    def __init__(self, name):
        self.name = name
        self.basedir = ARTIFACT_STORE_DIR / name

    def _retrieve(self, cmd):
        """Run cmd to retrieve the artifact"""
        self.basedir.mkdir(exist_ok=True)

        print_status(f'Retrieving artifact "{self.name}" ...')
        logger.debug("By running: %s in %s", cmd, self.basedir)
        run_cmd(cmd, output_verbosity=1, cwd=self.basedir)


GIT_FETCH_CMD = ["git", "fetch", "--force", "--tags"]


class GitArtifact(Artifact):
    """External git repository"""
    def __init__(self, name, url):
        super().__init__(name)
        self.url = url
        self.repo = self.basedir / "repo"

    def retrieve(self):
        """clone the git repo"""
        super()._retrieve(
            ["git", "clone", "--recursive", "--bare", self.url, "repo"])

    def provide(self, checkout, location=None):
        """checkout new worktree at location"""
        if not location:
            location = self.basedir / checkout

        # check if we have already provided this checkout
        if location.exists():
            try:
                run_cmd(GIT_FETCH_CMD, output_verbosity=1, cwd=location)
            except CalledProcessError:
                logger.error("Failed to update %s", location)
                raise
            try:
                run_cmd(["git", "reset", "--hard", checkout],
                        output_verbosity=1,
                        cwd=location)
            except CalledProcessError:
                logger.error("Failed to update %s", location)
                raise
            return location

        # check if we have already retrieved the repo
        if not self.repo.exists():
            self.retrieve()

        worktree_cmd = ["git", "worktree", "add", location, checkout]
        logger.debug("create new worktree. By running: %s in %s", worktree_cmd,
                     self.repo)
        try:
            run_cmd(worktree_cmd, output_verbosity=1, cwd=self.repo)
        except CalledProcessError:
            # update repo
            print_status(f'Updating git repository "{self.name}" ...')
            try:
                run_cmd(GIT_FETCH_CMD, output_verbosity=1, cwd=self.repo)
            except CalledProcessError:
                logger.error("Failed to update %s", self.name)
                raise

            try:
                run_cmd(worktree_cmd, output_verbosity=1, cwd=self.repo)
            except CalledProcessError:
                logger.error("Failed to provide %s", self.name)
                raise

        submodule_init_cmd = [
            "git", "submodule", "update", "--init", "--recursive"
        ]
        logger.debug("update submodules in worktree. By running: %s in %s",
                     submodule_init_cmd, self.repo)
        run_cmd(submodule_init_cmd, output_verbosity=1, cwd=location)
        return location


class ArchiveArtifact(Artifact):
    """External archive"""
    supported_formats = ["tar"]

    def __init__(self, name, url, archive_format, checksum):
        super().__init__(name)
        self.url = url
        if archive_format not in self.supported_formats:
            raise Exception(
                f'Archive format "{format}" not in supported list {self.supported_formats}'
            )
        self.archive_format = archive_format
        self.archive = self.basedir / f"{self.name}.{self.archive_format}"
        self.checksum = checksum

    def retrieve(self):
        """download the archive"""
        super()._retrieve(["wget", "-O", self.archive, self.url])

    def provide(self, location=None):
        """extract the archive"""

        # Download archive
        if not self.archive.exists():
            self.retrieve()

        # compare checksums
        logger.info("Verify checksum ...")
        if sha1sum(self.archive) != self.checksum:
            raise Exception(
                f"Archive {self.archive} does not match provided checksum")

        if not location:
            location = self.basedir / "content"

        # Check if we already provided the archive at location
        if location.exists():
            return location

        location.mkdir(exist_ok=True)

        # Extract archive
        if self.archive_format == "tar":
            cmd = ["tar", "Cxf", location, self.archive]

        logger.debug("extract archive by running: %s in %s", cmd, self.basedir)
        run_cmd(cmd, output_verbosity=1, cwd=self.basedir)
        return location
