import platform
import sys

def get_uname():
    return " ".join(platform.uname())

def get_kernel_version():
    return get_uname().split()[2]

def get_hostname():
    return platform.uname().node

def get_cc_version():
    with open("build/ccinfo", "r") as ccinfo:
        return ccinfo.readlines()[-1][:-1]

def get_libc_version(bin=None):
    bin = bin or sys.executable
    platform.libc_ver(executable=bin)
