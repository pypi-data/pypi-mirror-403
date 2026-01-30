Intrinsic Curve Analysis
========================

The intrinsic curve module provides tools for analyzing curves using their intrinsic
representations: the Cesaro form (curvature vs arc length) and Whewell form
(tangent angle vs arc length).

Mathematical Background
-----------------------

Intrinsic representations describe curves independent of their position and orientation:

**Cesaro Form**: Expresses curvature kappa as a function of arc length s:

.. math::

   \kappa = \kappa(s)

**Whewell Form**: Expresses tangent angle phi as a function of arc length s:

.. math::

   \phi = \phi(s)

These representations are related by:

.. math::

   \kappa(s) = \frac{d\phi}{ds}

Representations
---------------

.. autoclass:: analytic_continuation.CesaroRepresentation
   :members:
   :special-members: __init__

.. autoclass:: analytic_continuation.WhewellRepresentation
   :members:
   :special-members: __init__

Computation Functions
---------------------

.. autofunction:: analytic_continuation.compute_cesaro_form

.. autofunction:: analytic_continuation.compute_whewell_form

Example:

.. code-block:: python

   from analytic_continuation import compute_cesaro_form, compute_whewell_form
   import numpy as np

   # Circle parameterized by angle
   t = np.linspace(0, 2 * np.pi, 1000)
   curve = np.exp(1j * t)

   # Compute intrinsic forms
   cesaro = compute_cesaro_form(curve)
   whewell = compute_whewell_form(curve)

   # For a circle, curvature should be constant
   print(f"Curvature range: {cesaro.kappa.min():.3f} to {cesaro.kappa.max():.3f}")

Log Bijection Analysis
----------------------

.. autoclass:: analytic_continuation.LogBijectionData
   :members:

.. autofunction:: analytic_continuation.compute_log_bijection

Analyzes the logarithmic structure of a bijection between curves.

Complexity Estimation
---------------------

.. autoclass:: analytic_continuation.ComplexityEstimates
   :members:

.. autofunction:: analytic_continuation.estimate_complexity

Estimates the complexity of a curve for determining fitting parameters:

.. code-block:: python

   from analytic_continuation import estimate_complexity

   estimates = estimate_complexity(curve_points)

   print(f"Suggested N_min: {estimates.suggested_N_min}")
   print(f"Suggested N_max: {estimates.suggested_N_max}")
   print(f"Winding number: {estimates.winding_number}")

Inversion Configuration
-----------------------

.. autofunction:: analytic_continuation.suggest_inversion_config

Suggests configuration parameters based on curve analysis:

.. code-block:: python

   from analytic_continuation import suggest_inversion_config

   config = suggest_inversion_config(curve_points)

   print(f"Suggested tolerance: {config.tol}")
   print(f"Suggested max iterations: {config.max_iter}")

Complete Analysis
-----------------

.. autoclass:: analytic_continuation.IntrinsicCurveAnalysis
   :members:

.. autofunction:: analytic_continuation.analyze_bijection

Performs complete intrinsic curve analysis:

.. code-block:: python

   from analytic_continuation import analyze_bijection
   import numpy as np

   # Source and target curves
   source = np.exp(1j * np.linspace(0, 2 * np.pi, 1000))
   target = 2 * np.exp(1j * np.linspace(0, 2 * np.pi, 1000))

   analysis = analyze_bijection(source, target)

   print(f"Source total arc length: {analysis.source_cesaro.total_arc_length}")
   print(f"Target total arc length: {analysis.target_cesaro.total_arc_length}")

Contour Pre-check (Stage 1)
---------------------------

.. autoclass:: analytic_continuation.ContourPreCheckResult
   :members:

.. autofunction:: analytic_continuation.precheck_contour

Quick validation before proceeding with full analysis:

.. code-block:: python

   from analytic_continuation import precheck_contour

   result = precheck_contour(curve_points)

   if result.ok:
       print("Contour is suitable for analysis")
   else:
       print(f"Pre-check failed: {result.failure_reason}")
       print(f"Winding number: {result.winding_number}")

.. autofunction:: analytic_continuation.precheck_contour_from_spline_export

Convenience function for SplineExport data:

.. code-block:: python

   from analytic_continuation import precheck_contour_from_spline_export, SplineExport

   export = SplineExport.from_json(json_data)
   result = precheck_contour_from_spline_export(export)

Workflow Integration
--------------------

The intrinsic curve analysis is typically used in the early stages of the pipeline:

.. code-block:: python

   from analytic_continuation import (
       precheck_contour,
       estimate_complexity,
       suggest_inversion_config,
       LaurentFitConfig,
       fit_laurent_map,
   )

   # Stage 1: Quick pre-check
   precheck = precheck_contour(curve_points)
   if not precheck.ok:
       raise ValueError(f"Contour failed pre-check: {precheck.failure_reason}")

   # Stage 2: Analyze complexity
   complexity = estimate_complexity(curve_points)

   # Configure fitting based on analysis
   fit_config = LaurentFitConfig(
       N_min=complexity.suggested_N_min,
       N_max=complexity.suggested_N_max,
   )

   # Stage 3: Fit Laurent map
   result = fit_laurent_map(export, fit_config)
