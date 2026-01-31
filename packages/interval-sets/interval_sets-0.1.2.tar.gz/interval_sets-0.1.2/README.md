# Interval Sets Library

[![Tests](https://github.com/yourusername/interval-sets/workflows/Tests/badge.svg)](https://github.com/yourusername/interval-sets/actions)
[![codecov](https://codecov.io/gh/yourusername/interval-sets/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/interval-sets)
[![PyPI version](https://badge.fury.io/py/interval-sets.svg)](https://badge.fury.io/py/interval-sets)
[![Python Versions](https://img.shields.io/pypi/pyversions/interval-sets.svg)](https://pypi.org/project/interval-sets/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python library for performing **set operations** on intervals and points on the real number line. It supports continuous intervals with configurable open/closed boundaries and handles collections of disjoint intervals (sets) with automatic merging.

> **Note:** This library focuses on *set-theoretic* operations (Union, Intersection, Difference) on intervals. It is not designed for strict *interval arithmetic* used for error bounding (e.g., `[a,b] + [c,d]`).

## Features

- 📏 **Continuous Intervals**: Configurable boundaries `(a, b)`, `[a, b]`, `[a, b)`, `(a, b]`.
- 📦 **Interval Sets**: Disjoint collections with automatic merging.
- 🔢 **Set Operations**: Exact Union (`|`), Intersection (`&`), Difference (`-`), and XOR (`^`).
- 🛠️ **Analysis & Topology**: Tools for Convex Hull, Diameter, Boundedness, and Compactness.
- 📐 **Morphology**: Minkowski Sum/Difference, Opening, Closing, and ε-dilation.
- 🔒 **Type Safe**: Comprehensive type hints and runtime validation.
- 🐍 **Pythonic**: Supports standard operators, hashing, and membership testing (`in`).

## Installation

```bash
pip install interval-sets
```

## Quick Start

### Working with Intervals

The `Interval` class represents a single continuous range on the real number line.

```python
from src.intervals import Interval

# Create intervals
closed = Interval(0, 10)                    # [0, 10]
open_int = Interval(0, 10, open_start=True, open_end=True)  # (0, 10)
half_open = Interval(0, 10, open_start=False, open_end=True) # [0, 10)

# Convenient factories
i1 = Interval.closed(0, 5)     # [0, 5]
i2 = Interval.open(5, 10)      # (5, 10)
p  = Interval.point(3)         # [3, 3] (Point)

# Check membership
5 in closed  # True
0 in open_int    # False (open boundary)

# Interval properties
closed.length()  # 10.0
closed.is_empty()  # False
```

### Set Operations on Intervals

You can perform standard set operations on intervals. Operations that result in multiple disjoint intervals will return a `Set` object.

```python
i1 = Interval(0, 10)
i2 = Interval(5, 15)
i3 = Interval(20, 25)

# Union
# Returns a single Interval if they overlap/touch, or a Set if disjoint
u1 = i1.union(i2)  # [0, 15]
u2 = i1.union(i3)  # {[0, 10], [20, 25]} (Set object)

# Intersection
inter = i1.intersection(i2)  # [5, 10]

# Difference
diff = i1.difference(i2)      # [0, 5)
```

### Working with IntervalSets (1D Disjoint Intervals)

The `IntervalSet` class handles collections of 1D intervals and ensures they remain disjoint and normalized (merged).

```python
from src.intervals import IntervalSet, Interval

# Create a set from a list of intervals
# Overlapping [0, 5] and [3, 8] automatically merge to [0, 8]
s = IntervalSet([
    Interval(0, 5),
    Interval(3, 8),
    Interval(10, 15)
])

print(s)  # {[0, 8], [10, 15]}

# Set Arithmetic using Operators
s1 = IntervalSet([Interval(0, 10)])
s2 = IntervalSet([Interval(5, 15)])

# Union (|)
print(s1 | s2)  # [0, 15]
```

## Multi-Dimensional Support

The library supports N-dimensional intervals (**Boxes**) and universal sets of boxes (**Sets**).

### The `Box` Class (Hyperrectangle)
A `Box` represents a Cartesian product of intervals: $B = I_1 \times I_2 \times ... \times I_n$.

```python
from src.multidimensional import Box, Set
from src.intervals import Interval

# Create a 2D Unit Square [0,1]x[0,1]
square = Box([Interval(0, 1), Interval(0, 1)])
print(square.volume()) # 1.0
```

### The `Set` Class (Universal N-D Set)
A `Set` represents a collection of **disjoint** `Box`es. It is the N-dimensional equivalent of `IntervalSet` but supports all dimensions and automatic promotion.

```python
# L-Shape Construction
v_bar = Box([Interval(0, 1), Interval(0, 2)])
h_bar = Box([Interval(0, 2), Interval(0, 1)])

# Union creates a Set
l_shape = Set([v_bar]).union(h_bar)
print(l_shape.volume()) # 3.0

# Promotion: You can mix 1D Intervals into a Set!
# They are automatically treated as 1D Boxes.
s = Set([Interval(0, 5), Interval(10, 15)])
print(s.volume()) # 10.0
```

- **Dimension Safety**: Enforces dimension matching for all operations.

### Topological Analysis & Morphology

```python
# Topological checks
square.is_compact() # True
square.is_open()    # False

# Morphology
dilated = square.dilate_epsilon(0.1) # Expansion by 0.1
eroded = dilated.erode(square) # Morphological erosion

# Analysis
print(l_shape.convex_hull()) # Smallest Box containing the shape
print(l_shape.diameter())    # Maximum distance between points
```


### `Interval`

Represents a continuous interval defined by `start` and `end` points and boundary openness.

**Constructor:**
- `Interval(start, end, *, open_start=False, open_end=False)`

**Factory Methods:**
- `Interval.closed(start, end)`: `[start, end]`
- `Interval.open(start, end)`: `(start, end)`
- `Interval.left_open(start, end)`: `(start, end]`
- `Interval.right_open(start, end)`: `[start, end)`
- `Interval.point(value)`: `[value, value]`
- `Interval.empty()`: `(0, 0)`

**Key Methods:**
- `union(other)`: Returns `Interval` or `Set`
- `intersection(other)`: Returns `Interval` or `Set` (empty)
- `difference(other)`: Returns `Interval` or `Set`
- `overlaps(other)`: Check if intervals overlap
- `is_adjacent(other)`: Check if intervals touch but don't overlap

### `Set`

Represents a collection of disjoint intervals. All set operations (`union`, `intersection`, `difference`) are supported and return normalized `Set` or `Interval` objects.

**Constructor:**
- `Set(elements)`: List of `Interval` objects or nested `Set`s.

**Key Methods:**
- `contains(value)`: Check if a value or interval is contained in the set.
- `measure()`: Total length of all intervals in the set.
- `infimum() / supremum()`: Lower and upper bounds.
- `complement(universe)`: Return the complement of the set within a given universe interval.

### `Point`

A helper class (inheriting from `Interval`) representing a degenerate interval `[x, x]`.

## Mathematical Notes & Design Decisions

- **Set Theory vs Interval Arithmetic:** This library implements strict set-theoretic operations. `[1, 2] + [3, 4]` is treated as a Union operation (if valid in context), not numerical addition of bounds.
- **Normalization:** The `Set` class enforces normalization. You cannot hold `{[0, 5], [2, 7]}` inside a `Set`; it will instantly become `{[0, 7]}`.
- **Empty Set:** An empty set is represented by a `Set` with no intervals, `Set()`. `Interval.empty()` creates a special empty interval `(0, 0)` which acts as the neutral element for union.
- **Boundaries:** We meticulously handle open vs closed boundaries (`<` vs `<=`) during merging and difference operations to ensure mathematical correctness.

## Development

```bash
# Install dependencies
pip install pytest pytest-cov

# Run tests
pytest --cov --cov-report=term-missing tests/
```

## License

MIT License