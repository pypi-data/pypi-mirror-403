"""
C API bindings for bspmap using ctypes.
Direct low-level interface to the C library.
"""

import ctypes
import os
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np


# Locate the DLL
def _find_dll() -> Path:
    """Find the bspmap DLL in the package directory."""
    package_dir = Path(__file__).parent
    dll_dir = package_dir / "bin"
    
    if sys.platform == "win32":
        dll_name = "bspmap.dll"
    elif sys.platform == "darwin":
        dll_name = "libbspmap.dylib"
    else:
        dll_name = "libbspmap.so"
    
    dll_path = dll_dir / dll_name
    
    if not dll_path.exists():
        raise FileNotFoundError(
            f"Could not find {dll_name} in {dll_dir}. "
            "Please ensure the library is built and copied to the package directory."
        )
    
    return dll_path


# Load the DLL
_dll_path = _find_dll()
_lib = ctypes.CDLL(str(_dll_path))


# ==================== C API Function Declarations ====================

# ----- Version Info -----
_lib.bspmap_get_version.argtypes = []
_lib.bspmap_get_version.restype = ctypes.c_char_p


# ----- B-spline Basis Functions -----
_lib.bspmap_deboor_cox.argtypes = [
    ctypes.POINTER(ctypes.c_double),  # knot_vector
    ctypes.c_int,                      # knot_vector_size
    ctypes.c_int,                      # num_nodes
    ctypes.c_int,                      # degree
    ctypes.POINTER(ctypes.c_double),  # result (output)
]
_lib.bspmap_deboor_cox.restype = None


# ----- B-spline Basis Function Derivative -----
_lib.bspmap_basis_derivative.argtypes = [
    ctypes.POINTER(ctypes.c_double),  # basis_data
    ctypes.c_int,                      # dim1
    ctypes.c_int,                      # dim2
    ctypes.c_int,                      # dim3
    ctypes.POINTER(ctypes.c_double),  # result (output)
]
_lib.bspmap_basis_derivative.restype = None


# ----- Interval Finding -----
_lib.bspmap_find_interval.argtypes = [
    ctypes.POINTER(ctypes.c_double),  # knot_vector
    ctypes.c_int,                      # knot_vector_size
    ctypes.c_int,                      # degree
    ctypes.POINTER(ctypes.c_double),   # x
    ctypes.c_int,                      # size_x
    ctypes.POINTER(ctypes.c_int),     # interval_index (output)
]
_lib.bspmap_find_interval.restype = None


# ----- Weight Computation -----
_lib.bspmap_compute_weight.argtypes = [
    ctypes.POINTER(ctypes.c_double),  # basis_data
    ctypes.c_int,                      # dim1
    ctypes.c_int,                      # dim2
    ctypes.c_int,                      # dim3
    ctypes.POINTER(ctypes.c_double),  # knot_vector
    ctypes.c_int,                      # knot_vector_size
    ctypes.POINTER(ctypes.c_double),   # x
    ctypes.c_int,                      # size_x
    ctypes.POINTER(ctypes.c_double),  # weights (output)
    ctypes.POINTER(ctypes.c_int),     # interval_index (output)
]
_lib.bspmap_compute_weight.restype = None


# ----- Debug Functions -----
_lib.bspmap_debug_print.argtypes = [ctypes.c_char_p]
_lib.bspmap_debug_print.restype = None


# ==================== Python Wrapper Functions ====================

def get_version() -> str:
    """Get the version of the bspmap library.
    
    Returns:
        str: Version string (e.g., "0.1.0")
    """
    version_bytes = _lib.bspmap_get_version()
    return version_bytes.decode('utf-8')


def deboor_cox(knot_vector: np.ndarray, num_nodes: int, degree: int) -> np.ndarray:
    """Compute B-spline basis functions using the Cox-de Boor recursion formula.
    
    Args:
        knot_vector: List of knot values, with length = num_nodes + degree
        num_nodes: Number of control points
        degree: Degree of the B-spline
    
    Returns:
        np.ndarray: 2D array of basis function values with shape (intervals, pt_index, degree)
    """
    # Convert input to ctypes arrays
    knot_vector_size = len(knot_vector)
    knot_ptr = knot_vector.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    
    # Prepare output buffers
    # Tensor size: [interval_size, num_control_points_interval, degree + 1]
    # where interval_size = num_nodes + degree - 1
    interval_size = num_nodes + degree

    result_array = np.zeros((interval_size, degree + 1, degree + 1), dtype=np.float64)
    
    result_array_ptr = result_array.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    
    # Call C function
    _lib.bspmap_deboor_cox(
        knot_ptr,
        knot_vector_size,
        num_nodes,
        degree,
        result_array_ptr
    )

    return result_array[degree:interval_size-degree]


def basis_derivative(basis: np.ndarray) -> np.ndarray:
    """Compute derivatives of B-spline basis functions.
    
    Args:
        basis: 3D numpy array of basis function values with shape (num_intervals, num_control_points, degree+1)
    
    Returns:
        np.ndarray: 3D array of basis function derivatives with shape (num_intervals, num_control_points, degree)
    """
    # Get dimensions from basis array
    if basis.ndim != 3:
        raise ValueError(f"basis must be a 3D array, got {basis.ndim}D")
    
    dim1, dim2, dim3 = basis.shape
    
    # Convert basis to contiguous C array
    basis_flat = np.ascontiguousarray(basis.flatten(), dtype=np.float64)
    basis_ptr = basis_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    
    # Prepare output buffer (derivative has one less degree dimension)
    result_array = np.zeros((dim1, dim2, dim3), dtype=np.float64)
    result_ptr = result_array.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    
    # Call C function
    _lib.bspmap_basis_derivative(
        basis_ptr,
        dim1,
        dim2,
        dim3,
        result_ptr
    )
    
    return result_array


def find_interval(knot_vector: np.ndarray, degree: int, x: np.ndarray) -> int:
    """Find the interval index for a given parameter value x.
    
    Args:
        knot_vector: List of knot values
        degree: Degree of the B-spline
        x: Parameter value to find interval for
    
    Returns:
        int: Interval index, or -1 if x is outside the valid range
    """
    # Convert input to ctypes arrays
    knot_vector_size = len(knot_vector)
    knot_ptr = knot_vector.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

    # Convert x to ctypes array
    size_x = len(x)
    x_ptr = x.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    
    # Prepare output buffer
    interval_index = np.zeros(size_x, dtype=np.int32)
    interval_index_ptr = interval_index.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    
    # Call C function
    _lib.bspmap_find_interval(
        knot_ptr,
        knot_vector_size,
        degree,
        x_ptr,
        size_x,
        interval_index_ptr
    )
    
    return interval_index


def compute_weight(basis: np.ndarray, knot_vector: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute weights for control points at a given parameter value.
    
    Args:
        basis: 3D numpy array of basis function coefficients with shape (num_intervals, num_control_points, degree+1)
        knot_vector: List of knot values (currently unused, kept for future compatibility)
        x: Parameter value to evaluate at (as 1D array)
    
    Returns:
        tuple[np.ndarray, np.ndarray]: Weights and indices tensors.
    """
    # Get dimensions from basis array
    if basis.ndim != 3:
        raise ValueError(f"basis must be a 3D array, got {basis.ndim}D")
    
    dim1, dim2, dim3 = basis.shape
    
    # Convert basis to contiguous C array
    basis_flat = np.ascontiguousarray(basis.flatten(), dtype=np.float64)
    basis_ptr = basis_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    
    # Convert knot_vector to ctypes array
    knot_vector_size = len(knot_vector)
    knot_ptr = knot_vector.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

    # Convert x to ctypes array
    size_x = len(x)
    x_ptr = x.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    
    # Prepare output buffer
    weights = np.zeros((size_x, dim2), dtype=np.float64)
    weights_ptr = weights.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

    # Prepare interval_index output buffer (not used here, but required by C API)
    interval_index = np.zeros(size_x, dtype=np.int32)
    interval_index_ptr = interval_index.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    
    # Call C function
    _lib.bspmap_compute_weight(
        basis_ptr,
        dim1,
        dim2,
        dim3,
        knot_ptr,
        knot_vector_size,
        x_ptr,
        size_x,
        weights_ptr,
        interval_index_ptr
    )
    
    return weights, interval_index


def debug_print(msg: str) -> None:
    """Print a debug message through the C library.
    
    Args:
        msg: Message to print
    """
    _lib.bspmap_debug_print(msg.encode('utf-8'))


# ==================== Public API ====================

__all__ = [
    'get_version',
    'deboor_cox',
    'basis_derivative',
    'find_interval',
    'compute_weight',
    'debug_print',
]
