Laurent Series Fitting
======================

The Laurent module implements Stage 3 of the analytic continuation pipeline: fitting
a Laurent series map z(zeta) such that the unit circle maps to approximate a Jordan curve.

Mathematical Background
-----------------------

A Laurent series centered at the origin has the form:

.. math::

   z(\zeta) = a_0 + \sum_{k=1}^{N} a_k \zeta^k + \sum_{k=1}^{N} b_k \zeta^{-k}

When evaluated on the unit circle (|zeta| = 1), this maps to a curve in the complex plane.
The fitting process finds coefficients that best approximate a given Jordan curve.

Configuration
-------------

.. autoclass:: analytic_continuation.LaurentFitConfig
   :members:
   :special-members: __init__

Key configuration parameters:

- **N_min, N_max**: Range of Laurent series degrees to try
- **m_samples**: Number of sample points for fitting
- **lambda_init**: Initial Tikhonov regularization parameter
- **reparam_iters**: Number of reparameterization iterations
- **fit_tol_max_factor**: Maximum error tolerance as fraction of curve diameter

Results
-------

.. autoclass:: analytic_continuation.LaurentMapResult
   :members:
   :special-members: __init__

The result object provides methods for evaluating the Laurent map:

.. code-block:: python

   import numpy as np

   # Evaluate at a single point
   z = result.eval(np.exp(1j * 0.5))

   # Evaluate at multiple points (vectorized)
   thetas = np.linspace(0, 2 * np.pi, 100)
   zetas = np.exp(1j * thetas)
   curve = result.eval_array(zetas)

   # Compute derivative
   dz = result.deriv(np.exp(1j * 0.5))
   dz_array = result.deriv_array(zetas)

.. autoclass:: analytic_continuation.FitResult
   :members:

Main Fitting Function
---------------------

.. autofunction:: analytic_continuation.fit_laurent_map

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from analytic_continuation import fit_laurent_map, LaurentFitConfig, SplineExport

   # Load curve data
   with open("curve.json") as f:
       export = SplineExport.from_json(f.read())

   # Fit with default configuration
   result = fit_laurent_map(export)

   if result.ok:
       print(f"Fitted with N={result.laurent_map.N}")
       print(f"Max error: {result.fit_max_err}")
       print(f"RMS error: {result.fit_rms_err}")
   else:
       print(f"Fitting failed: {result.failure_reason}")

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   config = LaurentFitConfig(
       N_min=8,
       N_max=48,
       m_samples=4096,
       reparam_iters=3,
       fit_tol_max_factor=0.001,  # Tighter tolerance
   )

   result = fit_laurent_map(export, config)

Utility Functions
-----------------

.. autofunction:: analytic_continuation.load_polyline_from_export

.. autofunction:: analytic_continuation.estimate_diameter

Quality Checks
--------------

The fitting process performs several quality checks:

1. **Simplicity**: The mapped curve should not self-intersect
2. **Non-zero derivative**: |z'(zeta)| should be bounded away from zero on the unit circle
3. **Separation**: Points on the mapped curve should be well-separated

These checks are performed on the unit circle and on inner/outer circles (rho_in, rho_out)
to ensure the map is well-behaved on an annulus.
