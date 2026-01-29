# Haversine Distance

A minimal Python package providing a single function to calculate the [Great-circle distance](https://en.wikipedia.org/wiki/Great-circle_distance) distance between two points on the Earth’s surface.

The calculation is implemented in Cython for efficiency, offering faster performance than a pure Python version.

## Features

- **Fast**: Compiled C extension using `libc.math`.
- **Lightweight**: No external runtime dependencies (only requires a C compiler for building).
- **Simple API**: Callable module interface.

## Installation

You need a C compiler installed (GCC, MSVC, or Clang) to build this package.

### From PyPI
```bash
pip install haversine-distance
```

### From Source
You need a C compiler installed (GCC, MSVC, or Clang) to build this package.

```bash
pip install .
```

## Usage

The package is designed to be callable directly as a module.

### Input Arguments
The function expects coordinates in **Degrees**.
> **Note:** The signature follows `(longitude, latitude)` order based on the underlying calculation.

```python
import haversine_distance

# New York (74.0060° W, 40.7128° N)
lon1, lat1 = -74.0060, 40.7128

# London (0.1278° W, 51.5074° N)
lon2, lat2 = -0.1278, 51.5074

# Calculate distance
distance_meters = haversine_distance(lon1, lat1, lon2, lat2)

print(f"Distance: {distance_meters / 1000:.2f} km")
# Output: Distance: 5570.22 km
```

## License

MIT

