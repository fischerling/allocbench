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

"""malt allocator definition

Malt is a malloc tracker and used to capture and analyse the allocation profile
of a program. See https://github.com/memtt/malt for more details
"""

from src.allocator import Allocator

# result_dir and perm are substituted during Benchmark.run
malt = Allocator("malt", cmd_prefix="malt -q -o output:name={{result_dir}}/malt.{{perm}}.%3")
