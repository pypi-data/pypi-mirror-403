"""
Meromorphic function construction from zeros and poles.

Converts lists of zeros/poles (with optional multiplicities) to
mathematical expressions parseable by py_domaincolor/sympy.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from .types import Point


@dataclass
class Singularity:
    """A zero or pole with location and multiplicity."""
    x: float
    y: float
    multiplicity: int = 1

    @property
    def z(self) -> complex:
        return complex(self.x, self.y)

    def to_dict(self) -> dict:
        d = {"x": self.x, "y": self.y}
        if self.multiplicity != 1:
            d["multiplicity"] = self.multiplicity
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Singularity":
        return cls(
            x=d["x"],
            y=d["y"],
            multiplicity=d.get("multiplicity", 1),
        )

    @classmethod
    def from_point(cls, p: Point, multiplicity: int = 1) -> "Singularity":
        return cls(x=p.x, y=p.y, multiplicity=multiplicity)


def _format_complex(z: complex, tol: float = 1e-10) -> str:
    """
    Format a complex number for sympy expression.

    Produces clean output like:
    - "1" for 1+0j
    - "i" for 0+1j
    - "1+2i" for 1+2j
    - "-1-2i" for -1-2j
    """
    re, im = z.real, z.imag

    # Handle near-zero components
    if abs(re) < tol:
        re = 0
    if abs(im) < tol:
        im = 0

    # Pure real
    if im == 0:
        if re == int(re):
            return str(int(re))
        return f"{re:.10g}"

    # Pure imaginary
    if re == 0:
        if im == 1:
            return "i"
        elif im == -1:
            return "-i"
        elif im == int(im):
            return f"{int(im)}*i"
        return f"{im:.10g}*i"

    # Complex
    re_str = str(int(re)) if re == int(re) else f"{re:.10g}"

    if im == 1:
        im_str = "+i"
    elif im == -1:
        im_str = "-i"
    elif im > 0:
        im_val = str(int(im)) if im == int(im) else f"{im:.10g}"
        im_str = f"+{im_val}*i"
    else:
        im_val = str(int(abs(im))) if im == int(im) else f"{abs(im):.10g}"
        im_str = f"-{im_val}*i"

    return f"({re_str}{im_str})"


def _format_factor(z: complex, tol: float = 1e-10) -> str:
    """
    Format (z - z0) factor for the expression.

    Handles special cases:
    - (z - 0) -> z
    - (z - 1) -> (z-1)
    - (z - (1+2i)) -> (z-(1+2*i))
    - (z - (-i)) -> (z+i)
    """
    re, im = z.real, z.imag

    if abs(re) < tol:
        re = 0
    if abs(im) < tol:
        im = 0

    # Zero at origin
    if re == 0 and im == 0:
        return "z"

    # Pure real, negative: (z - (-1)) -> (z+1)
    if im == 0 and re < 0:
        val = -re
        return f"(z+{int(val)})" if val == int(val) else f"(z+{val:.10g})"

    # Pure real, positive: (z - 1) -> (z-1)
    if im == 0:
        return f"(z-{int(re)})" if re == int(re) else f"(z-{re:.10g})"

    # Pure imaginary, negative: (z - (-i)) -> (z+i)
    if re == 0 and im < 0:
        if im == -1:
            return "(z+i)"
        val = -im
        return f"(z+{int(val)}*i)" if val == int(val) else f"(z+{val:.10g}*i)"

    # Pure imaginary, positive: (z - i) -> (z-i)
    if re == 0:
        if im == 1:
            return "(z-i)"
        return f"(z-{int(im)}*i)" if im == int(im) else f"(z-{im:.10g}*i)"

    # General complex case
    z_str = _format_complex(z, tol)

    # If z_str starts with '(' it's already wrapped
    if z_str.startswith('('):
        return f"(z-{z_str})"

    return f"(z-{z_str})"


def build_meromorphic_expression(
    zeros: List[Singularity],
    poles: List[Singularity],
    normalize: bool = False,
) -> str:
    """
    Build a sympy-compatible expression for a meromorphic function.

    Parameters
    ----------
    zeros : List[Singularity]
        List of zeros with locations and multiplicities
    poles : List[Singularity]
        List of poles with locations and multiplicities
    normalize : bool
        If True, add a leading coefficient to normalize (not yet implemented)

    Returns
    -------
    str
        Expression string like "(z-1)*(z+1)/((z-i)*(z+i))"

    Examples
    --------
    >>> build_meromorphic_expression(
    ...     zeros=[Singularity(1, 0), Singularity(-1, 0)],
    ...     poles=[Singularity(0, 1), Singularity(0, -1)]
    ... )
    '(z-1)*(z+1)/((z-i)*(z+i))'
    """
    if not zeros and not poles:
        return "1"

    # Build numerator from zeros
    num_factors = []
    for zero in zeros:
        factor = _format_factor(zero.z)
        if zero.multiplicity == 1:
            num_factors.append(factor)
        else:
            num_factors.append(f"{factor}^{zero.multiplicity}")

    # Build denominator from poles
    den_factors = []
    for pole in poles:
        factor = _format_factor(pole.z)
        if pole.multiplicity == 1:
            den_factors.append(factor)
        else:
            den_factors.append(f"{factor}^{pole.multiplicity}")

    # Construct expression
    if num_factors:
        numerator = "*".join(num_factors)
    else:
        numerator = "1"

    if den_factors:
        denominator = "*".join(den_factors)
        # Wrap denominator in parens if multiple factors
        if len(den_factors) > 1:
            denominator = f"({denominator})"
        return f"{numerator}/{denominator}"
    else:
        return numerator


def meromorphic_from_points(
    zeros: List[Point],
    poles: List[Point],
    zero_multiplicities: Optional[List[int]] = None,
    pole_multiplicities: Optional[List[int]] = None,
) -> str:
    """
    Convenience function to build expression directly from Point lists.

    Parameters
    ----------
    zeros : List[Point]
        Zero locations
    poles : List[Point]
        Pole locations
    zero_multiplicities : List[int], optional
        Multiplicities for zeros (default all 1)
    pole_multiplicities : List[int], optional
        Multiplicities for poles (default all 1)

    Returns
    -------
    str
        Sympy-compatible expression
    """
    zero_mults = zero_multiplicities or [1] * len(zeros)
    pole_mults = pole_multiplicities or [1] * len(poles)

    zero_sings = [
        Singularity(p.x, p.y, m)
        for p, m in zip(zeros, zero_mults)
    ]
    pole_sings = [
        Singularity(p.x, p.y, m)
        for p, m in zip(poles, pole_mults)
    ]

    return build_meromorphic_expression(zero_sings, pole_sings)


class MeromorphicBuilder:
    """
    Builder class for constructing meromorphic functions interactively.

    Integrates with SpaceAdapter for coordinate transforms.
    """

    def __init__(self):
        self.zeros: List[Singularity] = []
        self.poles: List[Singularity] = []

    def add_zero(self, x: float, y: float, multiplicity: int = 1) -> "MeromorphicBuilder":
        """Add a zero at (x, y) in logical coordinates."""
        self.zeros.append(Singularity(x, y, multiplicity))
        return self

    def add_pole(self, x: float, y: float, multiplicity: int = 1) -> "MeromorphicBuilder":
        """Add a pole at (x, y) in logical coordinates."""
        self.poles.append(Singularity(x, y, multiplicity))
        return self

    def add_zero_from_screen(
        self,
        screen_x: float,
        screen_y: float,
        adapter: "SpaceAdapter",
        multiplicity: int = 1,
    ) -> "MeromorphicBuilder":
        """Add a zero from screen coordinates, transforming via adapter."""
        from .space_adapter import SpaceAdapter
        lx, ly = adapter.screen_to_logical(screen_x, screen_y)
        return self.add_zero(lx, ly, multiplicity)

    def add_pole_from_screen(
        self,
        screen_x: float,
        screen_y: float,
        adapter: "SpaceAdapter",
        multiplicity: int = 1,
    ) -> "MeromorphicBuilder":
        """Add a pole from screen coordinates, transforming via adapter."""
        from .space_adapter import SpaceAdapter
        lx, ly = adapter.screen_to_logical(screen_x, screen_y)
        return self.add_pole(lx, ly, multiplicity)

    def clear(self) -> "MeromorphicBuilder":
        """Clear all zeros and poles."""
        self.zeros.clear()
        self.poles.clear()
        return self

    def remove_zero(self, index: int) -> "MeromorphicBuilder":
        """Remove zero by index."""
        if 0 <= index < len(self.zeros):
            del self.zeros[index]
        return self

    def remove_pole(self, index: int) -> "MeromorphicBuilder":
        """Remove pole by index."""
        if 0 <= index < len(self.poles):
            del self.poles[index]
        return self

    def build_expression(self) -> str:
        """Build the sympy-compatible expression string."""
        return build_meromorphic_expression(self.zeros, self.poles)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "zeros": [z.to_dict() for z in self.zeros],
            "poles": [p.to_dict() for p in self.poles],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MeromorphicBuilder":
        """Deserialize from dictionary."""
        builder = cls()
        builder.zeros = [Singularity.from_dict(z) for z in d.get("zeros", [])]
        builder.poles = [Singularity.from_dict(p) for p in d.get("poles", [])]
        return builder
