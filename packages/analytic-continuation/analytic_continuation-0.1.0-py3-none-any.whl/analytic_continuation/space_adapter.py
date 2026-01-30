"""
Space adapter for transforming between screen and logical (complex plane) coordinates.

The adapter handles:
- Offset (translation)
- Scale (uniform or non-uniform)
- Y-axis flip (screen Y increases downward, logical Y increases upward)
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union
import math

from .types import Point, Spline, SplineExport


@dataclass
class TransformParams:
    """
    Parameters defining the screen-to-logical coordinate transformation.

    Screen space: origin at top-left, Y increases downward, pixel units
    Logical space: complex plane, Y increases upward, mathematical units

    The transform is:
        logical_x = (screen_x - offset_x) / scale_x
        logical_y = (offset_y - screen_y) / scale_y  (note Y flip)

    Or equivalently:
        screen_x = logical_x * scale_x + offset_x
        screen_y = offset_y - logical_y * scale_y
    """
    # Screen coordinates of the logical origin (0, 0)
    offset_x: float = 0.0
    offset_y: float = 0.0

    # Pixels per logical unit (scale factors)
    scale_x: float = 1.0
    scale_y: Optional[float] = None  # If None, use scale_x (uniform scaling)

    @property
    def scale_y_effective(self) -> float:
        """Get the effective Y scale (defaults to scale_x if not set)."""
        return self.scale_y if self.scale_y is not None else self.scale_x

    @property
    def is_uniform(self) -> bool:
        """Check if scaling is uniform in both axes."""
        return self.scale_y is None or self.scale_x == self.scale_y

    def to_dict(self) -> dict:
        d = {
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "scale_x": self.scale_x,
        }
        if self.scale_y is not None:
            d["scale_y"] = self.scale_y
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TransformParams":
        return cls(
            offset_x=d.get("offset_x", 0.0),
            offset_y=d.get("offset_y", 0.0),
            scale_x=d.get("scale_x", 1.0),
            scale_y=d.get("scale_y"),
        )

    @classmethod
    def from_view_bounds(
        cls,
        screen_width: float,
        screen_height: float,
        logical_x_range: Tuple[float, float],
        logical_y_range: Tuple[float, float],
        uniform: bool = True,
    ) -> "TransformParams":
        """
        Create transform params from screen dimensions and logical view bounds.

        Parameters
        ----------
        screen_width, screen_height : float
            Screen dimensions in pixels
        logical_x_range : tuple
            (x_min, x_max) in logical coordinates
        logical_y_range : tuple
            (y_min, y_max) in logical coordinates
        uniform : bool
            If True, use the same scale for both axes (may add margins)

        Returns
        -------
        TransformParams
        """
        x_min, x_max = logical_x_range
        y_min, y_max = logical_y_range

        logical_width = x_max - x_min
        logical_height = y_max - y_min

        scale_x = screen_width / logical_width
        scale_y = screen_height / logical_height

        if uniform:
            # Use the smaller scale to fit everything, center the view
            scale = min(scale_x, scale_y)
            scale_x = scale_y = scale

            # Compute offset to center the view
            actual_logical_width = screen_width / scale
            actual_logical_height = screen_height / scale
            x_margin = (actual_logical_width - logical_width) / 2
            y_margin = (actual_logical_height - logical_height) / 2

            offset_x = -((x_min - x_margin) * scale)
            offset_y = (y_max + y_margin) * scale
        else:
            offset_x = -(x_min * scale_x)
            offset_y = y_max * scale_y

        return cls(
            offset_x=offset_x,
            offset_y=offset_y,
            scale_x=scale_x,
            scale_y=None if uniform else scale_y,
        )


class SpaceAdapter:
    """
    Transforms coordinates between screen space and logical (complex plane) space.

    Screen space:
        - Origin at top-left
        - X increases rightward
        - Y increases downward
        - Units are pixels

    Logical space:
        - Complex plane
        - X is the real axis
        - Y is the imaginary axis (increases upward)
        - Units are mathematical units
    """

    def __init__(self, params: Optional[TransformParams] = None):
        """
        Initialize the space adapter.

        Parameters
        ----------
        params : TransformParams, optional
            Transform parameters. If None, uses identity transform.
        """
        self.params = params or TransformParams()

    @property
    def offset(self) -> Tuple[float, float]:
        """Get the offset as (x, y) tuple."""
        return (self.params.offset_x, self.params.offset_y)

    @property
    def scale(self) -> Tuple[float, float]:
        """Get the scale as (x, y) tuple."""
        return (self.params.scale_x, self.params.scale_y_effective)

    def screen_to_logical(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """
        Transform a point from screen space to logical space.

        Parameters
        ----------
        screen_x, screen_y : float
            Screen coordinates

        Returns
        -------
        tuple
            (logical_x, logical_y)
        """
        p = self.params
        logical_x = (screen_x - p.offset_x) / p.scale_x
        logical_y = (p.offset_y - screen_y) / p.scale_y_effective
        return (logical_x, logical_y)

    def logical_to_screen(self, logical_x: float, logical_y: float) -> Tuple[float, float]:
        """
        Transform a point from logical space to screen space.

        Parameters
        ----------
        logical_x, logical_y : float
            Logical coordinates

        Returns
        -------
        tuple
            (screen_x, screen_y)
        """
        p = self.params
        screen_x = logical_x * p.scale_x + p.offset_x
        screen_y = p.offset_y - logical_y * p.scale_y_effective
        return (screen_x, screen_y)

    def screen_to_complex(self, screen_x: float, screen_y: float) -> complex:
        """Transform screen coordinates to a complex number."""
        lx, ly = self.screen_to_logical(screen_x, screen_y)
        return complex(lx, ly)

    def complex_to_screen(self, z: complex) -> Tuple[float, float]:
        """Transform a complex number to screen coordinates."""
        return self.logical_to_screen(z.real, z.imag)

    def transform_point_to_logical(self, point: Point) -> Point:
        """Transform a Point from screen to logical space."""
        lx, ly = self.screen_to_logical(point.x, point.y)
        return Point(x=lx, y=ly, index=point.index)

    def transform_point_to_screen(self, point: Point) -> Point:
        """Transform a Point from logical to screen space."""
        sx, sy = self.logical_to_screen(point.x, point.y)
        return Point(x=sx, y=sy, index=point.index)

    def transform_points_to_logical(self, points: List[Point]) -> List[Point]:
        """Transform a list of points from screen to logical space."""
        return [self.transform_point_to_logical(p) for p in points]

    def transform_points_to_screen(self, points: List[Point]) -> List[Point]:
        """Transform a list of points from logical to screen space."""
        return [self.transform_point_to_screen(p) for p in points]

    def transform_spline_to_logical(self, spline: Spline) -> Spline:
        """Transform a Spline from screen to logical space."""
        return Spline(
            points=self.transform_points_to_logical(spline.points),
            closed=spline.closed,
        )

    def transform_spline_to_screen(self, spline: Spline) -> Spline:
        """Transform a Spline from logical to screen space."""
        return Spline(
            points=self.transform_points_to_screen(spline.points),
            closed=spline.closed,
        )

    def transform_spline_export_to_logical(self, export: SplineExport) -> SplineExport:
        """
        Transform a full SplineExport from screen to logical space.

        Transforms all point arrays (controlPoints, spline, adaptivePolyline).
        Also scales the parameters.minDistance accordingly.
        """
        # Scale minDistance by the average scale factor
        avg_scale = (self.params.scale_x + self.params.scale_y_effective) / 2
        new_min_distance = export.parameters.minDistance / avg_scale

        from .types import SplineParameters
        new_params = SplineParameters(
            tension=export.parameters.tension,
            adaptiveTolerance=export.parameters.adaptiveTolerance,
            minDistance=new_min_distance,
        )

        return SplineExport(
            version=export.version,
            timestamp=export.timestamp,
            closed=export.closed,
            parameters=new_params,
            controlPoints=self.transform_points_to_logical(export.controlPoints),
            spline=self.transform_points_to_logical(export.spline) if export.spline else [],
            adaptivePolyline=self.transform_points_to_logical(export.adaptivePolyline) if export.adaptivePolyline else [],
            stats=export.stats,
        )

    def screen_distance_to_logical(self, screen_distance: float) -> float:
        """
        Convert a distance from screen units to logical units.

        For non-uniform scaling, uses the geometric mean of scale factors.
        """
        if self.params.is_uniform:
            return screen_distance / self.params.scale_x
        else:
            avg_scale = math.sqrt(self.params.scale_x * self.params.scale_y_effective)
            return screen_distance / avg_scale

    def logical_distance_to_screen(self, logical_distance: float) -> float:
        """
        Convert a distance from logical units to screen units.

        For non-uniform scaling, uses the geometric mean of scale factors.
        """
        if self.params.is_uniform:
            return logical_distance * self.params.scale_x
        else:
            avg_scale = math.sqrt(self.params.scale_x * self.params.scale_y_effective)
            return logical_distance * avg_scale

    def with_params(self, **kwargs) -> "SpaceAdapter":
        """
        Create a new SpaceAdapter with modified parameters.

        Parameters
        ----------
        **kwargs
            Parameters to override (offset_x, offset_y, scale_x, scale_y)

        Returns
        -------
        SpaceAdapter
            New adapter with modified parameters
        """
        new_params = TransformParams(
            offset_x=kwargs.get("offset_x", self.params.offset_x),
            offset_y=kwargs.get("offset_y", self.params.offset_y),
            scale_x=kwargs.get("scale_x", self.params.scale_x),
            scale_y=kwargs.get("scale_y", self.params.scale_y),
        )
        return SpaceAdapter(new_params)

    def zoom(self, factor: float, center_screen: Optional[Tuple[float, float]] = None) -> "SpaceAdapter":
        """
        Create a new adapter with zoomed view.

        Parameters
        ----------
        factor : float
            Zoom factor (>1 zooms in, <1 zooms out)
        center_screen : tuple, optional
            Screen coordinates of zoom center. If None, zooms around logical origin.

        Returns
        -------
        SpaceAdapter
        """
        new_scale_x = self.params.scale_x * factor
        new_scale_y = self.params.scale_y_effective * factor if self.params.scale_y is not None else None

        if center_screen is not None:
            # Keep the center point fixed
            cx, cy = center_screen
            # Logical position of center
            lx, ly = self.screen_to_logical(cx, cy)
            # New offset to keep center fixed
            new_offset_x = cx - lx * new_scale_x
            new_offset_y = cy + ly * (new_scale_y or new_scale_x)
        else:
            new_offset_x = self.params.offset_x * factor
            new_offset_y = self.params.offset_y * factor

        return SpaceAdapter(TransformParams(
            offset_x=new_offset_x,
            offset_y=new_offset_y,
            scale_x=new_scale_x,
            scale_y=new_scale_y,
        ))

    def pan(self, delta_screen_x: float, delta_screen_y: float) -> "SpaceAdapter":
        """
        Create a new adapter with panned view.

        Parameters
        ----------
        delta_screen_x, delta_screen_y : float
            Pan amounts in screen pixels

        Returns
        -------
        SpaceAdapter
        """
        return SpaceAdapter(TransformParams(
            offset_x=self.params.offset_x + delta_screen_x,
            offset_y=self.params.offset_y + delta_screen_y,
            scale_x=self.params.scale_x,
            scale_y=self.params.scale_y,
        ))

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.params.to_dict()

    @classmethod
    def from_dict(cls, d: dict) -> "SpaceAdapter":
        """Deserialize from dictionary."""
        return cls(TransformParams.from_dict(d))
