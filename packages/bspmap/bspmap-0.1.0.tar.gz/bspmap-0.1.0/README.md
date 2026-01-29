# bspmap - B-spline Library

A high-performance B-spline library with C++ backend and Python bindings via ctypes.

## Features

- Fast C++ implementation for B-spline computations
- Easy-to-use Python interface via ctypes
- Cross-platform support (Windows, Linux, macOS)
- Dynamic library (DLL/SO) for easy integration
- No compilation needed for Python package (pure Python wrapper)
- Comprehensive test suite

## Project Structure

```
bspmap/
├── CMakeLists.txt              # Root CMake configuration
├── pyproject.toml              # Python package configuration
├── MANIFEST.in                 # Package manifest for Python distribution
├── copy_dll.py                 # Script to copy DLL for Python package
├── README.md                   # This file
├── src/
│   └── bspmap/                 # C++ library source
│       ├── CMakeLists.txt      # C++ library CMake configuration
│       ├── include/            # Public headers
│       │   ├── basisfunc.h
│       │   ├── bspmap.h
│       │   └── tensor.h
│       └── src/                # Implementation files
│           ├── basisfunc.cpp
│           ├── bspmap.cpp
│           └── tensor.cpp
├── python/
│   └── bspmap/                 # Python package (ctypes wrapper)
│       ├── __init__.py
│       ├── bsp.py
│       ├── capi.py
│       └── bin/                # Binary files directory
├── cmake/
│   └── bspmapConfig.cmake.in  # CMake package config template
├── docs/                       # Documentation
├── tests/                      # Test files
│   ├── test_bspmap.py
│   └── test_debug_cpp.py
└── build/                      # Build output (generated)
    ├── bin/                   # Executables and DLLs
    ├── lib/                   # Libraries
    └── CMakeFiles/            # CMake build files
```

## Prerequisites

- CMake 3.16 or higher
- C++ compiler (GCC, Clang, MSVC)
- Python 3.8 or higher
- uv (recommended for Python package management) or pip

## Building

### 1. Build C++ Library

```bash
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

This will create `bspmap.dll` (Windows) or `libbspmap.so` (Linux/macOS) in `build/bin/` or `build/lib/`.

#### CMake Options

- `CMAKE_BUILD_TYPE`: Build type (Debug, Release, etc.)
- `BUILD_SHARED_LIBS`: Build as shared library (default: ON)
- `BUILD_TESTS`: Build C++ tests (default: OFF)

### 2. Install Python Package

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

The Python package will automatically find the DLL from the build directory during development.

## Usage

### Python

```python
import bspmap

# Example usage (assuming the library provides these functions)
# Note: Update with actual API once implemented

# Get version
print(bspmap.get_version())

# Create a B-spline curve
# curve = bspmap.BSplineCurve(control_points, knots)
# result = curve.evaluate(t)
```

### C++

```cpp
#include <bspmap/bspmap.h>

// Example usage (assuming the library provides these classes)
// Note: Update with actual API once implemented

// Create a B-spline curve
// BSplineCurve curve(control_points, knots);
// double result = curve.evaluate(t);
```

## Testing

Run the Python tests:

```bash
python -m pytest tests/
```

Or run specific test files:

```bash
python tests/test_bspmap.py
```

## Development

### Setting up Development Environment

```bash
# Clone or navigate to the project directory
cd bspmap

# Build C++ library
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build . --config Debug
cd ..

# Create virtual environment and install in editable mode
uv venv
# On Windows:
.venv\Scripts\activate
# On Unix:
source .venv/bin/activate

uv pip install -e .
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Specify your license here, e.g., MIT, BSD, etc.]

## Contact

[Add contact information or issue tracker link]
# source .venv/bin/activate  # Linux/Mac

uv pip install -e ".[dev]"

# Run tests
pytest

# Format code (MSVC, GCC, Clang)
- Python >= 3.8 (for Python package)
- No additional dependencies for Python (uses standard library ctypes
```

## Python ctypes Wrapper Example

The Python package uses ctypes to call the C++ DLL. To add new functions:

1. **In C++ header** (`src/bspmap/include/bspmap/bspmap.h`):
```cpp
BSPMAP_API double evaluate_curve(const double* knots, int n_knots, double t);
```

2. **In Python wrapper** (`python/bspmap/__init__.py`):
```python
# Declare function signature
_lib.evaluate_curve.argtypes = [
    ctypes.POINTER(ctypes.c_double),  # knots
    ctypes.c_int,                      # n_knots
    ctypes.c_double                    # t
]
_lib.evaluate_curve.restype = ctypes.c_double

# Create Python wrapper
def evaluate_curve(knots: list[float], t: float) -> float:
    """Evaluate B-spline curve at parameter t"""
    knots_arr = (ctypes.c_double * len(knots))(*knots)
    return _lib.evaluate_curve(knots_arr, len(knots), t)
black python/
ruff check python/
```

## Requirements

- CMake >= 3.15
- C++17 compatible compiler
- Python >= 3.8 (for Python bindings)
- pybind11 >= 2.11.0 (automatically fetched if not found)

## License

MIT License
