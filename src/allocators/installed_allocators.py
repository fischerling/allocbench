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
# along with allocbench.
"""Collect allocators using installed system libraries"""

import subprocess

# TODO: add more allocators
MAYBE_ALLOCATORS = ["tcmalloc", "jemalloc", "hoard"]

allocators = {
    "libc": {
        "cmd_prefix": "",
        "binary_suffix": "",
        "LD_PRELOAD": "",
        "LD_LIBRARY_PATH": "",
        "color": "C1"
    }
}

for i, t in enumerate(MAYBE_ALLOCATORS):
    try:
        path = subprocess.run('whereis lib{} | cut -d":" -f2'.format(t),
                              shell=True,
                              stdout=subprocess.PIPE,
                              universal_newlines=True).stdout.strip()
    except:
        continue

    if path != "":
        allocators[t] = {
            "cmd_prefix": "",
            "binary_suffix": "",
            "LD_PRELOAD": path,
            "LD_LIBRARY_PATH": "",
            "color": "C" + str(i + 2)
        }
