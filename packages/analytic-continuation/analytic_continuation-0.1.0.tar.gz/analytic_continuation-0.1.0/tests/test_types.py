"""Tests for type definitions."""

import pytest
import json
from analytic_continuation.types import (
    Point,
    Spline,
    SplineParameters,
    SplineExport,
    Complex,
    LaurentMap,
)


class TestPoint:
    """Test Point dataclass."""

    def test_basic_creation(self):
        """Create a basic point."""
        p = Point(x=1.5, y=2.5)
        assert p.x == 1.5
        assert p.y == 2.5
        assert p.index is None

    def test_with_index(self):
        """Create point with index."""
        p = Point(x=1, y=2, index=5)
        assert p.index == 5

    def test_to_complex(self):
        """Convert to complex number."""
        p = Point(x=3, y=4)
        assert p.to_complex() == 3 + 4j

    def test_from_complex(self):
        """Create from complex number."""
        p = Point.from_complex(1 + 2j, index=3)
        assert p.x == 1
        assert p.y == 2
        assert p.index == 3

    def test_to_dict(self):
        """Serialize to dict."""
        p = Point(x=1, y=2, index=3)
        d = p.to_dict()
        assert d == {"x": 1, "y": 2, "index": 3}

    def test_to_dict_no_index(self):
        """Serialize without index."""
        p = Point(x=1, y=2)
        d = p.to_dict()
        assert "index" not in d

    def test_from_dict(self):
        """Deserialize from dict."""
        d = {"x": 1.5, "y": 2.5, "index": 10}
        p = Point.from_dict(d)
        assert p.x == 1.5
        assert p.y == 2.5
        assert p.index == 10


class TestSpline:
    """Test Spline dataclass."""

    def test_basic_creation(self):
        """Create a basic spline."""
        points = [Point(x=0, y=0), Point(x=1, y=1)]
        s = Spline(points=points)
        assert len(s.points) == 2
        assert s.closed is False

    def test_closed_spline(self):
        """Create a closed spline."""
        points = [Point(x=0, y=0), Point(x=1, y=0), Point(x=0.5, y=1)]
        s = Spline(points=points, closed=True)
        assert s.closed is True

    def test_to_dict(self):
        """Serialize to dict."""
        points = [Point(x=0, y=0, index=0), Point(x=1, y=1, index=1)]
        s = Spline(points=points, closed=True)
        d = s.to_dict()

        assert d["closed"] is True
        assert len(d["points"]) == 2
        assert d["points"][0] == {"x": 0, "y": 0, "index": 0}

    def test_from_dict(self):
        """Deserialize from dict."""
        d = {
            "points": [{"x": 0, "y": 0}, {"x": 1, "y": 1}],
            "closed": True,
        }
        s = Spline.from_dict(d)
        assert len(s.points) == 2
        assert s.closed is True


class TestSplineParameters:
    """Test SplineParameters dataclass."""

    def test_defaults(self):
        """Check default values."""
        p = SplineParameters()
        assert p.tension == 0.5
        assert p.adaptiveTolerance == 3.0
        assert p.minDistance == 15.0

    def test_custom_values(self):
        """Custom parameter values."""
        p = SplineParameters(tension=0.8, adaptiveTolerance=5.0, minDistance=20.0)
        assert p.tension == 0.8
        assert p.adaptiveTolerance == 5.0
        assert p.minDistance == 20.0

    def test_roundtrip(self):
        """Serialize and deserialize."""
        p = SplineParameters(tension=0.3, minDistance=10.0)
        d = p.to_dict()
        p2 = SplineParameters.from_dict(d)
        assert p.tension == p2.tension
        assert p.minDistance == p2.minDistance


class TestSplineExport:
    """Test SplineExport dataclass."""

    @pytest.fixture
    def sample_export(self):
        """Create a sample export for testing."""
        return SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(tension=0.5, minDistance=15.0),
            controlPoints=[
                Point(x=0, y=0, index=0),
                Point(x=100, y=0, index=1),
                Point(x=50, y=100, index=2),
            ],
            spline=[
                Point(x=0, y=0, index=0),
                Point(x=50, y=25, index=1),
                Point(x=100, y=0, index=2),
            ],
        )

    def test_get_polyline_default(self, sample_export):
        """get_polyline defaults to adaptive, falls back to spline."""
        # No adaptivePolyline, should fall back to spline
        polyline = sample_export.get_polyline()
        assert len(polyline) == 3

    def test_get_polyline_control(self, sample_export):
        """get_polyline with prefer='control'."""
        polyline = sample_export.get_polyline(prefer="control")
        assert len(polyline) == 3
        assert polyline[0].x == 0

    def test_to_dict(self, sample_export):
        """Serialize to dict."""
        d = sample_export.to_dict()

        assert d["version"] == "1.0"
        assert d["closed"] is True
        assert len(d["controlPoints"]) == 3
        assert len(d["spline"]) == 3

    def test_from_dict(self, sample_export):
        """Deserialize from dict."""
        d = sample_export.to_dict()
        restored = SplineExport.from_dict(d)

        assert restored.version == sample_export.version
        assert restored.closed == sample_export.closed
        assert len(restored.controlPoints) == len(sample_export.controlPoints)

    def test_json_roundtrip(self, sample_export):
        """JSON serialization roundtrip."""
        json_str = sample_export.to_json()
        restored = SplineExport.from_json(json_str)

        assert restored.version == sample_export.version
        assert restored.timestamp == sample_export.timestamp

    def test_from_sample_file(self):
        """Parse the sample spline export file."""
        import os
        sample_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "laurent_pipeline_bundle",
            "examples",
            "spline_export.sample.json",
        )

        if os.path.exists(sample_path):
            with open(sample_path) as f:
                data = json.load(f)
            export = SplineExport.from_dict(data)

            assert export.version == "1.0"
            assert export.closed is True
            assert len(export.controlPoints) > 0


class TestComplex:
    """Test Complex dataclass (schema representation)."""

    def test_to_complex(self):
        """Convert to Python complex."""
        c = Complex(re=3, im=4)
        assert c.to_complex() == 3 + 4j

    def test_from_complex(self):
        """Create from Python complex."""
        c = Complex.from_complex(1 + 2j)
        assert c.re == 1
        assert c.im == 2

    def test_to_dict(self):
        """Serialize to dict."""
        c = Complex(re=1.5, im=2.5)
        assert c.to_dict() == {"re": 1.5, "im": 2.5}

    def test_from_dict(self):
        """Deserialize from dict."""
        c = Complex.from_dict({"re": 3, "im": 4})
        assert c.re == 3
        assert c.im == 4


class TestLaurentMap:
    """Test LaurentMap dataclass."""

    def test_basic_creation(self):
        """Create a basic Laurent map."""
        lm = LaurentMap(
            N=2,
            a0=Complex(re=0, im=0),
            a=[Complex(re=1, im=0), Complex(re=0, im=0)],
            b=[Complex(re=0, im=0), Complex(re=0, im=0)],
        )
        assert lm.N == 2
        assert len(lm.a) == 2
        assert len(lm.b) == 2

    def test_to_dict(self):
        """Serialize to dict."""
        lm = LaurentMap(
            N=1,
            a0=Complex(re=1, im=0),
            a=[Complex(re=2, im=1)],
            b=[Complex(re=0, im=1)],
        )
        d = lm.to_dict()

        assert d["N"] == 1
        assert d["a0"] == {"re": 1, "im": 0}
        assert d["a"] == [{"re": 2, "im": 1}]

    def test_from_dict(self):
        """Deserialize from dict."""
        d = {
            "N": 1,
            "a0": {"re": 0, "im": 0},
            "a": [{"re": 1, "im": 0}],
            "b": [{"re": 0, "im": 1}],
        }
        lm = LaurentMap.from_dict(d)

        assert lm.N == 1
        assert lm.a0.to_complex() == 0
        assert lm.a[0].to_complex() == 1
        assert lm.b[0].to_complex() == 1j
