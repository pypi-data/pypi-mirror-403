analytic-continuation Documentation
====================================

A Python package for coordinate transforms, Laurent series fitting, and analytic
continuation pipeline utilities for complex analysis visualizations.

Overview
--------

This package provides tools for working with complex analysis, including:

- **Coordinate Transforms**: Transform between screen space and logical (complex plane)
  coordinates with the :class:`~analytic_continuation.SpaceAdapter` class
- **Laurent Series Fitting**: Fit Laurent maps to Jordan curves, mapping the unit circle
  to approximate curve boundaries
- **Meromorphic Function Construction**: Build meromorphic functions from zeros and poles
- **Analytic Continuation Pipeline**: Utilities for holomorphic checking, inversion, and
  composition operations
- **Intrinsic Curve Analysis**: Analyze curves using Cesaro and Whewell representations
- **Progress Tracking**: Pipeline stage tracking and logging infrastructure

Installation
------------

.. code-block:: bash

   pip install analytic-continuation

For development with all optional dependencies:

.. code-block:: bash

   pip install analytic-continuation[dev]

Quick Start
-----------

SpaceAdapter for Coordinate Transforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

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

Laurent Series Fitting
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytic_continuation import LaurentFitConfig, fit_laurent_map, SplineExport

   # Load curve data and fit a Laurent map
   export = SplineExport.from_json(curve_json)
   config = LaurentFitConfig(N_min=6, N_max=32)
   result = fit_laurent_map(export, config)

   if result.ok:
       # Evaluate on unit circle
       curve_points = result.laurent_map.eval_array(np.exp(1j * thetas))

Meromorphic Function Builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytic_continuation import MeromorphicBuilder

   builder = MeromorphicBuilder()
   builder.add_zero(1, 0).add_zero(-1, 0)
   builder.add_pole(0, 1).add_pole(0, -1)

   expr = builder.build_expression()
   # Returns: "(z-1)*(z+1)/((z-i)*(z+i))"

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   api
   space_adapter
   laurent
   meromorphic
   continuation
   intrinsic_curve
   logging_progress

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
