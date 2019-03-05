import colorama
import sys

import src.globalvars

def allocbench_msg(color, *objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    if src.globalvars.verbosity < 0:
        return
    color = getattr(colorama.Fore, color)
    print(color, end="", file=file)
    print(*objects, sep=sep, end=end, file=file)
    print(colorama.Fore.RESET, end="", file=file, flush=flush)

def print_debug(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    if src.globalvars.verbosity < 99:
        return
    print(*objects, sep=sep, end=end, file=file, flush=flush)

def print_info(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    if src.globalvars.verbosity < 1:
        return
    print(*objects, sep=sep, end=end, file=file, flush=flush)

def print_info0(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    if src.globalvars.verbosity < 0:
        return
    print(*objects, sep=sep, end=end, file=file, flush=flush)

def print_info2(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    if src.globalvars.verbosity < 2:
        return
    print(*objects, sep=sep, end=end, file=file, flush=flush)

def print_status(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    allocbench_msg("GREEN", *objects, sep=sep, end=end, file=file, flush=flush)

def print_warn(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    if src.globalvars.verbosity < 1:
        return
    allocbench_msg("YELLOW", *objects, sep=sep, end=end, file=file, flush=flush)

def print_error(*objects, sep=' ', end='\n', file=sys.stderr, flush=False):
    allocbench_msg("RED", *objects, sep=sep, end=end, file=file, flush=flush)
