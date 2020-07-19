#!/usr/bin/env python3

# Copyright 2020 Florian Fischer <florian.fl.fischer@fau.de>
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
"""Integration tests for in allocbench included benchmarks"""

import unittest
import subprocess


class TestDummy(unittest.TestCase):
    """Test the dummy benchmark"""
    def test_execution(self):
        """Test if it executes successfully and outputs something"""
        cmd = './bench.py -b dummy -a system_default -r 1 -vv'
        try:
            res = subprocess.check_output(cmd.split(),
                                          text=True,
                                          stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(e.stdout)
            print(e.stderr)
            raise

        # allocbench should output something
        self.assertNotEqual(res, "")


if __name__ == '__main__':
    unittest.main()
