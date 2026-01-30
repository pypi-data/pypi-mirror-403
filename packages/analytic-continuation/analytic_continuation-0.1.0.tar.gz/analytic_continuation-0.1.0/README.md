# analytic-continuation

A Python package for coordinate transforms, Laurent series fitting, and analytic continuation pipeline utilities for complex analysis visualizations.

## Overview

This package provides tools for working with complex analysis, particularly focused on:

- **Coordinate Transforms**: Transform between screen space and logical (complex plane) coordinates with the `SpaceAdapter` class
- **Laurent Series Fitting**: Fit Laurent maps to Jordan curves, mapping the unit circle to approximate curve boundaries
- **Meromorphic Function Construction**: Build meromorphic functions from zeros and poles with proper mathematical expressions
- **Analytic Continuation Pipeline**: Utilities for holomorphic checking, inversion, and composition operations
- **Intrinsic Curve Analysis**: Analyze curves using Cesaro and Whewell representations
- **Progress Tracking**: Pipeline stage tracking and logging infrastructure

## Installation

```bash
pip install analytic-continuation
```

For development:

```bash
pip install analytic-continuation[dev]
```

## Quick Start

### SpaceAdapter for Coordinate Transforms

```python
from analytic_continuation import SpaceAdapter, TransformParams

# Create an adapter for a 800x600 screen viewing [-2, 2] x [-1.5, 1.5]
params = TransformParams.from_view_bounds(
    screen_width=800,
    screen_height=600,
    logical_x_range=(-2, 2),
    logical_y_range=(-1.5, 1.5),
)
adapter = SpaceAdapter(params)

# Convert screen coordinates to complex numbers
z = adapter.screen_to_complex(400, 300)  # Returns 0+0j (center)

# Convert complex numbers to screen coordinates
screen_x, screen_y = adapter.complex_to_screen(1 + 1j)
```

### Laurent Series Fitting

```python
from analytic_continuation import (
    LaurentFitConfig,
    fit_laurent_map,
    SplineExport,
)

# Load curve data from a SplineExport
with open("curve.json") as f:
    export = SplineExport.from_json(f.read())

# Fit a Laurent map
config = LaurentFitConfig(N_min=6, N_max=32)
result = fit_laurent_map(export, config)

if result.ok:
    # Evaluate the map at points on the unit circle
    import numpy as np
    thetas = np.linspace(0, 2 * np.pi, 100)
    zetas = np.exp(1j * thetas)
    curve_points = result.laurent_map.eval_array(zetas)
```

### Meromorphic Function Builder

```python
from analytic_continuation import MeromorphicBuilder, Singularity

# Build a meromorphic function with zeros and poles
builder = MeromorphicBuilder()
builder.add_zero(1, 0)   # Zero at z = 1
builder.add_zero(-1, 0)  # Zero at z = -1
builder.add_pole(0, 1)   # Pole at z = i
builder.add_pole(0, -1)  # Pole at z = -i

expr = builder.build_expression()
# Returns: "(z-1)*(z+1)/((z-i)*(z+i))"
```

### Analytic Continuation Pipeline

```python
from analytic_continuation import (
    check_f_holomorphic_on_annulus,
    invert_z,
    compute_composition,
    HolomorphicCheckConfig,
    InvertConfig,
)

# Check if a function is holomorphic on an annulus
config = HolomorphicCheckConfig(rho_in=0.5, rho_out=2.0)
result = check_f_holomorphic_on_annulus(laurent_map, config)

# Compute the inverse map
invert_cfg = InvertConfig(max_iter=100, tol=1e-10)
inv_result = invert_z(laurent_map, target_z, invert_cfg)
```

## Core Components

### Types Module

- `Point`: 2D point with optional index, convertible to/from complex numbers
- `Spline`: Sequence of points forming a spline or polyline
- `SplineExport`: Full spline export structure matching frontend format
- `LaurentMap`: Laurent series coefficients for serialization
- `Complex`: Serializable complex number representation

### SpaceAdapter Module

- `TransformParams`: Parameters for screen-to-logical coordinate transforms
- `SpaceAdapter`: Main class for coordinate transformations

### Laurent Module

- `LaurentFitConfig`: Configuration for Laurent map fitting
- `LaurentMapResult`: Result of Laurent map evaluation with coefficients
- `FitResult`: Complete fitting result including quality metrics
- `fit_laurent_map()`: Main entry point for Stage 3 fitting

### Meromorphic Module

- `Singularity`: Zero or pole with location and multiplicity
- `MeromorphicBuilder`: Builder class for constructing meromorphic functions
- `build_meromorphic_expression()`: Build sympy-compatible expressions

### Continuation Module

- `Pole`: Pole location with residue information
- `HolomorphicCheckConfig` / `HolomorphicCheckResult`: Holomorphic checking
- `InvertConfig` / `InvertResult`: Inversion configuration and results
- `CompositionResult`: Composition computation results
- `check_f_holomorphic_on_annulus()`: Check holomorphicity on annulus
- `invert_z()`: Compute inverse mapping
- `compute_composition()`: Compute function compositions
- `compute_continuation_grid()`: Compute continuation on a grid

### Intrinsic Curve Module

- `CesaroRepresentation`: Cesaro (curvature vs arc length) form
- `WhewellRepresentation`: Whewell (tangent angle vs arc length) form
- `IntrinsicCurveAnalysis`: Complete intrinsic curve analysis
- `analyze_bijection()`: Analyze a bijection between curves
- `precheck_contour()`: Quick pre-check for raw contours (Stage 1 gate)

### Logging and Progress

- `PipelineLogger`: Structured logging for pipeline stages
- `ProgressTracker`: Track progress through pipeline stages
- `TaskStatus` / `TaskProgress`: Task status tracking
- `format_cli_progress()`: Format progress for CLI display

## Pipeline Stages

The package implements utilities for a multi-stage analytic continuation pipeline:

1. **Stage 1**: Contour pre-check and validation
2. **Stage 2**: Intrinsic curve analysis (Cesaro/Whewell forms)
3. **Stage 3**: Laurent map fitting (main fitting stage)
4. **Stage 4**: Holomorphic checking on annulus
5. **Stage 5**: Inversion computation
6. **Stage 6**: Composition and continuation grid computation

## Development

### Running Tests

```bash
pytest tests/
```

### Building Documentation

```bash
cd docs
make html
```

## License

MIT License
