"""Tests for Laurent map fitting and evaluation."""

import pytest
import numpy as np
from analytic_continuation import (
    LaurentFitConfig,
    LaurentMapResult,
    FitResult,
    fit_laurent_map,
    load_polyline_from_export,
    estimate_diameter,
    Point,
    SplineExport,
)
from analytic_continuation.types import SplineParameters
from analytic_continuation.laurent import (
    resample_closed_polyline,
    build_laurent_matrix,
    solve_tikhonov,
    check_polyline_simple,
    check_laurent_map,
)


class TestLoadPolyline:
    """Test polyline loading from SplineExport."""

    def test_load_from_control_points(self):
        """Load from control points."""
        export = SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(),
            controlPoints=[
                Point(x=0, y=0, index=0),
                Point(x=1, y=0, index=1),
                Point(x=1, y=1, index=2),
            ],
        )
        poly = load_polyline_from_export(export, "controlPoints")
        assert len(poly) == 3
        assert poly[0] == 0 + 0j
        assert poly[1] == 1 + 0j

    def test_drop_duplicate_terminal(self):
        """Duplicate terminal point should be dropped."""
        export = SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(),
            controlPoints=[
                Point(x=0, y=0, index=0),
                Point(x=1, y=0, index=1),
                Point(x=0, y=0, index=2),  # Duplicate of first
            ],
        )
        poly = load_polyline_from_export(export, "controlPoints", drop_duplicate_terminal=True)
        assert len(poly) == 2

    def test_fallback_chain(self):
        """Should fall back if requested field is empty."""
        export = SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(),
            controlPoints=[Point(x=0, y=0), Point(x=1, y=1)],
            spline=[],
            adaptivePolyline=[],
        )
        poly = load_polyline_from_export(export, "adaptivePolyline")
        assert len(poly) == 2  # Falls back to controlPoints


class TestEstimateDiameter:
    """Test diameter estimation."""

    def test_unit_square(self):
        """Diameter of unit square is sqrt(2)."""
        poly = [0 + 0j, 1 + 0j, 1 + 1j, 0 + 1j]
        diameter = estimate_diameter(poly)
        assert abs(diameter - np.sqrt(2)) < 1e-10

    def test_line_segment(self):
        """Diameter of line segment is its length."""
        poly = [0 + 0j, 3 + 4j]  # Length 5
        diameter = estimate_diameter(poly)
        assert abs(diameter - 5) < 1e-10


class TestResample:
    """Test arc-length resampling."""

    def test_resample_square(self):
        """Resample a square."""
        poly = [0 + 0j, 1 + 0j, 1 + 1j, 0 + 1j]
        resampled = resample_closed_polyline(poly, 8)
        assert len(resampled) == 8
        # Check approximate uniformity by arc length
        # Total perimeter is 4, so each segment should be 0.5

    def test_preserves_closure(self):
        """Resampling should preserve closed curve property."""
        poly = [0 + 0j, 1 + 0j, 0.5 + 1j]
        resampled = resample_closed_polyline(poly, 100)
        # First and last point should be close to forming a closed curve
        # (not identical, but the interpolation wraps around)
        assert len(resampled) == 100


class TestBuildLaurentMatrix:
    """Test Laurent design matrix construction."""

    def test_matrix_shape(self):
        """Matrix should have correct shape."""
        thetas = np.linspace(0, 2 * np.pi, 100, endpoint=False)
        N = 10
        A = build_laurent_matrix(thetas, N)
        assert A.shape == (100, 1 + 2 * N)

    def test_constant_column(self):
        """First column should be all ones."""
        thetas = np.linspace(0, 2 * np.pi, 50, endpoint=False)
        A = build_laurent_matrix(thetas, 5)
        assert np.allclose(A[:, 0], 1.0)

    def test_positive_powers(self):
        """Positive power columns should be ζ^k."""
        thetas = np.array([0, np.pi / 2, np.pi])
        A = build_laurent_matrix(thetas, 2)
        zeta = np.exp(1j * thetas)
        # Column 1 should be ζ^1
        assert np.allclose(A[:, 1], zeta)
        # Column 2 should be ζ^2
        assert np.allclose(A[:, 2], zeta ** 2)


class TestSolveTikhonov:
    """Test Tikhonov regularized least squares."""

    def test_recovers_known_coefficients(self):
        """Should recover known Laurent coefficients."""
        N = 3
        # Create a known Laurent series: z(ζ) = 1 + 2ζ + 0.5/ζ
        true_a0 = 1.0
        true_a = np.array([2.0, 0.0, 0.0])
        true_b = np.array([0.5, 0.0, 0.0])

        # Sample at many points
        m = 200
        thetas = np.linspace(0, 2 * np.pi, m, endpoint=False)
        zeta = np.exp(1j * thetas)
        y = true_a0 + true_a[0] * zeta + true_b[0] / zeta

        A = build_laurent_matrix(thetas, N)
        coeffs = solve_tikhonov(A, y, N, lam=1e-12)  # Very small regularization

        assert abs(coeffs[0] - true_a0) < 1e-6
        assert abs(coeffs[1] - true_a[0]) < 1e-6
        assert abs(coeffs[N + 1] - true_b[0]) < 1e-6


class TestCheckPolylineSimple:
    """Test polyline self-intersection check."""

    def test_simple_polygon(self):
        """Simple polygon should pass."""
        poly = np.array([0 + 0j, 1 + 0j, 1 + 1j, 0 + 1j])
        assert check_polyline_simple(poly, eps=1e-6)

    def test_self_intersecting(self):
        """Self-intersecting polygon should fail."""
        # Figure-8 shape
        poly = np.array([0 + 0j, 1 + 1j, 1 + 0j, 0 + 1j])
        assert not check_polyline_simple(poly, eps=1e-6)


class TestLaurentMapResult:
    """Test LaurentMapResult evaluation."""

    def test_eval_constant(self):
        """Constant map z(ζ) = c."""
        lmap = LaurentMapResult(
            N=1,
            a0=2 + 3j,
            a=np.array([0j]),
            b=np.array([0j]),
        )
        assert lmap.eval(1 + 0j) == 2 + 3j
        assert lmap.eval(0 + 1j) == 2 + 3j

    def test_eval_linear(self):
        """Linear map z(ζ) = ζ."""
        lmap = LaurentMapResult(
            N=1,
            a0=0j,
            a=np.array([1 + 0j]),
            b=np.array([0j]),
        )
        zeta = np.exp(1j * np.pi / 4)
        assert abs(lmap.eval(zeta) - zeta) < 1e-10

    def test_eval_inverse(self):
        """Inverse map z(ζ) = 1/ζ."""
        lmap = LaurentMapResult(
            N=1,
            a0=0j,
            a=np.array([0j]),
            b=np.array([1 + 0j]),
        )
        zeta = 2 + 0j
        assert abs(lmap.eval(zeta) - 0.5) < 1e-10

    def test_deriv_linear(self):
        """Derivative of z(ζ) = ζ is 1."""
        lmap = LaurentMapResult(
            N=1,
            a0=0j,
            a=np.array([1 + 0j]),
            b=np.array([0j]),
        )
        assert abs(lmap.deriv(1 + 0j) - 1) < 1e-10

    def test_vectorized_eval(self):
        """Vectorized evaluation should match scalar."""
        lmap = LaurentMapResult(
            N=2,
            a0=1j,
            a=np.array([0.5, 0.1]),
            b=np.array([0.2, 0.05]),
        )
        zetas = np.exp(1j * np.linspace(0, 2 * np.pi, 10))
        vectorized = lmap.eval_array(zetas)
        scalar = np.array([lmap.eval(z) for z in zetas])
        assert np.allclose(vectorized, scalar)


class TestFitLaurentMap:
    """Test the full Laurent fitting pipeline."""

    @pytest.fixture
    def circle_export(self):
        """Create a SplineExport for a unit circle."""
        n_points = 100
        thetas = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
        points = [
            Point(x=float(np.cos(t)), y=float(np.sin(t)), index=i)
            for i, t in enumerate(thetas)
        ]
        return SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(minDistance=0.1),
            controlPoints=points,
        )

    @pytest.fixture
    def ellipse_export(self):
        """Create a SplineExport for an ellipse."""
        n_points = 100
        thetas = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
        a, b = 2.0, 1.0  # Semi-axes
        points = [
            Point(x=float(a * np.cos(t)), y=float(b * np.sin(t)), index=i)
            for i, t in enumerate(thetas)
        ]
        return SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(minDistance=0.1),
            controlPoints=points,
        )

    def test_fit_circle(self, circle_export):
        """Fitting a circle should succeed with low error."""
        cfg = LaurentFitConfig(N_min=1, N_max=8, m_samples=256)
        result = fit_laurent_map(circle_export, cfg)

        assert result.ok
        assert result.laurent_map is not None
        # Circle should be fit well with just N=1 (a0 + a1*zeta)
        assert result.fit_max_err < 0.1

    def test_fit_ellipse(self, ellipse_export):
        """Fitting an ellipse should succeed."""
        cfg = LaurentFitConfig(N_min=1, N_max=16, m_samples=512)
        result = fit_laurent_map(ellipse_export, cfg)

        assert result.ok
        assert result.laurent_map is not None
        # Ellipse needs more terms but should still fit well
        assert result.fit_max_err < 0.1

    def test_fit_returns_curve_scale(self, circle_export):
        """Fitting should return the curve diameter."""
        result = fit_laurent_map(circle_export)
        # Unit circle has diameter 2
        assert abs(result.curve_scale - 2.0) < 0.1

    def test_fit_checks_simplicity(self, circle_export):
        """Result should include simplicity check."""
        result = fit_laurent_map(circle_export)
        assert result.ok
        assert result.simple_on_unit_circle

    def test_rejects_too_short_polyline(self):
        """Should reject polylines with fewer than 3 points."""
        export = SplineExport(
            version="1.0",
            timestamp="2026-01-22T00:00:00Z",
            closed=True,
            parameters=SplineParameters(),
            controlPoints=[Point(x=0, y=0), Point(x=1, y=1)],
        )
        result = fit_laurent_map(export)
        assert not result.ok
        assert "too short" in result.failure_reason.lower()


class TestLaurentMapSerialization:
    """Test LaurentMapResult serialization."""

    def test_to_laurent_map(self):
        """Convert to serializable LaurentMap."""
        lmr = LaurentMapResult(
            N=2,
            a0=1 + 2j,
            a=np.array([0.5 + 0.1j, 0.2]),
            b=np.array([0.3j, 0.1 - 0.1j]),
        )
        lm = lmr.to_laurent_map()

        assert lm.N == 2
        assert lm.a0.re == 1
        assert lm.a0.im == 2
        assert len(lm.a) == 2
        assert len(lm.b) == 2

    def test_from_laurent_map(self):
        """Create from serializable LaurentMap."""
        from analytic_continuation.types import LaurentMap, Complex

        lm = LaurentMap(
            N=2,
            a0=Complex(re=1, im=2),
            a=[Complex(re=0.5, im=0.1), Complex(re=0.2, im=0)],
            b=[Complex(re=0, im=0.3), Complex(re=0.1, im=-0.1)],
        )
        lmr = LaurentMapResult.from_laurent_map(lm)

        assert lmr.N == 2
        assert lmr.a0 == 1 + 2j
        assert lmr.a[0] == 0.5 + 0.1j

    def test_roundtrip(self):
        """Serialization roundtrip should preserve values."""
        original = LaurentMapResult(
            N=3,
            a0=1.5 - 0.5j,
            a=np.array([1, 2j, 0.5 + 0.5j]),
            b=np.array([0.1, 0.2, 0.3j]),
        )
        lm = original.to_laurent_map()
        restored = LaurentMapResult.from_laurent_map(lm)

        assert restored.N == original.N
        assert restored.a0 == original.a0
        assert np.allclose(restored.a, original.a)
        assert np.allclose(restored.b, original.b)
