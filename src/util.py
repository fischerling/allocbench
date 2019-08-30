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

import os
import subprocess
import sys

import src.globalvars

def download_reporthook(blocknum, blocksize, totalsize):
    """Status report hook for urlretrieve"""
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 100 / totalsize
        status = "\r%5.1f%% %*d / %d" % (
                  percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(status)
    else:  # total size is unknown
        sys.stderr.write(f"\rdownloaded {readsofar}")


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

    binary_abspath = subprocess.run(["whereis", cmd[0:binary_end]],
                                    stdout=subprocess.PIPE,
                                    universal_newlines=True).stdout.split()[1]

    return binary_abspath + " " + cmd[binary_end:]


def allocbench_msg(color, *objects, sep=' ', end='\n', file=sys.stdout):
    """Colored output function wrapping print"""
    if src.globalvars.verbosity < 0:
        return

    color = {"YELLOW": "\x1b[33m",
             "GREEN": "\x1b[32m",
             "RED": "\x1b[31m"}[color]

    is_atty = sys.stdout.isatty()
    if is_atty:
        print(color, end="", file=file, flush=True)

    print(*objects, sep=sep, end=end, file=file)

    if is_atty:
        print("\x1b[0m", end="", file=file, flush=True)


def print_debug(*objects, sep=' ', end='\n', file=sys.stdout):
    """Print colorless debug message"""
    if src.globalvars.verbosity < 3:
        return
    print(*objects, sep=sep, end=end, file=file)


def print_info(*objects, sep=' ', end='\n', file=sys.stdout):
    """Print colorless info message"""
    if src.globalvars.verbosity < 1:
        return
    print(*objects, sep=sep, end=end, file=file)


def print_info0(*objects, sep=' ', end='\n', file=sys.stdout):
    """Print colorless info message at every verbosity level message"""
    if src.globalvars.verbosity < 0:
        return
    print(*objects, sep=sep, end=end, file=file)


def print_info2(*objects, sep=' ', end='\n', file=sys.stdout):
    """Print colorless info message at the second verbosity level message"""
    if src.globalvars.verbosity < 2:
        return
    print(*objects, sep=sep, end=end, file=file)


def print_status(*objects, sep=' ', end='\n', file=sys.stdout):
    """Print green status message"""
    allocbench_msg("GREEN", *objects, sep=sep, end=end, file=file)


def print_warn(*objects, sep=' ', end='\n', file=sys.stdout):
    """Print yellow warning"""
    if src.globalvars.verbosity < 1:
        return
    allocbench_msg("YELLOW", *objects, sep=sep, end=end, file=file)


def print_error(*objects, sep=' ', end='\n', file=sys.stderr):
    """Print red error message"""
    allocbench_msg("RED", *objects, sep=sep, end=end, file=file)


def print_license_and_exit():
    """Print GPL info and Copyright before exit"""
    print("Copyright (C) 2018-2019 Florian Fischer")
    print("License GPLv3: GNU GPL version 3 <http://gnu.org/licenses/gpl.html>")
    exit(0)


def print_version_and_exit():
    """Print current commit info before exit"""
    proc = subprocess.run(["git", "rev-parse", "HEAD"],
                          universal_newlines=True, stdout=subprocess.PIPE)

    if proc.returncode != 0:
        print_error("git rev-parse failed")
        exit(1)
    commit = proc.stdout[:-1]

    proc = subprocess.run(["git", "status", "--porcelain"],
                          universal_newlines=True, stdout=subprocess.PIPE)
    
    if proc.returncode != 0:
        print_error("git status --porcelain failed")
        exit(1)

    dirty = "-dirty" if proc.stdout != "" else ""
    
    print(f"{commit}{dirty}")
    exit(0)
