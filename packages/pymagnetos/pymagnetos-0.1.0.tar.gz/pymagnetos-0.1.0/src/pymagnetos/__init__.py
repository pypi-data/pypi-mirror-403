"""
The pymagnetos package.

It provides analysis tools for high magnetic field experiments.
"""

import nexusformat.nexus as nx

from . import core, pytdo, pyuson
from .core import sp, utils

__all__ = ["core", "pytdo", "pyuson", "sp", "utils"]

# Configure NeXus globally
nx.nxsetconfig(compression=None, encoding="utf-8", lock=0, memory=8000, recursive=True)
