import os
import subprocess
import sys

import src.globalvars


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

def find_cmd(cmd):
    fpath, fname = os.path.split(cmd)

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

    binary_end = cmd.find(" ")
    binary_end = None if binary_end == -1 else binary_end

    cmd_start = len(cmd) if binary_end == None else binary_end

    binary_abspath = subprocess.run(["whereis", cmd[0:binary_end]],
                                    stdout=subprocess.PIPE,
                                    universal_newlines=True).stdout.split()[1]

    return binary_abspath + " " + cmd[binary_end:]


def allocbench_msg(color, *objects, sep=' ', end='\n', file=sys.stdout):
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
    if src.globalvars.verbosity < 99:
        return
    print(*objects, sep=sep, end=end, file=file)

def print_info(*objects, sep=' ', end='\n', file=sys.stdout):
    if src.globalvars.verbosity < 1:
        return
    print(*objects, sep=sep, end=end, file=file)

def print_info0(*objects, sep=' ', end='\n', file=sys.stdout):
    if src.globalvars.verbosity < 0:
        return
    print(*objects, sep=sep, end=end, file=file)

def print_info2(*objects, sep=' ', end='\n', file=sys.stdout):
    if src.globalvars.verbosity < 2:
        return
    print(*objects, sep=sep, end=end, file=file)

def print_status(*objects, sep=' ', end='\n', file=sys.stdout):
    allocbench_msg("GREEN", *objects, sep=sep, end=end, file=file)

def print_warn(*objects, sep=' ', end='\n', file=sys.stdout):
    if src.globalvars.verbosity < 1:
        return
    allocbench_msg("YELLOW", *objects, sep=sep, end=end, file=file)

def print_error(*objects, sep=' ', end='\n', file=sys.stderr):
    allocbench_msg("RED", *objects, sep=sep, end=end, file=file)
