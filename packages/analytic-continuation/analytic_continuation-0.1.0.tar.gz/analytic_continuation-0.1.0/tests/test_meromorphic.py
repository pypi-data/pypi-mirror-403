"""Tests for meromorphic function expression building."""

import pytest
from analytic_continuation import (
    Singularity,
    MeromorphicBuilder,
    build_meromorphic_expression,
    meromorphic_from_points,
    SpaceAdapter,
    TransformParams,
    Point,
)


class TestSingularity:
    """Test Singularity dataclass."""

    def test_default_multiplicity(self):
        """Default multiplicity is 1."""
        s = Singularity(1, 2)
        assert s.multiplicity == 1

    def test_complex_property(self):
        """z property returns complex number."""
        s = Singularity(3, 4)
        assert s.z == 3 + 4j

    def test_to_dict_without_multiplicity(self):
        """to_dict omits multiplicity if 1."""
        s = Singularity(1, 2)
        d = s.to_dict()
        assert "multiplicity" not in d
        assert d == {"x": 1, "y": 2}

    def test_to_dict_with_multiplicity(self):
        """to_dict includes multiplicity if > 1."""
        s = Singularity(1, 2, multiplicity=3)
        d = s.to_dict()
        assert d == {"x": 1, "y": 2, "multiplicity": 3}

    def test_from_dict(self):
        """from_dict creates Singularity correctly."""
        s = Singularity.from_dict({"x": 1, "y": 2, "multiplicity": 3})
        assert s.x == 1
        assert s.y == 2
        assert s.multiplicity == 3

    def test_from_point(self):
        """from_point creates Singularity from Point."""
        p = Point(x=5, y=6, index=0)
        s = Singularity.from_point(p, multiplicity=2)
        assert s.x == 5
        assert s.y == 6
        assert s.multiplicity == 2


class TestBuildExpression:
    """Test expression building from zeros and poles."""

    def test_empty(self):
        """No zeros or poles returns '1'."""
        expr = build_meromorphic_expression([], [])
        assert expr == "1"

    def test_single_zero_at_origin(self):
        """Single zero at origin -> 'z'."""
        zeros = [Singularity(0, 0)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "z"

    def test_single_zero_real(self):
        """Single real zero -> '(z-a)'."""
        zeros = [Singularity(2, 0)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z-2)"

    def test_single_zero_negative_real(self):
        """Negative real zero -> '(z+a)'."""
        zeros = [Singularity(-3, 0)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z+3)"

    def test_single_zero_imaginary(self):
        """Single imaginary zero."""
        zeros = [Singularity(0, 1)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z-i)"

    def test_single_zero_negative_imaginary(self):
        """Negative imaginary zero -> '(z+i)'."""
        zeros = [Singularity(0, -1)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z+i)"

    def test_single_zero_complex(self):
        """Complex zero."""
        zeros = [Singularity(1, 2)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z-(1+2*i))"

    def test_single_pole(self):
        """Single pole -> '1/(z-a)'."""
        poles = [Singularity(1, 0)]
        expr = build_meromorphic_expression([], poles)
        assert expr == "1/(z-1)"

    def test_zeros_and_poles(self):
        """Combined zeros and poles."""
        zeros = [Singularity(1, 0), Singularity(-1, 0)]
        poles = [Singularity(0, 1), Singularity(0, -1)]
        expr = build_meromorphic_expression(zeros, poles)
        assert expr == "(z-1)*(z+1)/((z-i)*(z+i))"

    def test_multiplicity_zero(self):
        """Zero with multiplicity > 1."""
        zeros = [Singularity(0, 0, multiplicity=2)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "z^2"

    def test_multiplicity_pole(self):
        """Pole with multiplicity > 1."""
        poles = [Singularity(1, 0, multiplicity=3)]
        expr = build_meromorphic_expression([], poles)
        assert expr == "1/(z-1)^3"

    def test_mixed_multiplicities(self):
        """Mixed multiplicities."""
        zeros = [Singularity(0, 0, multiplicity=2)]
        poles = [Singularity(1, 0, multiplicity=3)]
        expr = build_meromorphic_expression(zeros, poles)
        assert expr == "z^2/(z-1)^3"

    def test_multiple_zeros_only(self):
        """Multiple zeros, no poles."""
        zeros = [Singularity(1, 0), Singularity(2, 0), Singularity(3, 0)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z-1)*(z-2)*(z-3)"

    def test_multiple_poles_only(self):
        """Multiple poles wrapped in parens."""
        poles = [Singularity(1, 0), Singularity(2, 0)]
        expr = build_meromorphic_expression([], poles)
        assert expr == "1/((z-1)*(z-2))"


class TestFormatEdgeCases:
    """Test edge cases in number formatting."""

    def test_small_real(self):
        """Very small real part treated as zero."""
        zeros = [Singularity(1e-15, 1)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z-i)"

    def test_small_imaginary(self):
        """Very small imaginary part treated as zero."""
        zeros = [Singularity(1, 1e-15)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z-1)"

    def test_integer_formatting(self):
        """Integers formatted without decimals."""
        zeros = [Singularity(2.0, 0)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z-2)"  # Not "(z-2.0)"

    def test_float_formatting(self):
        """Non-integers keep decimal."""
        zeros = [Singularity(1.5, 0)]
        expr = build_meromorphic_expression(zeros, [])
        assert "(z-1.5)" in expr

    def test_negative_complex(self):
        """Negative real and imaginary parts."""
        zeros = [Singularity(-1, -1)]
        expr = build_meromorphic_expression(zeros, [])
        assert expr == "(z-(-1-i))"


class TestMeromorphicFromPoints:
    """Test convenience function for Point lists."""

    def test_basic_usage(self):
        """Basic usage with Point lists."""
        zeros = [Point(x=1, y=0), Point(x=-1, y=0)]
        poles = [Point(x=0, y=1)]
        expr = meromorphic_from_points(zeros, poles)
        assert expr == "(z-1)*(z+1)/(z-i)"

    def test_with_multiplicities(self):
        """Usage with explicit multiplicities."""
        zeros = [Point(x=0, y=0)]
        poles = [Point(x=1, y=0)]
        expr = meromorphic_from_points(
            zeros, poles,
            zero_multiplicities=[2],
            pole_multiplicities=[3],
        )
        assert expr == "z^2/(z-1)^3"


class TestMeromorphicBuilder:
    """Test the builder class."""

    def test_empty_builder(self):
        """Empty builder produces '1'."""
        builder = MeromorphicBuilder()
        assert builder.build_expression() == "1"

    def test_add_zero(self):
        """Adding zeros via builder."""
        builder = MeromorphicBuilder()
        builder.add_zero(1, 0)
        builder.add_zero(-1, 0)
        assert builder.build_expression() == "(z-1)*(z+1)"

    def test_add_pole(self):
        """Adding poles via builder."""
        builder = MeromorphicBuilder()
        builder.add_pole(0, 1)
        assert builder.build_expression() == "1/(z-i)"

    def test_chaining(self):
        """Method chaining works."""
        expr = (MeromorphicBuilder()
                .add_zero(1, 0)
                .add_pole(0, 1)
                .build_expression())
        assert expr == "(z-1)/(z-i)"

    def test_add_from_screen_coords(self):
        """Adding from screen coordinates via adapter."""
        params = TransformParams(offset_x=400, offset_y=300, scale_x=100)
        adapter = SpaceAdapter(params)

        builder = MeromorphicBuilder()
        # Screen (500, 200) -> logical (1, 1)
        builder.add_zero_from_screen(500, 200, adapter)
        # Screen (400, 300) -> logical (0, 0)
        builder.add_pole_from_screen(400, 300, adapter)

        expr = builder.build_expression()
        assert "(z-(1+i))" in expr
        assert "/z" in expr

    def test_clear(self):
        """Clear removes all zeros and poles."""
        builder = MeromorphicBuilder()
        builder.add_zero(1, 0).add_pole(0, 1)
        builder.clear()
        assert builder.build_expression() == "1"

    def test_remove_zero(self):
        """Remove zero by index."""
        builder = MeromorphicBuilder()
        builder.add_zero(1, 0).add_zero(2, 0).add_zero(3, 0)
        builder.remove_zero(1)  # Remove the (2, 0)
        assert builder.build_expression() == "(z-1)*(z-3)"

    def test_remove_pole(self):
        """Remove pole by index."""
        builder = MeromorphicBuilder()
        builder.add_pole(1, 0).add_pole(2, 0)
        builder.remove_pole(0)  # Remove the (1, 0)
        assert builder.build_expression() == "1/(z-2)"

    def test_to_dict(self):
        """Serialization to dict."""
        builder = MeromorphicBuilder()
        builder.add_zero(1, 0, multiplicity=2)
        builder.add_pole(0, 1)

        d = builder.to_dict()
        assert len(d["zeros"]) == 1
        assert len(d["poles"]) == 1
        assert d["zeros"][0]["x"] == 1
        assert d["zeros"][0]["multiplicity"] == 2

    def test_from_dict(self):
        """Deserialization from dict."""
        d = {
            "zeros": [{"x": 1, "y": 0}],
            "poles": [{"x": 0, "y": 1, "multiplicity": 2}],
        }
        builder = MeromorphicBuilder.from_dict(d)

        assert len(builder.zeros) == 1
        assert len(builder.poles) == 1
        assert builder.poles[0].multiplicity == 2


class TestKnownFunctions:
    """Test that we can build expressions for known functions."""

    def test_rational_z2_minus_1_over_z2_plus_1(self):
        """(z^2-1)/(z^2+1) has zeros at ±1, poles at ±i."""
        zeros = [Singularity(1, 0), Singularity(-1, 0)]
        poles = [Singularity(0, 1), Singularity(0, -1)]
        expr = build_meromorphic_expression(zeros, poles)
        assert expr == "(z-1)*(z+1)/((z-i)*(z+i))"

    def test_simple_pole_1_over_z(self):
        """1/z has a simple pole at origin."""
        expr = build_meromorphic_expression([], [Singularity(0, 0)])
        assert expr == "1/z"

    def test_double_pole(self):
        """1/z^2 has a double pole at origin."""
        expr = build_meromorphic_expression([], [Singularity(0, 0, multiplicity=2)])
        assert expr == "1/z^2"

    def test_cubic_polynomial(self):
        """z^3 - 1 has zeros at cube roots of unity."""
        import cmath
        roots = [cmath.exp(2j * cmath.pi * k / 3) for k in range(3)]
        zeros = [Singularity(r.real, r.imag) for r in roots]
        expr = build_meromorphic_expression(zeros, [])
        # Should have 3 factors
        assert expr.count("(z") == 3
