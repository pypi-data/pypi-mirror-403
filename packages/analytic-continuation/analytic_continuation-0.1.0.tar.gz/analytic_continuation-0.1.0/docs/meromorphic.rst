Meromorphic Functions
=====================

The meromorphic module provides tools for constructing meromorphic functions from
lists of zeros and poles, generating sympy-compatible mathematical expressions.

Mathematical Background
-----------------------

A meromorphic function is a ratio of holomorphic functions, characterized by its
zeros and poles. Given zeros z_1, ..., z_m with multiplicities n_1, ..., n_m and
poles p_1, ..., p_k with multiplicities m_1, ..., m_k, the function is:

.. math::

   f(z) = C \frac{\prod_{j=1}^{m} (z - z_j)^{n_j}}{\prod_{j=1}^{k} (z - p_j)^{m_j}}

Singularity Class
-----------------

.. autoclass:: analytic_continuation.Singularity
   :members:
   :special-members: __init__

Represents a zero or pole at a specific location with a given multiplicity:

.. code-block:: python

   from analytic_continuation import Singularity

   # Simple zero at z = 1
   zero = Singularity(x=1, y=0)

   # Double pole at z = i
   pole = Singularity(x=0, y=1, multiplicity=2)

   # Convert to complex number
   z = zero.z  # Returns (1+0j)

Building Expressions
--------------------

.. autofunction:: analytic_continuation.build_meromorphic_expression

Direct function for building expressions:

.. code-block:: python

   from analytic_continuation import build_meromorphic_expression, Singularity

   zeros = [
       Singularity(1, 0),    # Zero at z = 1
       Singularity(-1, 0),   # Zero at z = -1
   ]
   poles = [
       Singularity(0, 1),    # Pole at z = i
       Singularity(0, -1),   # Pole at z = -i
   ]

   expr = build_meromorphic_expression(zeros, poles)
   # Returns: "(z-1)*(z+1)/((z-i)*(z+i))"

.. autofunction:: analytic_continuation.meromorphic_from_points

Convenience function using Point objects:

.. code-block:: python

   from analytic_continuation import meromorphic_from_points, Point

   zeros = [Point(x=1, y=0), Point(x=-1, y=0)]
   poles = [Point(x=0, y=1), Point(x=0, y=-1)]

   expr = meromorphic_from_points(zeros, poles)

With multiplicities:

.. code-block:: python

   expr = meromorphic_from_points(
       zeros=zeros,
       poles=poles,
       zero_multiplicities=[1, 2],  # Simple, then double zero
       pole_multiplicities=[1, 1],
   )

MeromorphicBuilder Class
------------------------

.. autoclass:: analytic_continuation.MeromorphicBuilder
   :members:
   :special-members: __init__

Interactive builder for constructing meromorphic functions:

.. code-block:: python

   from analytic_continuation import MeromorphicBuilder

   builder = MeromorphicBuilder()

   # Add zeros and poles (fluent interface)
   builder.add_zero(1, 0).add_zero(-1, 0)
   builder.add_pole(0, 1).add_pole(0, -1)

   # Build the expression
   expr = builder.build_expression()

Adding from Screen Coordinates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The builder integrates with SpaceAdapter for coordinate transforms:

.. code-block:: python

   from analytic_continuation import MeromorphicBuilder, SpaceAdapter, TransformParams

   params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
   adapter = SpaceAdapter(params)

   builder = MeromorphicBuilder()
   builder.add_zero_from_screen(450, 250, adapter)  # Adds zero at (0.5, 0.5)
   builder.add_pole_from_screen(350, 350, adapter)  # Adds pole at (-0.5, -0.5)

Modifying the Builder
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Remove zeros or poles by index
   builder.remove_zero(0)
   builder.remove_pole(1)

   # Clear all
   builder.clear()

Serialization
~~~~~~~~~~~~~

.. code-block:: python

   # Save state
   data = builder.to_dict()

   # Restore state
   restored = MeromorphicBuilder.from_dict(data)

Expression Format
-----------------

The generated expressions are compatible with sympy and use these conventions:

- ``z`` is the complex variable
- ``i`` represents the imaginary unit
- Factors are written as ``(z-a)`` or ``(z+a)`` appropriately
- Multiplicities use exponentiation: ``(z-1)^2``

Examples of generated expressions:

.. code-block:: text

   z                           # Single zero at origin
   (z-1)                       # Single zero at z=1
   (z-1)*(z+1)                 # Zeros at z=1 and z=-1
   z^2/(z-1)                   # Double zero at origin, pole at z=1
   (z-1)*(z+1)/((z-i)*(z+i))   # Complete rational function
