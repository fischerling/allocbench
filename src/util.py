import sys

import src.globalvars

def allocbench_msg(color, *objects, sep=' ', end='\n', file=sys.stdout):
    if src.globalvars.verbosity < 0:
        return
    
    color = {"YELLOW": "\x1b[33m",
             "GREEN": "\x1b[32m",
             "RED": "\x1b[31m"}[color]

    print(color, end="", file=file, flush=True)
    print(*objects, sep=sep, end=end, file=file)
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
