Space Adapter
=============

The space adapter module provides utilities for transforming between screen space
and logical (complex plane) coordinates. This is essential for complex analysis
visualizations where mouse coordinates need to be converted to mathematical coordinates.

Overview
--------

Screen space and logical space differ in several ways:

- **Screen space**: Origin at top-left, Y increases downward, units are pixels
- **Logical space**: Complex plane, Y increases upward, units are mathematical

The :class:`~analytic_continuation.SpaceAdapter` handles these differences transparently.

TransformParams
---------------

.. autoclass:: analytic_continuation.TransformParams
   :members:
   :special-members: __init__

The transform is defined by:

- **offset**: Screen coordinates of the logical origin (0, 0)
- **scale**: Pixels per logical unit

The mathematical relationship is:

.. code-block:: text

   logical_x = (screen_x - offset_x) / scale_x
   logical_y = (offset_y - screen_y) / scale_y   # Note Y flip

Creating from View Bounds
~~~~~~~~~~~~~~~~~~~~~~~~~

A common use case is creating transform parameters from desired view bounds:

.. code-block:: python

   params = TransformParams.from_view_bounds(
       screen_width=800,
       screen_height=600,
       logical_x_range=(-2, 2),
       logical_y_range=(-1.5, 1.5),
       uniform=True,  # Preserve aspect ratio
   )

SpaceAdapter
------------

.. autoclass:: analytic_continuation.SpaceAdapter
   :members:
   :special-members: __init__

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from analytic_continuation import SpaceAdapter, TransformParams

   # Create adapter with default parameters (identity transform)
   adapter = SpaceAdapter()

   # Or with custom parameters
   params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
   adapter = SpaceAdapter(params)

   # Transform coordinates
   lx, ly = adapter.screen_to_logical(450, 250)  # (0.5, 0.5)
   sx, sy = adapter.logical_to_screen(0.5, 0.5)  # (450, 250)

Working with Complex Numbers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Direct conversion to/from complex numbers
   z = adapter.screen_to_complex(500, 200)
   screen_coords = adapter.complex_to_screen(1 + 2j)

Transforming Points and Splines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from analytic_continuation import Point, Spline

   # Transform individual points
   screen_point = Point(x=400, y=300)
   logical_point = adapter.transform_point_to_logical(screen_point)

   # Transform entire splines
   screen_spline = Spline(points=[Point(0, 0), Point(100, 100)], closed=True)
   logical_spline = adapter.transform_spline_to_logical(screen_spline)

Zoom and Pan
~~~~~~~~~~~~

.. code-block:: python

   # Zoom in by 2x around center of screen
   zoomed = adapter.zoom(factor=2.0, center_screen=(400, 300))

   # Pan by 50 pixels right and 30 pixels down
   panned = adapter.pan(delta_screen_x=50, delta_screen_y=30)

Distance Conversion
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Convert screen distance to logical distance
   logical_dist = adapter.screen_distance_to_logical(100)  # 100 pixels

   # Convert logical distance to screen distance
   screen_dist = adapter.logical_distance_to_screen(1.0)  # 1 unit
