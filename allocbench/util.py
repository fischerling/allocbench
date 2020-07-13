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
"""Helper functions for allocbench"""

import hashlib
import logging
import os
import subprocess
import sys

# Verbosity level -1: quiet, 0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG
VERBOSITY = 0


def set_verbosity(verbosity: int):
    """Set global logging level

    0 (default): logging.WARNING
    1: logging.INFO
    2: logging.DEBUG
    """
    loglevels = [logging.ERROR, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=loglevels[verbosity])
    global VERBOSITY
    VERBOSITY = verbosity


logger = logging.getLogger(__file__)


def run_cmd(cmd,
            output_verbosity=2,
            capture=False,
            shell=False,
            check=True,
            cwd=None,
            input=None):  # pylint: disable=redefined-builtin
    """subprocess.run wrapper which cares about the set verbosity"""
    if capture:
        stdout = subprocess.PIPE
        stderr = stdout
    elif VERBOSITY < output_verbosity:
        stdout = subprocess.DEVNULL
        stderr = stdout
    else:
        stdout = None
        stderr = stdout

    logger.debug("Running command %s", cmd)

    return subprocess.run(cmd,
                          stdout=stdout,
                          stderr=stderr,
                          shell=shell,
                          check=check,
                          input=input,
                          cwd=cwd,
                          universal_newlines=True)


def is_exe(fpath):
    """Check if the given path is an exexutable file"""
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def find_cmd(cmd):
    """Return abspath of cmd if it is an executable or in PATH"""
    fpath, _ = os.path.split(cmd)

    # Search for file
    if fpath:
        if is_exe(cmd):
            return cmd
    # Search in PATH
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, cmd)
            if is_exe(exe_file):
                return exe_file

    return None


def prefix_cmd_with_abspath(cmd):
    """Prefix cmd with the abspath of the first word

    Usefull if cmd should be executed by the loader of a custom glibc."""

    if os.path.isabs(cmd) or cmd == "":
        return cmd

    binary_end = cmd.find(" ")
    binary_end = None if binary_end == -1 else binary_end

    binary_abspath = find_cmd(cmd[0:binary_end])

    # add arguments of cmd to the abspath
    if binary_end:
        return binary_abspath + " " + cmd[binary_end:]
    return binary_abspath


def allocbench_msg(color, *objects, sep=' ', end='\n', file=None):
    """Colored output function wrapping print"""
    if VERBOSITY < 0:
        return

    color = {
        "YELLOW": "\x1b[33m",
        "GREEN": "\x1b[32m",
        "RED": "\x1b[31m"
    }[color]

    is_atty = sys.stdout.isatty()
    if is_atty:
        print(color, end="", file=file, flush=True)

    print(*objects, sep=sep, end=end, file=file)

    if is_atty:
        print("\x1b[0m", end="", file=file, flush=True)


def print_status(*objects, sep=' ', end='\n', file=None):
    """Print green status message"""
    allocbench_msg("GREEN", *objects, sep=sep, end=end, file=file)


def print_license_and_exit():
    """Print GPL info and Copyright before exit"""
    print("Copyright (C) 2018-2020 Florian Fischer")
    print(
        "License GPLv3: GNU GPL version 3 <http://gnu.org/licenses/gpl.html>")
    sys.exit(0)


def sha1sum(filename):
    """Return sha1sum of a file"""
    sha1 = hashlib.sha1()
    barray = bytearray(64 * 1024)
    view = memoryview(barray)
    with open(filename, 'rb', buffering=0) as input_file:
        for bytes_read in iter(lambda: input_file.readinto(view), 0):
            sha1.update(view[:bytes_read])
    return sha1.hexdigest()
