Analytic Continuation
=====================

The continuation module implements the later stages of the analytic continuation pipeline,
including holomorphic checking, inversion, and composition operations.

Pipeline Overview
-----------------

After Laurent map fitting (Stage 3), the pipeline continues with:

- **Stage 4**: Check if the composition is holomorphic on an annulus
- **Stage 5**: Compute the inverse mapping
- **Stage 6**: Compute the composition and continuation grid

Pole Class
----------

.. autoclass:: analytic_continuation.Pole
   :members:
   :special-members: __init__

Represents a pole with location and residue information for analysis.

Holomorphic Checking (Stage 4)
------------------------------

Configuration
~~~~~~~~~~~~~

.. autoclass:: analytic_continuation.HolomorphicCheckConfig
   :members:
   :special-members: __init__

Result
~~~~~~

.. autoclass:: analytic_continuation.HolomorphicCheckResult
   :members:

Main Function
~~~~~~~~~~~~~

.. autofunction:: analytic_continuation.check_f_holomorphic_on_annulus

Example usage:

.. code-block:: python

   from analytic_continuation import (
       check_f_holomorphic_on_annulus,
       HolomorphicCheckConfig,
   )

   config = HolomorphicCheckConfig(
       rho_in=0.5,
       rho_out=2.0,
       theta_samples=1024,
       tolerance=1e-8,
   )

   result = check_f_holomorphic_on_annulus(laurent_map, config)

   if result.ok:
       print("Function is holomorphic on the annulus")
   else:
       print(f"Check failed: {result.failure_reason}")

Inversion (Stage 5)
-------------------

Configuration
~~~~~~~~~~~~~

.. autoclass:: analytic_continuation.InvertConfig
   :members:
   :special-members: __init__

Result
~~~~~~

.. autoclass:: analytic_continuation.InvertResult
   :members:

Main Function
~~~~~~~~~~~~~

.. autofunction:: analytic_continuation.invert_z

Computes the inverse of the Laurent map at a given target point:

.. code-block:: python

   from analytic_continuation import invert_z, InvertConfig

   config = InvertConfig(
       max_iter=100,
       tol=1e-10,
       initial_guess=None,  # Use automatic guess
   )

   result = invert_z(laurent_map, target_z=1.5 + 0.5j, config=config)

   if result.ok:
       print(f"Inverse found: zeta = {result.zeta}")
       print(f"Iterations: {result.iterations}")
   else:
       print(f"Inversion failed: {result.failure_reason}")

Composition (Stage 6)
---------------------

Result
~~~~~~

.. autoclass:: analytic_continuation.CompositionResult
   :members:

Main Functions
~~~~~~~~~~~~~~

.. autofunction:: analytic_continuation.compute_composition

Compute the composition of functions for analytic continuation:

.. code-block:: python

   from analytic_continuation import compute_composition

   result = compute_composition(
       laurent_map=lmap,
       f=lambda z: z**2 + 1,  # The function to continue
       zeta=np.exp(1j * theta),
   )

.. autofunction:: analytic_continuation.compute_continuation_grid

Compute continuation values on a grid:

.. code-block:: python

   import numpy as np
   from analytic_continuation import compute_continuation_grid

   # Define a grid in the zeta plane
   re = np.linspace(-2, 2, 100)
   im = np.linspace(-2, 2, 100)
   zeta_grid = re[:, None] + 1j * im[None, :]

   # Compute continuation
   continuation = compute_continuation_grid(
       laurent_map=lmap,
       f=lambda z: np.sin(z),
       zeta_grid=zeta_grid,
       mask_outside_annulus=True,
   )

Workflow Example
----------------

Complete workflow for analytic continuation:

.. code-block:: python

   from analytic_continuation import (
       fit_laurent_map,
       check_f_holomorphic_on_annulus,
       invert_z,
       compute_continuation_grid,
       SplineExport,
       LaurentFitConfig,
       HolomorphicCheckConfig,
   )
   import numpy as np

   # Stage 3: Fit Laurent map
   export = SplineExport.from_json(curve_json)
   fit_result = fit_laurent_map(export)

   if not fit_result.ok:
       raise ValueError(f"Fitting failed: {fit_result.failure_reason}")

   lmap = fit_result.laurent_map

   # Stage 4: Check holomorphic
   check_config = HolomorphicCheckConfig(rho_in=0.5, rho_out=2.0)
   check_result = check_f_holomorphic_on_annulus(lmap, check_config)

   if not check_result.ok:
       raise ValueError(f"Holomorphic check failed: {check_result.failure_reason}")

   # Stage 6: Compute continuation grid
   re = np.linspace(-3, 3, 200)
   im = np.linspace(-3, 3, 200)
   zeta_grid = re[:, None] + 1j * im[None, :]

   continuation = compute_continuation_grid(
       laurent_map=lmap,
       f=lambda z: 1 / (z**2 + 1),
       zeta_grid=zeta_grid,
   )

   # The result can be visualized using domain coloring
