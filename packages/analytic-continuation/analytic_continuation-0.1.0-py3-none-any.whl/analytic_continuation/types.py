"""
Type definitions for analytic continuation package.

Matches the schemas defined in laurent_pipeline_bundle/schemas/types.json
"""

from dataclasses import dataclass, field
from typing import List, Optional
import json


@dataclass
class Point:
    """A 2D point, used for both screen and logical coordinates."""
    x: float
    y: float
    index: Optional[int] = None

    def to_complex(self) -> complex:
        """Convert to complex number (x + iy)."""
        return complex(self.x, self.y)

    @classmethod
    def from_complex(cls, z: complex, index: Optional[int] = None) -> "Point":
        """Create from complex number."""
        return cls(x=z.real, y=z.imag, index=index)

    def to_dict(self) -> dict:
        d = {"x": self.x, "y": self.y}
        if self.index is not None:
            d["index"] = self.index
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Point":
        return cls(x=d["x"], y=d["y"], index=d.get("index"))


@dataclass
class Spline:
    """A sequence of points forming a spline or polyline."""
    points: List[Point]
    closed: bool = False

    def to_dict(self) -> dict:
        return {
            "points": [p.to_dict() for p in self.points],
            "closed": self.closed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Spline":
        return cls(
            points=[Point.from_dict(p) for p in d["points"]],
            closed=d.get("closed", False),
        )


@dataclass
class SplineParameters:
    """Parameters from a SplineExport."""
    tension: float = 0.5
    adaptiveTolerance: float = 3.0
    minDistance: float = 15.0

    def to_dict(self) -> dict:
        return {
            "tension": self.tension,
            "adaptiveTolerance": self.adaptiveTolerance,
            "minDistance": self.minDistance,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SplineParameters":
        return cls(
            tension=d.get("tension", 0.5),
            adaptiveTolerance=d.get("adaptiveTolerance", 3.0),
            minDistance=d.get("minDistance", 15.0),
        )


@dataclass
class SplineExport:
    """
    Full spline export structure matching the React frontend format.

    Contains control points, interpolated spline, and adaptive polyline.
    """
    version: str
    timestamp: str
    closed: bool
    parameters: SplineParameters
    controlPoints: List[Point]
    spline: List[Point] = field(default_factory=list)
    adaptivePolyline: List[Point] = field(default_factory=list)
    stats: Optional[dict] = None

    def get_polyline(self, prefer: str = "adaptive") -> List[Point]:
        """
        Get the best available polyline representation.

        Parameters
        ----------
        prefer : str
            Which representation to prefer: 'adaptive', 'spline', or 'control'

        Returns
        -------
        List[Point]
            The polyline points
        """
        if prefer == "adaptive" and self.adaptivePolyline:
            return self.adaptivePolyline
        elif prefer == "spline" and self.spline:
            return self.spline
        elif self.controlPoints:
            return self.controlPoints
        # Fallback chain
        return self.adaptivePolyline or self.spline or self.controlPoints

    def to_dict(self) -> dict:
        d = {
            "version": self.version,
            "timestamp": self.timestamp,
            "closed": self.closed,
            "parameters": self.parameters.to_dict(),
            "controlPoints": [p.to_dict() for p in self.controlPoints],
        }
        if self.spline:
            d["spline"] = [p.to_dict() for p in self.spline]
        if self.adaptivePolyline:
            d["adaptivePolyline"] = [p.to_dict() for p in self.adaptivePolyline]
        if self.stats:
            d["stats"] = self.stats
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SplineExport":
        return cls(
            version=d["version"],
            timestamp=d["timestamp"],
            closed=d["closed"],
            parameters=SplineParameters.from_dict(d["parameters"]),
            controlPoints=[Point.from_dict(p) for p in d["controlPoints"]],
            spline=[Point.from_dict(p) for p in d.get("spline", [])],
            adaptivePolyline=[Point.from_dict(p) for p in d.get("adaptivePolyline", [])],
            stats=d.get("stats"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "SplineExport":
        return cls.from_dict(json.loads(json_str))

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class Complex:
    """Complex number representation matching the schema."""
    re: float
    im: float

    def to_complex(self) -> complex:
        return complex(self.re, self.im)

    @classmethod
    def from_complex(cls, z: complex) -> "Complex":
        return cls(re=z.real, im=z.imag)

    def to_dict(self) -> dict:
        return {"re": self.re, "im": self.im}

    @classmethod
    def from_dict(cls, d: dict) -> "Complex":
        return cls(re=d["re"], im=d["im"])


@dataclass
class LaurentMap:
    """
    Laurent series map φ(ζ) = a₀ + Σₙ aₙζⁿ + Σₙ bₙζ⁻ⁿ

    Maps the unit circle to the curve boundary.
    """
    N: int  # Number of terms
    a0: Complex
    a: List[Complex]  # Positive power coefficients [a₁, a₂, ..., aₙ]
    b: List[Complex]  # Negative power coefficients [b₁, b₂, ..., bₙ]

    def to_dict(self) -> dict:
        return {
            "N": self.N,
            "a0": self.a0.to_dict(),
            "a": [c.to_dict() for c in self.a],
            "b": [c.to_dict() for c in self.b],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LaurentMap":
        return cls(
            N=d["N"],
            a0=Complex.from_dict(d["a0"]),
            a=[Complex.from_dict(c) for c in d["a"]],
            b=[Complex.from_dict(c) for c in d["b"]],
        )
