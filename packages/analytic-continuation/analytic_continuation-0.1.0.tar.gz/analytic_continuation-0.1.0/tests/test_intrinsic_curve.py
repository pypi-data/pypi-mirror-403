"""
Tests for intrinsic curve analysis (Cesàro/Whewell representations).
"""

import pytest
import numpy as np
from analytic_continuation.laurent import LaurentMapResult
from analytic_continuation.intrinsic_curve import (
    CesaroRepresentation,
    WhewellRepresentation,
    LogBijectionData,
    ComplexityEstimates,
    IntrinsicCurveAnalysis,
    analyze_bijection,
    compute_log_bijection,
    compute_cesaro_form,
    compute_whewell_form,
    estimate_complexity,
    suggest_inversion_config,
    # Pre-check functions
    precheck_contour,
    precheck_contour_from_spline_export,
    ContourPreCheckResult,
)


class TestLogBijection:
    """Tests for log bijection computation."""

    @pytest.fixture
    def simple_laurent_map(self):
        """A simple Laurent map: z(ζ) = ζ + 0.1/ζ (maps to ellipse-like curve)."""
        N = 2
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j, 0.0])
        b = np.array([0.1 + 0j, 0.0])
        return LaurentMapResult(N=N, a0=a0, a=a, b=b)

    def test_log_bijection_samples(self, simple_laurent_map):
        """Test that log bijection produces correct number of samples."""
        log_data = compute_log_bijection(simple_laurent_map, curve_scale=2.2, samples=512)

        assert len(log_data.theta_samples) == 512
        assert len(log_data.log_z_samples) == 512
        assert len(log_data.z_samples) == 512
        assert len(log_data.log_derivative_samples) == 512

    def test_log_bijection_theta_range(self, simple_laurent_map):
        """Test that theta samples span [0, 2π)."""
        log_data = compute_log_bijection(simple_laurent_map, curve_scale=2.2, samples=256)

        assert log_data.theta_samples[0] == 0
        assert log_data.theta_samples[-1] < 2 * np.pi
        assert np.all(np.diff(log_data.theta_samples) > 0)  # Monotonically increasing

    def test_log_bijection_continuity(self, simple_laurent_map):
        """Test that log(z) is continuous (no branch jumps)."""
        log_data = compute_log_bijection(simple_laurent_map, curve_scale=2.2, samples=1024)

        # Check that imaginary part changes smoothly
        im_diffs = np.abs(np.diff(log_data.log_z_samples.imag))
        # No large jumps (would indicate branch cut crossing)
        assert np.all(im_diffs < 0.5)

    def test_log_bijection_serialization(self, simple_laurent_map):
        """Test serialization round-trip."""
        log_data = compute_log_bijection(simple_laurent_map, curve_scale=2.2, samples=64)

        d = log_data.to_dict()
        restored = LogBijectionData.from_dict(d)

        assert restored.laurent_N == log_data.laurent_N
        assert restored.curve_scale == log_data.curve_scale
        np.testing.assert_array_almost_equal(restored.theta_samples, log_data.theta_samples)


class TestCesaroRepresentation:
    """Tests for Cesàro (curvature) representation."""

    @pytest.fixture
    def log_data(self):
        """Log bijection data for a simple curve."""
        N = 2
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j, 0.0])
        b = np.array([0.1 + 0j, 0.0])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)
        return compute_log_bijection(lmap, curve_scale=2.2, samples=512)

    def test_cesaro_arc_length_monotonic(self, log_data):
        """Test that arc length is monotonically increasing."""
        cesaro = compute_cesaro_form(log_data)

        assert np.all(np.diff(cesaro.arc_lengths) >= 0)

    def test_cesaro_closed_curve(self, log_data):
        """Test that total arc length is finite and positive."""
        cesaro = compute_cesaro_form(log_data)

        assert cesaro.total_arc_length > 0
        assert np.isfinite(cesaro.total_arc_length)

    def test_cesaro_interpolation(self, log_data):
        """Test curvature interpolation."""
        cesaro = compute_cesaro_form(log_data)

        # Test interpolation at various points
        for s in [0.0, cesaro.total_arc_length / 4, cesaro.total_arc_length / 2]:
            kappa = cesaro.kappa_at(s)
            assert np.isfinite(kappa)

    def test_cesaro_serialization(self, log_data):
        """Test serialization round-trip."""
        cesaro = compute_cesaro_form(log_data)

        d = cesaro.to_dict()
        restored = CesaroRepresentation.from_dict(d)

        assert restored.samples == cesaro.samples
        assert restored.total_arc_length == cesaro.total_arc_length
        np.testing.assert_array_almost_equal(restored.curvatures, cesaro.curvatures)


class TestWhewellRepresentation:
    """Tests for Whewell (tangent angle) representation."""

    @pytest.fixture
    def cesaro(self):
        """Cesàro representation for a simple curve."""
        N = 2
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j, 0.0])
        b = np.array([0.1 + 0j, 0.0])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)
        log_data = compute_log_bijection(lmap, curve_scale=2.2, samples=512)
        return compute_cesaro_form(log_data)

    def test_whewell_winding_number(self, cesaro):
        """Test that winding number is approximately 1 for simple closed curve."""
        whewell = compute_whewell_form(cesaro)

        # For a simple closed curve, winding number should be 1
        assert abs(whewell.winding_number - 1.0) < 0.1

    def test_whewell_angle_monotonic(self, cesaro):
        """Test that tangent angle increases monotonically for convex-ish curve."""
        whewell = compute_whewell_form(cesaro)

        # For a convex curve, tangent angle should be roughly monotonic
        # Allow some small decreases due to non-convexity
        decreases = np.sum(np.diff(whewell.tangent_angles) < -0.1)
        assert decreases < whewell.samples // 10  # Less than 10% decreasing

    def test_whewell_interpolation(self, cesaro):
        """Test tangent angle interpolation."""
        whewell = compute_whewell_form(cesaro)

        # Test interpolation at various points
        for s in [0.0, whewell.total_arc_length / 3, whewell.total_arc_length * 0.9]:
            phi = whewell.phi_at(s)
            assert np.isfinite(phi)

    def test_whewell_serialization(self, cesaro):
        """Test serialization round-trip."""
        whewell = compute_whewell_form(cesaro)

        d = whewell.to_dict()
        restored = WhewellRepresentation.from_dict(d)

        assert restored.samples == whewell.samples
        assert abs(restored.winding_number - whewell.winding_number) < 1e-10


class TestComplexityEstimates:
    """Tests for complexity estimation."""

    @pytest.fixture
    def analysis_simple(self):
        """Analysis of a simple curve."""
        N = 2
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j, 0.0])
        b = np.array([0.1 + 0j, 0.0])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)
        return analyze_bijection(lmap, curve_scale=2.2, samples=512)

    @pytest.fixture
    def analysis_complex(self):
        """Analysis of a more complex curve."""
        N = 6
        a0 = 0.0 + 0j
        a = np.array([1.0, 0.1 + 0.05j, 0.03 - 0.02j, 0.01 + 0.01j, 0.005, 0.002j])
        b = np.array([0.2 + 0.1j, 0.05 - 0.03j, 0.02 + 0.01j, 0.01, 0.005j, 0.002])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)
        return analyze_bijection(lmap, curve_scale=2.5, samples=512)

    def test_complexity_metrics_positive(self, analysis_simple):
        """Test that complexity metrics are positive."""
        c = analysis_simple.complexity

        assert c.total_curvature > 0
        assert c.total_arc_length > 0
        assert c.min_jacobian > 0
        assert c.max_jacobian > 0
        assert c.jacobian_ratio >= 1.0
        assert c.inversion_difficulty > 0
        assert c.sampling_density_factor > 0
        assert c.newton_convergence_factor > 0

    def test_complexity_winding_simple(self, analysis_simple):
        """Test that winding number is ~1 for simple curve."""
        c = analysis_simple.complexity
        assert abs(c.winding_number - 1.0) < 0.1

    def test_complexity_comparison(self, analysis_simple, analysis_complex):
        """Test that complex curve has higher complexity scores."""
        c_simple = analysis_simple.complexity
        c_complex = analysis_complex.complexity

        # Complex curve should have higher curvature variation
        assert c_complex.curvature_variation > c_simple.curvature_variation

        # Complex curve should have higher inversion difficulty
        assert c_complex.inversion_difficulty > c_simple.inversion_difficulty

    def test_complexity_summary(self, analysis_simple):
        """Test that summary string is generated."""
        summary = analysis_simple.complexity.summary()

        assert "Bijection Complexity Analysis" in summary
        assert "Total curvature" in summary
        assert "Inversion difficulty" in summary

    def test_complexity_serialization(self, analysis_simple):
        """Test serialization round-trip."""
        c = analysis_simple.complexity

        d = c.to_dict()
        restored = ComplexityEstimates.from_dict(d)

        assert abs(restored.total_curvature - c.total_curvature) < 1e-10
        assert abs(restored.inversion_difficulty - c.inversion_difficulty) < 1e-10


class TestAnalyzeBijection:
    """Tests for the main analyze_bijection function."""

    def test_full_analysis(self):
        """Test complete analysis pipeline."""
        N = 3
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j, 0.02 + 0.01j, 0.005])
        b = np.array([0.12 + 0.05j, 0.01 - 0.01j, 0.003j])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)

        analysis = analyze_bijection(lmap, curve_scale=2.3, samples=256)

        assert isinstance(analysis, IntrinsicCurveAnalysis)
        assert analysis.log_data is not None
        assert analysis.cesaro is not None
        assert analysis.whewell is not None
        assert analysis.complexity is not None

    def test_analysis_serialization(self):
        """Test full analysis serialization round-trip."""
        N = 2
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j, 0.0])
        b = np.array([0.1 + 0j, 0.0])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)

        analysis = analyze_bijection(lmap, curve_scale=2.2, samples=128)

        d = analysis.to_dict()
        restored = IntrinsicCurveAnalysis.from_dict(d)

        assert restored.cesaro.samples == analysis.cesaro.samples
        assert (
            abs(restored.complexity.total_curvature - analysis.complexity.total_curvature) < 1e-10
        )


class TestSuggestInversionConfig:
    """Tests for configuration suggestion."""

    def test_suggest_basic(self):
        """Test basic configuration suggestion."""
        N = 2
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j, 0.0])
        b = np.array([0.1 + 0j, 0.0])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)

        analysis = analyze_bijection(lmap, curve_scale=2.2, samples=256)
        config = suggest_inversion_config(analysis.complexity)

        assert "theta_grid" in config
        assert "max_iters" in config
        assert "max_backtracks" in config
        assert "damping" in config
        assert config["damping"] is True

    def test_suggest_scales_with_complexity(self):
        """Test that suggestions scale with curve complexity."""
        # Simple curve
        a_simple = np.array([1.0 + 0j, 0.0])
        b_simple = np.array([0.1 + 0j, 0.0])
        lmap_simple = LaurentMapResult(N=2, a0=0.0, a=a_simple, b=b_simple)
        analysis_simple = analyze_bijection(lmap_simple, curve_scale=2.2, samples=256)
        config_simple = suggest_inversion_config(analysis_simple.complexity)

        # Complex curve
        a_complex = np.array([1.0, 0.15 + 0.1j, 0.05 - 0.03j, 0.02 + 0.02j])
        b_complex = np.array([0.25 + 0.15j, 0.08 - 0.05j, 0.03 + 0.02j, 0.01])
        lmap_complex = LaurentMapResult(N=4, a0=0.0, a=a_complex, b=b_complex)
        analysis_complex = analyze_bijection(lmap_complex, curve_scale=2.5, samples=256)
        config_complex = suggest_inversion_config(analysis_complex.complexity)

        # Complex curve should need more samples and iterations
        assert config_complex["theta_grid"] >= config_simple["theta_grid"]
        assert config_complex["max_iters"] >= config_simple["max_iters"]


class TestEdgeCases:
    """Tests for edge cases."""

    def test_unit_circle(self):
        """Test analysis of exact unit circle (identity map)."""
        # z(ζ) = ζ (identity)
        N = 1
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j])
        b = np.array([0.0 + 0j])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)

        analysis = analyze_bijection(lmap, curve_scale=2.0, samples=256)

        # Unit circle has constant curvature = 1
        assert abs(analysis.complexity.mean_curvature - 1.0) < 0.1

        # Jacobian should be constant = 1
        assert abs(analysis.complexity.jacobian_ratio - 1.0) < 0.1

    def test_small_samples(self):
        """Test with minimal samples."""
        N = 2
        a0 = 0.0 + 0j
        a = np.array([1.0 + 0j, 0.0])
        b = np.array([0.1 + 0j, 0.0])
        lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)

        # Should work even with few samples
        analysis = analyze_bijection(lmap, curve_scale=2.2, samples=32)

        assert analysis.cesaro.samples == 32
        assert analysis.complexity.total_arc_length > 0


# =============================================================================
# Contour Pre-Check Tests (Stage 1 Gate)
# =============================================================================


class TestContourPreCheck:
    """Tests for quick contour pre-check functionality."""

    def test_simple_circle_passes(self):
        """A simple circle should pass all checks."""
        theta = np.linspace(0, 2 * np.pi, 50, endpoint=False)
        circle = [(np.cos(t), np.sin(t)) for t in theta]

        result = precheck_contour(circle)

        assert result.ok is True
        assert result.proceed is True
        assert result.is_simple is True
        assert result.estimated_difficulty == "easy"
        assert len(result.errors) == 0

    def test_figure8_detected(self):
        """A figure-8 (self-intersecting) should be detected."""
        theta = np.linspace(0, 2 * np.pi, 100, endpoint=False)
        figure8 = [(np.sin(t), np.sin(2 * t)) for t in theta]

        result = precheck_contour(figure8)

        assert result.ok is False
        assert result.proceed is False
        assert result.is_simple is False
        assert result.estimated_difficulty == "infeasible"
        assert any("Self-intersection" in e for e in result.errors)

    def test_too_few_points(self):
        """Contour with too few points should fail."""
        triangle = [(0, 0), (1, 0), (0.5, 1)]

        result = precheck_contour(triangle, min_points=8)

        assert result.has_sufficient_points is False
        assert any("Too few points" in e for e in result.errors)

    def test_degenerate_contour(self):
        """Degenerate (zero-area) contour should fail."""
        line = [(0, 0), (1, 0), (2, 0), (3, 0)]

        result = precheck_contour(line)

        assert result.ok is False
        assert "Degenerate" in result.errors[0] or result.aspect_ratio == float("inf")

    def test_elongated_contour_warns(self):
        """Very elongated contour should generate warning."""
        theta = np.linspace(0, 2 * np.pi, 50, endpoint=False)
        ellipse = [(10 * np.cos(t), 0.1 * np.sin(t)) for t in theta]

        result = precheck_contour(ellipse)

        assert result.aspect_ratio > 20  # Very elongated
        assert any("elongated" in w.lower() for w in result.warnings)

    def test_sharp_turn_warns(self):
        """Sharp turns should generate warnings."""
        # Pentagon with one very sharp point
        star = [
            (0, 1),
            (0.1, 0.1),  # Sharp inward point
            (1, 0),
            (0, -1),
            (-1, 0),
        ]

        result = precheck_contour(star)

        # Max turning angle should be detected
        assert result.max_turning_angle > np.radians(90)

    def test_precheck_from_spline_export(self):
        """Test precheck_contour_from_spline_export uses adaptive polyline."""
        # Simple control points
        control = [(0, 0), (1, 0), (1, 1), (0, 1)]

        # More detailed adaptive polyline (a circle)
        theta = np.linspace(0, 2 * np.pi, 50, endpoint=False)
        adaptive = [(np.cos(t), np.sin(t)) for t in theta]

        result = precheck_contour_from_spline_export(
            control_points=control,
            adaptive_polyline=adaptive,
            closed=True,
        )

        # Should use adaptive (50 points), not control (4 points)
        assert result.num_points == 50
        assert result.is_simple is True

    def test_result_serialization(self):
        """Test that result can be serialized to dict."""
        theta = np.linspace(0, 2 * np.pi, 30, endpoint=False)
        circle = [(np.cos(t), np.sin(t)) for t in theta]

        result = precheck_contour(circle)
        d = result.to_dict()

        assert "ok" in d
        assert "proceed" in d
        assert "is_simple" in d
        assert "estimated_difficulty" in d
        assert "bounding_box" in d
        assert len(d["bounding_box"]) == 4

    def test_difficulty_scaling(self):
        """Test that difficulty scales with complexity."""
        # Simple circle
        theta = np.linspace(0, 2 * np.pi, 50, endpoint=False)
        circle = [(np.cos(t), np.sin(t)) for t in theta]
        circle_result = precheck_contour(circle)

        # More complex star
        star_pts = []
        for i in range(20):
            angle = i * np.pi / 10
            r = 1.0 if i % 2 == 0 else 0.5
            star_pts.append((r * np.cos(angle), r * np.sin(angle)))
        star_result = precheck_contour(star_pts)

        # Star should be harder than circle
        difficulty_order = ["easy", "moderate", "hard", "extreme", "infeasible"]
        circle_idx = difficulty_order.index(circle_result.estimated_difficulty)
        star_idx = difficulty_order.index(star_result.estimated_difficulty)

        assert star_idx >= circle_idx
