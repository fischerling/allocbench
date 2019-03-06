import os


"""Dict holding facts about the current benchmark run"""
facts = {}

"""Verbosity level -1: quiet, 0: status, 1: info, 2: stdout of subcommands, 3: debug info"""
verbosity = 0

"""Dict holding the allocators to compare"""
allocators = {}

"""File were the allocators definitions are loaded from"""
allocators_file = None

"""Path of the build directory"""
builddir = os.path.join(os.getcwd(), "build")
