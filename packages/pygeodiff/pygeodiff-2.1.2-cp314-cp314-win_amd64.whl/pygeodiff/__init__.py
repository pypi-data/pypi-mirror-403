# -*- coding: utf-8 -*-
"""
    pygeodiff
    -----------
    This module provides tools for create diffs of geospatial data formats
    :copyright: (c) 2019-2022 Lutra Consulting Ltd.
    :license: MIT, see LICENSE for more details.
"""


# start delvewheel patch
def _delvewheel_patch_1_12_0():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'pygeodiff.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_12_0()
del _delvewheel_patch_1_12_0
# end delvewheel patch

from .main import GeoDiff
from .geodifflib import (
    GeoDiffLibError,
    GeoDiffLibConflictError,
    GeoDiffLibUnsupportedChangeError,
    GeoDiffLibVersionError,
    ChangesetEntry,
    ChangesetReader,
    UndefinedValue,
)

__all__ = [
    "GeoDiff",
    "GeoDiffLibError",
    "GeoDiffLibConflictError",
    "GeoDiffLibUnsupportedChangeError",
    "GeoDiffLibVersionError",
    "ChangesetEntry",
    "ChangesetReader",
    "UndefinedValue",
]
