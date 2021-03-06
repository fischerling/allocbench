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

from pathlib import Path
from subprocess import CalledProcessError

from allocbench.directories import get_allocbench_base_dir, PathType
from allocbench.util import print_status, run_cmd, sha1sum, get_logger, CmdType

ARTIFACT_STORE_DIR = get_allocbench_base_dir() / "cache"

logger = get_logger(__file__)


class Artifact:  # pylint: disable=too-few-public-methods
    """Base class for external ressources"""
    def __init__(self, name: str):
        self.name = name
        self.basedir = ARTIFACT_STORE_DIR / name

    def _retrieve(self, cmd: CmdType):
        """Run cmd to retrieve the artifact"""
        self.basedir.mkdir(exist_ok=True)

        print_status(f'Retrieving artifact "{self.name}" ...')
        logger.debug("By running: %s in %s", cmd, self.basedir)
        run_cmd(cmd, output_verbosity=1, cwd=self.basedir)


GIT_FETCH_CMD = ["git", "fetch", "--force", "--tags"]


class GitArtifact(Artifact):
    """External git repository"""
    def __init__(self, name: str, url: str):
        super().__init__(name)
        self.url = url
        self.repo = self.basedir / "repo"

    def retrieve(self):
        """clone the git repo"""
        super()._retrieve(
            ["git", "clone", "--recursive", "--bare", self.url, "repo"])

    def provide(self, checkout: str, location: PathType = None):
        """checkout new worktree at location"""
        if not location:
            location = self.basedir / checkout

        # make sure location is a pathlib Path object
        location = Path(location)

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

        worktree_cmd = ["git", "worktree", "add", str(location), checkout]
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

    def __init__(self, name: str, url: str, archive_format: str,
                 checksum: str):
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

    def provide(self, location: PathType = None):
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

        # make sure location is a pathlib Path object
        location = Path(location)

        # Check if we already provided the archive at location
        if location.exists():
            return location

        location.mkdir(exist_ok=True)

        # Extract archive
        if self.archive_format == "tar":
            cmd = ["tar", "Cxf", str(location), str(self.archive)]

        logger.debug("extract archive by running: %s in %s", cmd, self.basedir)
        run_cmd(cmd, output_verbosity=1, cwd=self.basedir)
        return location
