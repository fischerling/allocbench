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
"""Functions to obtain specific directories in the allocbench directory tree"""

from pathlib import Path
from typing import Optional, Union

# /.../allocbench/allocbench
SRCDIR = Path(__file__).parent


def get_allocbench_src_dir() -> Path:
    """Return path to allocbench's sources"""
    return SRCDIR


# /.../allocbench/
BASEDIR = SRCDIR.parent


def get_allocbench_base_dir() -> Path:
    """Return path to allocbench's root directory"""
    return BASEDIR


# /.../allocbench/allocbench/benchmarks
BENCHSRCDIR = SRCDIR / "benchmarks"


def get_allocbench_benchmark_src_dir() -> Path:
    """Return path to benchmark definitions and sources"""
    return BENCHSRCDIR


# /.../allocbench/allocbench/allocators
ALLOCSRCDIR = SRCDIR / "allocators"


def get_allocbench_allocator_src_dir() -> Path:
    """Return path to allocator definitions"""
    return ALLOCSRCDIR


# /.../allocbench/build
BUILDDIR = BASEDIR / "build"


def get_allocbench_build_dir() -> Path:
    """Return path to allocbench's build directory"""
    return BUILDDIR


# /.../allocbench/build/allocators
ALLOCBUILDDIR = BUILDDIR / "allocators"


def get_allocbench_allocator_build_dir() -> Path:
    """Return path to the allocators build directory"""
    return ALLOCBUILDDIR


# /.../allocbench/build/allocators
BENCHMARKBUILDDIR = BUILDDIR / "benchmarks"


def get_allocbench_benchmark_build_dir() -> Path:
    """Return path to the benchmarks build directory"""
    return BENCHMARKBUILDDIR


RESDIR = None


def set_current_result_dir(resdir: Union[Path, str]):
    """Set the path to the result directory of the current invocation and silently create it"""
    global RESDIR
    RESDIR = Path(resdir)
    RESDIR.mkdir(parents=True, exist_ok=True)


def get_current_result_dir() -> Optional[Path]:
    """Return the path to the results of the current invocation"""
    return RESDIR
