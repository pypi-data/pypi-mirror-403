"""Tests for analytic continuation pipeline (Stages 4-6)."""

import pytest
import numpy as np
from analytic_continuation import (
    Pole,
    HolomorphicCheckConfig,
    InvertConfig,
    HolomorphicCheckResult,
    InvertResult,
    CompositionResult,
    check_f_holomorphic_on_annulus,
    invert_z,
    compute_composition,
    LaurentMapResult,
)


class TestPole:
    """Test Pole dataclass."""

    def test_creation(self):
        """Create a pole."""
        p = Pole(z=1 + 2j, multiplicity=2)
        assert p.z == 1 + 2j
        assert p.multiplicity == 2

    def test_default_multiplicity(self):
        """Default multiplicity is 1."""
        p = Pole(z=0j)
        assert p.multiplicity == 1


class TestCheckHolomorphic:
    """Test pole holomorphicity checking (Stage 4)."""

    @pytest.fixture
    def identity_map(self):
        """Laurent map for z(ζ) = ζ (identity on unit disk)."""
        return LaurentMapResult(
            N=1,
            a0=0j,
            a=np.array([1 + 0j]),
            b=np.array([0j]),
        )

    def test_no_poles(self, identity_map):
        """Empty pole list should pass."""
        result = check_f_holomorphic_on_annulus(
            poles=[],
            lmap=identity_map,
            curve_scale=2.0,
            min_distance_param=0.1,
        )
        assert result.ok
        assert result.min_pole_distance == float('inf')

    def test_pole_far_away(self, identity_map):
        """Pole far from curve should pass."""
        # Identity map: unit circle is the curve
        # Pole at z=5 is far from unit circle
        result = check_f_holomorphic_on_annulus(
            poles=[Pole(z=5 + 0j)],
            lmap=identity_map,
            curve_scale=2.0,
            min_distance_param=0.1,
        )
        assert result.ok
        assert result.min_pole_distance > 3  # At least 4 away from unit circle

    def test_pole_on_curve(self, identity_map):
        """Pole on the curve should fail."""
        # Pole at z=1 is on the unit circle
        result = check_f_holomorphic_on_annulus(
            poles=[Pole(z=1 + 0j)],
            lmap=identity_map,
            curve_scale=2.0,
            min_distance_param=0.1,
        )
        assert not result.ok
        assert result.closest_pole == 1 + 0j

    def test_pole_inside_curve(self, identity_map):
        """Pole inside curve should fail with small margin."""
        # Pole at z=0.5 is inside unit circle, close to it
        cfg = HolomorphicCheckConfig(pole_margin_factor=1.0)
        result = check_f_holomorphic_on_annulus(
            poles=[Pole(z=0.95 + 0j)],  # Very close to curve
            lmap=identity_map,
            curve_scale=2.0,
            min_distance_param=0.1,  # margin = 0.1
            cfg=cfg,
        )
        # Should fail because 0.95 is only 0.05 from the curve, less than margin 0.1
        assert not result.ok

    def test_multiple_poles(self, identity_map):
        """Should track closest pole."""
        result = check_f_holomorphic_on_annulus(
            poles=[Pole(z=5 + 0j), Pole(z=2 + 0j)],  # 2+0j is closer
            lmap=identity_map,
            curve_scale=2.0,
            min_distance_param=0.1,
        )
        assert result.ok
        assert result.closest_pole == 2 + 0j


class TestInvertZ:
    """Test map inversion (Stage 5)."""

    @pytest.fixture
    def identity_map(self):
        """Laurent map for z(ζ) = ζ."""
        return LaurentMapResult(
            N=1,
            a0=0j,
            a=np.array([1 + 0j]),
            b=np.array([0j]),
        )

    @pytest.fixture
    def scaled_map(self):
        """Laurent map for z(ζ) = 2ζ."""
        return LaurentMapResult(
            N=1,
            a0=0j,
            a=np.array([2 + 0j]),
            b=np.array([0j]),
        )

    def test_invert_identity_on_circle(self, identity_map):
        """Inverting on unit circle with identity map."""
        # z = 1 should invert to ζ = 1
        result = invert_z(1 + 0j, identity_map, curve_scale=2.0)
        assert result.converged
        assert abs(result.zeta - 1) < 1e-6

    def test_invert_identity_at_i(self, identity_map):
        """Inverting at i with identity map."""
        result = invert_z(0 + 1j, identity_map, curve_scale=2.0)
        assert result.converged
        assert abs(result.zeta - 1j) < 1e-6

    def test_invert_scaled(self, scaled_map):
        """Inverting with scaled map z(ζ) = 2ζ."""
        # z = 2 should invert to ζ = 1
        result = invert_z(2 + 0j, scaled_map, curve_scale=4.0)
        assert result.converged
        assert abs(result.zeta - 1) < 1e-6

    def test_selects_root_near_unit_circle(self, identity_map):
        """Should select root closest to unit circle."""
        # For identity map, all points have unique inverse
        # But for more complex maps, multiple roots may exist
        result = invert_z(np.exp(1j * np.pi / 3), identity_map, curve_scale=2.0)
        assert result.converged
        assert abs(abs(result.zeta) - 1) < 1e-6  # Should be on unit circle


class TestComputeComposition:
    """Test composition computation (Stage 6)."""

    @pytest.fixture
    def identity_map(self):
        """Laurent map for z(ζ) = ζ."""
        return LaurentMapResult(
            N=1,
            a0=0j,
            a=np.array([1 + 0j]),
            b=np.array([0j]),
        )

    def test_composition_with_identity_f(self, identity_map):
        """Composition with f(z) = z should return z."""
        f = lambda z: z
        z_query = 1 + 0j

        result = compute_composition(z_query, f, identity_map, curve_scale=2.0)

        assert result.ok
        assert abs(result.value - z_query) < 1e-6

    def test_composition_with_square(self, identity_map):
        """Composition with f(z) = z^2."""
        f = lambda z: z ** 2
        z_query = 1 + 0j

        result = compute_composition(z_query, f, identity_map, curve_scale=2.0)

        assert result.ok
        assert abs(result.value - 1) < 1e-6  # 1^2 = 1

    def test_composition_at_i(self, identity_map):
        """Composition at z = i with f(z) = z^2."""
        f = lambda z: z ** 2
        z_query = 0 + 1j

        result = compute_composition(z_query, f, identity_map, curve_scale=2.0)

        assert result.ok
        assert abs(result.value - (-1)) < 1e-6  # i^2 = -1

    def test_composition_returns_zeta(self, identity_map):
        """Result should include the inverted zeta."""
        f = lambda z: z
        z_query = np.exp(1j * np.pi / 4)

        result = compute_composition(z_query, f, identity_map, curve_scale=2.0)

        assert result.ok
        assert result.zeta is not None
        assert abs(result.zeta - z_query) < 1e-6  # For identity map

    def test_composition_with_pole(self, identity_map):
        """Composition with f having a pole at query point should work (or fail gracefully)."""
        # f(z) = 1/z has a pole at z=0
        f = lambda z: 1 / z if abs(z) > 1e-10 else float('inf')

        # Query at z=1 (not at pole)
        result = compute_composition(1 + 0j, f, identity_map, curve_scale=2.0)
        assert result.ok
        assert abs(result.value - 1) < 1e-6


class TestCompositionWithComplexMaps:
    """Test composition with more complex Laurent maps."""

    @pytest.fixture
    def offset_map(self):
        """Laurent map for z(ζ) = 1 + ζ (shifted circle)."""
        return LaurentMapResult(
            N=1,
            a0=1 + 0j,
            a=np.array([1 + 0j]),
            b=np.array([0j]),
        )

    def test_offset_circle(self, offset_map):
        """Composition on shifted circle."""
        f = lambda z: z ** 2

        # z = 2 is on the shifted circle (at ζ = 1)
        # f(z(1)) = f(2) = 4
        result = compute_composition(2 + 0j, f, offset_map, curve_scale=2.0)

        assert result.ok
        assert abs(result.value - 4) < 1e-5


class TestConfigs:
    """Test configuration classes."""

    def test_holomorphic_check_config_defaults(self):
        """Default config values."""
        cfg = HolomorphicCheckConfig()
        assert cfg.theta_grid == 2048
        assert 0.97 in cfg.rho_samples

    def test_invert_config_defaults(self):
        """Default invert config values."""
        cfg = InvertConfig()
        assert cfg.theta_grid == 256
        assert cfg.max_iters == 40
        assert cfg.damping is True

    def test_config_from_pipeline(self):
        """Create config from pipeline config dict."""
        pipeline_cfg = {
            "fHolomorphicCheck": {
                "theta_grid": 1024,
                "rho_samples": [0.95, 1.0, 1.05],
            }
        }
        cfg = HolomorphicCheckConfig.from_pipeline_config(pipeline_cfg)
        assert cfg.theta_grid == 1024
        assert cfg.rho_samples == [0.95, 1.0, 1.05]
