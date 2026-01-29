"""
bspmap - B-spline mapping library with Python bindings.

High-level Python interface to the bspmap C++ library.
"""

from .capi import get_version, deboor_cox, debug_print, find_interval, compute_weight, basis_derivative

from . import capi

from .bsp import BSP

from .basis import Basis, BasisCircular, BasisClamped

__version__ = get_version()

__all__ = [
    'get_version',
    'deboor_cox', 
    'debug_print',
    'find_interval',
    'compute_weight',
    'basis_derivative',
    'BSP',
    'Basis',
    'BasisCircular',
    'BasisClamped',
]
