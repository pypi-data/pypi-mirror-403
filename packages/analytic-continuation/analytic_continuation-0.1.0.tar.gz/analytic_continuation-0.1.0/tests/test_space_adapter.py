"""Tests for SpaceAdapter coordinate transforms."""

import pytest
from analytic_continuation import SpaceAdapter, TransformParams, Point, SplineExport
from analytic_continuation.types import SplineParameters


class TestBasicTransforms:
    """Test basic screen <-> logical coordinate transforms."""

    def test_identity_transform(self):
        """Identity transform should pass through unchanged."""
        adapter = SpaceAdapter(TransformParams())
        assert adapter.screen_to_logical(5, 10) == (5, -10)  # Y flips
        assert adapter.logical_to_screen(5, -10) == (5, 10)

    def test_screen_to_logical_origin(self):
        """Screen origin maps to logical origin with proper offset."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        lx, ly = adapter.screen_to_logical(400, 300)
        assert abs(lx) < 1e-10
        assert abs(ly) < 1e-10

    def test_logical_to_screen_positive_x(self):
        """Logical positive x maps to screen right."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        sx, sy = adapter.logical_to_screen(1, 0)
        assert abs(sx - 500) < 1e-10
        assert abs(sy - 300) < 1e-10

    def test_logical_to_screen_positive_y(self):
        """Logical positive y maps to screen up (lower y value)."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        sx, sy = adapter.logical_to_screen(0, 1)
        assert abs(sx - 400) < 1e-10
        assert abs(sy - 200) < 1e-10  # Y flipped: 300 - 100 = 200

    def test_y_flip(self):
        """Verify Y-axis is properly flipped."""
        params = TransformParams(offset_x=0, offset_y=100, scale_x=1)
        adapter = SpaceAdapter(params)

        # Screen y=0 (top) should be logical y=100
        _, ly = adapter.screen_to_logical(0, 0)
        assert abs(ly - 100) < 1e-10

        # Screen y=100 should be logical y=0
        _, ly = adapter.screen_to_logical(0, 100)
        assert abs(ly) < 1e-10


class TestRoundtrip:
    """Test that transforms are invertible."""

    @pytest.mark.parametrize("sx,sy", [
        (0, 0),
        (100, 200),
        (500, 100),
        (123.5, 456.7),
        (-50, -75),
    ])
    def test_screen_logical_screen(self, sx, sy):
        """screen -> logical -> screen should be identity."""
        params = TransformParams(offset_x=123.5, offset_y=456.7, scale_x=89.2)
        adapter = SpaceAdapter(params)

        lx, ly = adapter.screen_to_logical(sx, sy)
        sx2, sy2 = adapter.logical_to_screen(lx, ly)

        assert abs(sx - sx2) < 1e-10
        assert abs(sy - sy2) < 1e-10

    @pytest.mark.parametrize("lx,ly", [
        (0, 0),
        (1, 1),
        (-2, 3),
        (0.5, -0.5),
    ])
    def test_logical_screen_logical(self, lx, ly):
        """logical -> screen -> logical should be identity."""
        params = TransformParams(offset_x=200, offset_y=300, scale_x=50)
        adapter = SpaceAdapter(params)

        sx, sy = adapter.logical_to_screen(lx, ly)
        lx2, ly2 = adapter.screen_to_logical(sx, sy)

        assert abs(lx - lx2) < 1e-10
        assert abs(ly - ly2) < 1e-10


class TestNonUniformScaling:
    """Test non-uniform X/Y scaling."""

    def test_different_scales(self):
        """Different X and Y scales should work correctly."""
        params = TransformParams(offset_x=0, offset_y=100, scale_x=50, scale_y=100)
        adapter = SpaceAdapter(params)

        # Screen (50, 0) should be logical (1, 1)
        lx, ly = adapter.screen_to_logical(50, 0)
        assert abs(lx - 1) < 1e-10
        assert abs(ly - 1) < 1e-10

    def test_is_uniform_property(self):
        """is_uniform should reflect scaling type."""
        uniform = TransformParams(scale_x=100)
        assert SpaceAdapter(uniform).params.is_uniform

        non_uniform = TransformParams(scale_x=100, scale_y=50)
        assert not SpaceAdapter(non_uniform).params.is_uniform

    def test_scale_y_effective(self):
        """scale_y_effective should default to scale_x."""
        params = TransformParams(scale_x=100)
        assert params.scale_y_effective == 100

        params = TransformParams(scale_x=100, scale_y=50)
        assert params.scale_y_effective == 50


class TestFromViewBounds:
    """Test creating transforms from view bounds."""

    def test_uniform_square(self):
        """Square view with uniform scaling."""
        params = TransformParams.from_view_bounds(
            screen_width=800,
            screen_height=800,
            logical_x_range=(-2, 2),
            logical_y_range=(-2, 2),
            uniform=True,
        )
        adapter = SpaceAdapter(params)

        # Center should map to origin
        lx, ly = adapter.screen_to_logical(400, 400)
        assert abs(lx) < 1e-10
        assert abs(ly) < 1e-10

        # Scale should be 200 px/unit
        assert abs(params.scale_x - 200) < 1e-10

    def test_uniform_rectangular(self):
        """Rectangular view with uniform scaling (should fit)."""
        params = TransformParams.from_view_bounds(
            screen_width=800,
            screen_height=600,
            logical_x_range=(-2, 2),
            logical_y_range=(-1.5, 1.5),
            uniform=True,
        )
        adapter = SpaceAdapter(params)

        # Center should map to origin
        lx, ly = adapter.screen_to_logical(400, 300)
        assert abs(lx) < 1e-10
        assert abs(ly) < 1e-10

    def test_non_uniform(self):
        """Non-uniform scaling stretches to fill."""
        params = TransformParams.from_view_bounds(
            screen_width=800,
            screen_height=400,
            logical_x_range=(-2, 2),
            logical_y_range=(-2, 2),
            uniform=False,
        )

        # Different scales for X and Y
        assert params.scale_x == 200  # 800 / 4
        assert params.scale_y == 100  # 400 / 4


class TestZoomAndPan:
    """Test zoom and pan operations."""

    def test_zoom_doubles_scale(self):
        """Zoom by 2x should double the scale."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        zoomed = adapter.zoom(2.0, center_screen=(400, 300))
        assert abs(zoomed.params.scale_x - 200) < 1e-10

    def test_zoom_preserves_center(self):
        """Zoom should keep center point fixed."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        zoomed = adapter.zoom(2.0, center_screen=(400, 300))

        # After zoom, screen center should still map to logical (0, 0)
        lx, ly = zoomed.screen_to_logical(400, 300)
        assert abs(lx) < 1e-10
        assert abs(ly) < 1e-10

    def test_zoom_preserves_arbitrary_center(self):
        """Zoom around arbitrary point should keep that point fixed."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        # Zoom around (500, 200) which is logical (1, 1)
        center = (500, 200)
        zoomed = adapter.zoom(2.0, center_screen=center)

        # The center point should map to same logical coords
        lx_before, ly_before = adapter.screen_to_logical(*center)
        lx_after, ly_after = zoomed.screen_to_logical(*center)

        assert abs(lx_before - lx_after) < 1e-10
        assert abs(ly_before - ly_after) < 1e-10

    def test_pan_shifts_offset(self):
        """Pan should shift the offset."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        panned = adapter.pan(50, 25)

        assert abs(panned.params.offset_x - 450) < 1e-10
        assert abs(panned.params.offset_y - 325) < 1e-10


class TestComplexConversion:
    """Test complex number conversions."""

    def test_screen_to_complex(self):
        """Screen coordinates to complex number."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        z = adapter.screen_to_complex(500, 200)
        assert abs(z - (1 + 1j)) < 1e-10

    def test_complex_to_screen(self):
        """Complex number to screen coordinates."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        sx, sy = adapter.complex_to_screen(-1 - 1j)
        assert abs(sx - 300) < 1e-10
        assert abs(sy - 400) < 1e-10


class TestPointTransforms:
    """Test Point object transforms."""

    def test_transform_point_to_logical(self):
        """Transform Point object to logical space."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        point = Point(x=500, y=200, index=5)
        result = adapter.transform_point_to_logical(point)

        assert abs(result.x - 1) < 1e-10
        assert abs(result.y - 1) < 1e-10
        assert result.index == 5  # Index preserved

    def test_transform_points_list(self):
        """Transform list of Points."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        points = [
            Point(x=400, y=300, index=0),
            Point(x=500, y=200, index=1),
        ]
        results = adapter.transform_points_to_logical(points)

        assert len(results) == 2
        assert abs(results[0].x) < 1e-10
        assert abs(results[0].y) < 1e-10
        assert abs(results[1].x - 1) < 1e-10
        assert abs(results[1].y - 1) < 1e-10


class TestSplineExportTransform:
    """Test full SplineExport transforms."""

    def test_transform_control_points(self):
        """Control points should be transformed."""
        params = TransformParams(offset_x=300, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        export = SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(tension=0.5, adaptiveTolerance=3.0, minDistance=15.0),
            controlPoints=[
                Point(x=300, y=300, index=0),  # -> (0, 0)
                Point(x=400, y=300, index=1),  # -> (1, 0)
                Point(x=400, y=200, index=2),  # -> (1, 1)
            ],
        )

        transformed = adapter.transform_spline_export_to_logical(export)
        cp = transformed.controlPoints

        assert abs(cp[0].x) < 1e-10 and abs(cp[0].y) < 1e-10
        assert abs(cp[1].x - 1) < 1e-10 and abs(cp[1].y) < 1e-10
        assert abs(cp[2].x - 1) < 1e-10 and abs(cp[2].y - 1) < 1e-10

    def test_min_distance_scaled(self):
        """minDistance parameter should be scaled."""
        params = TransformParams(offset_x=300, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        export = SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(minDistance=15.0),
            controlPoints=[Point(x=0, y=0)],
        )

        transformed = adapter.transform_spline_export_to_logical(export)

        # 15 pixels / 100 px per unit = 0.15 logical units
        assert abs(transformed.parameters.minDistance - 0.15) < 1e-10

    def test_preserves_metadata(self):
        """Metadata like version, timestamp, closed should be preserved."""
        params = TransformParams(scale_x=100)
        adapter = SpaceAdapter(params)

        export = SplineExport(
            version="2.5",
            timestamp="2026-01-22T12:00:00Z",
            closed=False,
            parameters=SplineParameters(),
            controlPoints=[],
        )

        transformed = adapter.transform_spline_export_to_logical(export)

        assert transformed.version == "2.5"
        assert transformed.timestamp == "2026-01-22T12:00:00Z"
        assert transformed.closed is False


class TestDistanceConversion:
    """Test distance unit conversions."""

    def test_screen_to_logical_distance(self):
        """Convert screen distance to logical."""
        params = TransformParams(scale_x=100)
        adapter = SpaceAdapter(params)

        assert adapter.screen_distance_to_logical(100) == 1.0
        assert adapter.screen_distance_to_logical(50) == 0.5

    def test_logical_to_screen_distance(self):
        """Convert logical distance to screen."""
        params = TransformParams(scale_x=100)
        adapter = SpaceAdapter(params)

        assert adapter.logical_distance_to_screen(1.0) == 100
        assert adapter.logical_distance_to_screen(0.5) == 50


class TestSerialization:
    """Test serialization/deserialization."""

    def test_params_to_dict(self):
        """TransformParams serializes correctly."""
        params = TransformParams(offset_x=100, offset_y=200, scale_x=50, scale_y=75)
        d = params.to_dict()

        assert d["offset_x"] == 100
        assert d["offset_y"] == 200
        assert d["scale_x"] == 50
        assert d["scale_y"] == 75

    def test_params_from_dict(self):
        """TransformParams deserializes correctly."""
        d = {"offset_x": 100, "offset_y": 200, "scale_x": 50}
        params = TransformParams.from_dict(d)

        assert params.offset_x == 100
        assert params.offset_y == 200
        assert params.scale_x == 50
        assert params.scale_y is None

    def test_adapter_roundtrip(self):
        """SpaceAdapter serialization roundtrip."""
        original = SpaceAdapter(TransformParams(offset_x=123, offset_y=456, scale_x=78))
        d = original.to_dict()
        restored = SpaceAdapter.from_dict(d)

        assert original.params.offset_x == restored.params.offset_x
        assert original.params.offset_y == restored.params.offset_y
        assert original.params.scale_x == restored.params.scale_x
