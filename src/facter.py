import multiprocessing
import os
import platform
import sys

import src.globalvars as gv


# Populate src.globalvars.facts on import
_uname = platform.uname()
gv.facts["hostname"] = _uname.node
gv.facts["system"] = _uname.system
gv.facts["kernel"] = _uname.release
gv.facts["arch"] = _uname.machine
gv.facts["cpus"] = multiprocessing.cpu_count()

with open(os.path.join(gv.builddir, "ccinfo"), "r") as ccinfo:
    gv.facts["cc"] = ccinfo.readlines()[-1][:-1]


def get_libc_version(bin=None):
    bin = bin or sys.executable
    platform.libc_ver(executable=bin)
