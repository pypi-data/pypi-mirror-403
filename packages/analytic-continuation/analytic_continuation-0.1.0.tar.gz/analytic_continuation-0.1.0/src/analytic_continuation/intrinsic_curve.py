"""
Intrinsic curve representations for complexity estimation.

Stores the natural log of the approximate bijection z(ζ) and converts to:
- Cesàro form: κ(s) - curvature as function of arc length
- Whewell form: φ(s) - tangent angle as function of arc length

These intrinsic representations enable better estimates of computational
complexity for the actual bijection work (inversion, evaluation).

Theory
------
For a conformal map z(ζ) from the unit disk, the composition with log
linearizes the multiplicative structure:

    w(ζ) = log(z(ζ))

On the unit circle ζ = e^{iθ}, the curve γ(θ) = z(e^{iθ}) has:

    Tangent:    T(θ) = z'(e^{iθ}) · i·e^{iθ} / |z'(e^{iθ})|
    Curvature:  κ(θ) = Im[z''(ζ) / z'(ζ)] / |z'(ζ)|  on |ζ|=1
    Arc length: s(θ) = ∫₀^θ |z'(e^{it})| dt

Complexity Indicators
--------------------
1. Total curvature: ∫|κ(s)|ds - measures total "bending"
2. Curvature variation: ∫|κ'(s)|ds - measures complexity of shape
3. Winding number: (1/2π)∫κ(s)ds = 1 for simple closed curves
4. Curvature peaks: max|κ(s)| - tight turns require finer sampling
5. Log-derivative oscillation: variation of arg(z'(ζ)) on |ζ|=1
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import json

from .laurent import LaurentMapResult


@dataclass
class CesaroRepresentation:
    """
    Cesàro intrinsic form: κ(s) - curvature as function of arc length.

    Attributes
    ----------
    arc_lengths : np.ndarray
        Cumulative arc length values s[i] at sample points
    curvatures : np.ndarray
        Curvature κ(s[i]) at each sample point
    total_arc_length : float
        Total perimeter L = s[-1]
    samples : int
        Number of sample points
    """

    arc_lengths: np.ndarray
    curvatures: np.ndarray
    total_arc_length: float
    samples: int

    def kappa_at(self, s: float) -> float:
        """Interpolate curvature at arc length s."""
        s_mod = s % self.total_arc_length
        idx = np.searchsorted(self.arc_lengths, s_mod)
        if idx == 0:
            return self.curvatures[0]
        if idx >= self.samples:
            return self.curvatures[-1]
        # Linear interpolation
        t = (s_mod - self.arc_lengths[idx - 1]) / (
            self.arc_lengths[idx] - self.arc_lengths[idx - 1]
        )
        return (1 - t) * self.curvatures[idx - 1] + t * self.curvatures[idx]

    def to_dict(self) -> dict:
        return {
            "arc_lengths": self.arc_lengths.tolist(),
            "curvatures": self.curvatures.tolist(),
            "total_arc_length": self.total_arc_length,
            "samples": self.samples,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CesaroRepresentation":
        return cls(
            arc_lengths=np.array(d["arc_lengths"]),
            curvatures=np.array(d["curvatures"]),
            total_arc_length=d["total_arc_length"],
            samples=d["samples"],
        )


@dataclass
class WhewellRepresentation:
    """
    Whewell intrinsic form: φ(s) - tangent angle as function of arc length.

    The tangent angle φ(s) = ∫₀ˢ κ(t) dt + φ₀

    Attributes
    ----------
    arc_lengths : np.ndarray
        Cumulative arc length values
    tangent_angles : np.ndarray
        Tangent angle φ(s[i]) at each sample point (radians)
    total_arc_length : float
        Total perimeter
    winding_number : float
        φ(L) - φ(0) = 2π·n for winding number n (should be 2π for simple curves)
    samples : int
        Number of sample points
    """

    arc_lengths: np.ndarray
    tangent_angles: np.ndarray
    total_arc_length: float
    winding_number: float
    samples: int

    def phi_at(self, s: float) -> float:
        """Interpolate tangent angle at arc length s."""
        # Handle winding for s > L
        winds, s_mod = divmod(s, self.total_arc_length)
        base_angle = winds * 2 * np.pi * self.winding_number

        idx = np.searchsorted(self.arc_lengths, s_mod)
        if idx == 0:
            return base_angle + self.tangent_angles[0]
        if idx >= self.samples:
            return base_angle + self.tangent_angles[-1]
        t = (s_mod - self.arc_lengths[idx - 1]) / (
            self.arc_lengths[idx] - self.arc_lengths[idx - 1]
        )
        return base_angle + (1 - t) * self.tangent_angles[idx - 1] + t * self.tangent_angles[idx]

    def to_dict(self) -> dict:
        return {
            "arc_lengths": self.arc_lengths.tolist(),
            "tangent_angles": self.tangent_angles.tolist(),
            "total_arc_length": self.total_arc_length,
            "winding_number": self.winding_number,
            "samples": self.samples,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WhewellRepresentation":
        return cls(
            arc_lengths=np.array(d["arc_lengths"]),
            tangent_angles=np.array(d["tangent_angles"]),
            total_arc_length=d["total_arc_length"],
            winding_number=d["winding_number"],
            samples=d["samples"],
        )


@dataclass
class LogBijectionData:
    """
    Natural log of the bijection z(ζ), storing both the original
    Laurent coefficients and derived intrinsic representations.

    Taking log linearizes the multiplicative structure:
        log(z(ζ)) = log|z| + i·arg(z)

    The derivative relationship:
        d/dζ[log(z(ζ))] = z'(ζ)/z(ζ)
    """

    # Original Laurent map (for reference)
    laurent_N: int
    laurent_a0: complex
    laurent_a: np.ndarray
    laurent_b: np.ndarray
    curve_scale: float

    # Log-transformed data on unit circle samples
    theta_samples: np.ndarray  # θ values on [0, 2π)
    log_z_samples: np.ndarray  # log(z(e^{iθ})) - branch chosen for continuity
    z_samples: np.ndarray  # z(e^{iθ}) - the curve itself

    # Derived quantities
    log_derivative_samples: np.ndarray  # z'(ζ)/z(ζ) on |ζ|=1

    def to_dict(self) -> dict:
        return {
            "laurent_N": self.laurent_N,
            "laurent_a0": {"re": self.laurent_a0.real, "im": self.laurent_a0.imag},
            "laurent_a": [{"re": c.real, "im": c.imag} for c in self.laurent_a],
            "laurent_b": [{"re": c.real, "im": c.imag} for c in self.laurent_b],
            "curve_scale": self.curve_scale,
            "theta_samples": self.theta_samples.tolist(),
            "log_z_samples": [{"re": c.real, "im": c.imag} for c in self.log_z_samples],
            "z_samples": [{"re": c.real, "im": c.imag} for c in self.z_samples],
            "log_derivative_samples": [
                {"re": c.real, "im": c.imag} for c in self.log_derivative_samples
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LogBijectionData":
        return cls(
            laurent_N=d["laurent_N"],
            laurent_a0=complex(d["laurent_a0"]["re"], d["laurent_a0"]["im"]),
            laurent_a=np.array([complex(c["re"], c["im"]) for c in d["laurent_a"]]),
            laurent_b=np.array([complex(c["re"], c["im"]) for c in d["laurent_b"]]),
            curve_scale=d["curve_scale"],
            theta_samples=np.array(d["theta_samples"]),
            log_z_samples=np.array([complex(c["re"], c["im"]) for c in d["log_z_samples"]]),
            z_samples=np.array([complex(c["re"], c["im"]) for c in d["z_samples"]]),
            log_derivative_samples=np.array(
                [complex(c["re"], c["im"]) for c in d["log_derivative_samples"]]
            ),
        )


@dataclass
class ComplexityEstimates:
    """
    Computational complexity estimates derived from intrinsic curve analysis.

    These predict the relative difficulty of:
    - Inverting z(ζ) = z_query (finding ζ given z)
    - Evaluating the continuation at many points
    - Achieving a target accuracy
    """

    # Curvature-based metrics
    total_curvature: float  # ∫|κ(s)|ds - total bending
    curvature_variation: float  # ∫|κ'(s)|ds - shape complexity
    max_curvature: float  # max|κ(s)| - sharpest turn
    mean_curvature: float  # (1/L)∫|κ(s)|ds
    curvature_std: float  # std deviation of |κ(s)|

    # Winding and topology
    winding_number: float  # Should be 1 for simple curves
    total_arc_length: float  # Perimeter L

    # Log-derivative metrics (measure conformal distortion)
    log_deriv_variation: float  # Var(log|z'(ζ)|) on |ζ|=1
    arg_deriv_variation: float  # Total variation of arg(z'(ζ))
    min_jacobian: float  # min|z'(ζ)| - worst stretching
    max_jacobian: float  # max|z'(ζ)| - worst compression
    jacobian_ratio: float  # max/min - condition number analog

    # Derived complexity scores
    inversion_difficulty: float  # Estimated relative cost of inversion
    sampling_density_factor: float  # Suggested sampling density multiplier
    newton_convergence_factor: float  # Expected Newton convergence rate factor

    def to_dict(self) -> dict:
        return {
            "total_curvature": self.total_curvature,
            "curvature_variation": self.curvature_variation,
            "max_curvature": self.max_curvature,
            "mean_curvature": self.mean_curvature,
            "curvature_std": self.curvature_std,
            "winding_number": self.winding_number,
            "total_arc_length": self.total_arc_length,
            "log_deriv_variation": self.log_deriv_variation,
            "arg_deriv_variation": self.arg_deriv_variation,
            "min_jacobian": self.min_jacobian,
            "max_jacobian": self.max_jacobian,
            "jacobian_ratio": self.jacobian_ratio,
            "inversion_difficulty": self.inversion_difficulty,
            "sampling_density_factor": self.sampling_density_factor,
            "newton_convergence_factor": self.newton_convergence_factor,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ComplexityEstimates":
        return cls(**d)

    def summary(self) -> str:
        """Human-readable summary of complexity estimates."""
        lines = [
            "=" * 50,
            "Bijection Complexity Analysis",
            "=" * 50,
            "",
            "Curvature Metrics:",
            f"  Total curvature:     {self.total_curvature:.4f}",
            f"  Curvature variation: {self.curvature_variation:.4f}",
            f"  Max curvature:       {self.max_curvature:.4f}",
            f"  Mean |κ|:            {self.mean_curvature:.4f}",
            f"  Std |κ|:             {self.curvature_std:.4f}",
            "",
            "Topology:",
            f"  Winding number:      {self.winding_number:.4f}",
            f"  Arc length:          {self.total_arc_length:.4f}",
            "",
            "Jacobian (Conformal Distortion):",
            f"  |z'| range:          [{self.min_jacobian:.4f}, {self.max_jacobian:.4f}]",
            f"  Condition ratio:     {self.jacobian_ratio:.4f}",
            f"  log|z'| variation:   {self.log_deriv_variation:.4f}",
            f"  arg(z') variation:   {self.arg_deriv_variation:.4f}",
            "",
            "Derived Complexity Scores:",
            f"  Inversion difficulty:    {self.inversion_difficulty:.2f}x baseline",
            f"  Sampling density factor: {self.sampling_density_factor:.2f}x",
            f"  Newton convergence:      {self.newton_convergence_factor:.2f}x expected iters",
            "=" * 50,
        ]
        return "\n".join(lines)


def compute_log_bijection(
    lmap: LaurentMapResult,
    curve_scale: float,
    samples: int = 4096,
) -> LogBijectionData:
    """
    Compute the natural log of the bijection z(ζ) on the unit circle.

    Uses continuous branch selection for log(z) to avoid discontinuities.

    Parameters
    ----------
    lmap : LaurentMapResult
        The fitted Laurent map
    curve_scale : float
        The diameter/scale of the curve
    samples : int
        Number of samples on the unit circle

    Returns
    -------
    LogBijectionData
        The log-transformed bijection data
    """
    theta = np.linspace(0, 2 * np.pi, samples, endpoint=False)
    zeta = np.exp(1j * theta)

    # Evaluate z(ζ) and z'(ζ) on unit circle
    z = lmap.eval_array(zeta)
    dz = lmap.deriv_array(zeta)

    # Compute log(z) with continuous branch
    # Start with principal branch and unwrap
    log_z = np.zeros(samples, dtype=complex)
    log_z[0] = np.log(z[0])  # Principal branch for first point

    for i in range(1, samples):
        # Use previous value to select branch
        log_candidate = np.log(z[i])
        # Adjust imaginary part to be continuous
        prev_im = log_z[i - 1].imag
        diff = log_candidate.imag - prev_im
        # Unwrap: if diff > π, subtract 2π; if diff < -π, add 2π
        n_wraps = round(diff / (2 * np.pi))
        log_z[i] = log_candidate - 2j * np.pi * n_wraps

    # Compute logarithmic derivative z'/z
    log_deriv = dz / z

    return LogBijectionData(
        laurent_N=lmap.N,
        laurent_a0=lmap.a0,
        laurent_a=lmap.a.copy(),
        laurent_b=lmap.b.copy(),
        curve_scale=curve_scale,
        theta_samples=theta,
        log_z_samples=log_z,
        z_samples=z,
        log_derivative_samples=log_deriv,
    )


def compute_cesaro_form(
    log_data: LogBijectionData,
) -> CesaroRepresentation:
    """
    Convert log bijection data to Cesàro form κ(s).

    The curvature for a parametric curve z(θ) is:
        κ = Im[z̄' · z''] / |z'|³

    where z' = dz/dθ.

    Parameters
    ----------
    log_data : LogBijectionData
        The log-transformed bijection data

    Returns
    -------
    CesaroRepresentation
        The Cesàro (curvature) representation
    """
    n = len(log_data.theta_samples)
    dtheta = 2 * np.pi / n
    z = log_data.z_samples

    # Compute derivatives using central differences
    # dz/dθ using periodic boundary
    dz_dtheta = np.zeros(n, dtype=complex)
    d2z_dtheta2 = np.zeros(n, dtype=complex)

    for i in range(n):
        i_prev = (i - 1) % n
        i_next = (i + 1) % n
        dz_dtheta[i] = (z[i_next] - z[i_prev]) / (2 * dtheta)
        d2z_dtheta2[i] = (z[i_next] - 2 * z[i] + z[i_prev]) / (dtheta * dtheta)

    # Compute |dz/dθ| for arc length differential
    speed = np.abs(dz_dtheta)

    # Curvature: κ = Im[conj(z') * z''] / |z'|³
    curvature = np.imag(np.conj(dz_dtheta) * d2z_dtheta2) / (speed**3 + 1e-15)

    # Compute cumulative arc length
    ds = speed * dtheta
    arc_lengths = np.zeros(n)
    arc_lengths[0] = 0
    for i in range(1, n):
        arc_lengths[i] = arc_lengths[i - 1] + ds[i - 1]

    total_arc_length = arc_lengths[-1] + ds[-1]  # Close the curve

    return CesaroRepresentation(
        arc_lengths=arc_lengths,
        curvatures=curvature,
        total_arc_length=total_arc_length,
        samples=n,
    )


def compute_whewell_form(
    cesaro: CesaroRepresentation,
    initial_angle: float = 0.0,
) -> WhewellRepresentation:
    """
    Convert Cesàro form to Whewell form φ(s) by integration.

    φ(s) = φ₀ + ∫₀ˢ κ(t) dt

    Parameters
    ----------
    cesaro : CesaroRepresentation
        The Cesàro (curvature) representation
    initial_angle : float
        Initial tangent angle φ(0)

    Returns
    -------
    WhewellRepresentation
        The Whewell (tangent angle) representation
    """
    n = cesaro.samples
    tangent_angles = np.zeros(n)
    tangent_angles[0] = initial_angle

    # Integrate curvature to get tangent angle
    for i in range(1, n):
        ds = cesaro.arc_lengths[i] - cesaro.arc_lengths[i - 1]
        # Trapezoidal rule
        kappa_avg = 0.5 * (cesaro.curvatures[i] + cesaro.curvatures[i - 1])
        tangent_angles[i] = tangent_angles[i - 1] + kappa_avg * ds

    # Compute winding number from total angle change
    # For a simple closed curve, should be 2π (winding number = 1)
    final_ds = cesaro.total_arc_length - cesaro.arc_lengths[-1]
    kappa_avg = 0.5 * (cesaro.curvatures[0] + cesaro.curvatures[-1])
    total_angle_change = tangent_angles[-1] + kappa_avg * final_ds - tangent_angles[0]
    winding_number = total_angle_change / (2 * np.pi)

    return WhewellRepresentation(
        arc_lengths=cesaro.arc_lengths,
        tangent_angles=tangent_angles,
        total_arc_length=cesaro.total_arc_length,
        winding_number=winding_number,
        samples=n,
    )


def estimate_complexity(
    log_data: LogBijectionData,
    cesaro: CesaroRepresentation,
    whewell: WhewellRepresentation,
) -> ComplexityEstimates:
    """
    Compute complexity estimates from intrinsic curve representations.

    The estimates predict computational costs for:
    - Newton iteration for inversion
    - Sampling density requirements
    - Overall pipeline complexity

    Parameters
    ----------
    log_data : LogBijectionData
        The log-transformed bijection
    cesaro : CesaroRepresentation
        The Cesàro representation
    whewell : WhewellRepresentation
        The Whewell representation

    Returns
    -------
    ComplexityEstimates
        The complexity analysis results
    """
    n = cesaro.samples
    L = cesaro.total_arc_length
    kappa = cesaro.curvatures

    # Curvature metrics
    abs_kappa = np.abs(kappa)
    total_curvature = np.trapezoid(abs_kappa, cesaro.arc_lengths)
    mean_curvature = total_curvature / L if L > 0 else 0
    max_curvature = np.max(abs_kappa)
    curvature_std = np.std(abs_kappa)

    # Curvature variation (total variation of κ)
    dkappa = np.diff(kappa)
    ds_intervals = np.diff(cesaro.arc_lengths)
    ds_intervals = np.where(ds_intervals > 1e-15, ds_intervals, 1e-15)
    kappa_deriv = np.abs(dkappa / ds_intervals)
    curvature_variation = np.sum(kappa_deriv * ds_intervals)

    # Jacobian (derivative magnitude) metrics
    zeta = np.exp(1j * log_data.theta_samples)
    dz = log_data.log_derivative_samples * log_data.z_samples  # z' = (z'/z) * z
    jacobian = np.abs(dz)

    min_jacobian = np.min(jacobian)
    max_jacobian = np.max(jacobian)
    jacobian_ratio = max_jacobian / min_jacobian if min_jacobian > 1e-15 else float("inf")

    # Log-derivative variation measures conformal distortion
    log_jacobian = np.log(jacobian + 1e-15)
    log_deriv_variation = np.max(log_jacobian) - np.min(log_jacobian)

    # Argument variation of z'
    arg_dz = np.angle(dz)
    # Unwrap to get total variation
    arg_dz_unwrapped = np.unwrap(arg_dz)
    arg_deriv_variation = np.max(arg_dz_unwrapped) - np.min(arg_dz_unwrapped)

    # === Derived Complexity Scores ===

    # Inversion difficulty scales with:
    # - Jacobian condition (ill-conditioned = harder Newton)
    # - Curvature variation (complex shape = more local minima)
    # - Max curvature (sharp turns = need finer initial grid)
    inversion_difficulty = (
        np.sqrt(jacobian_ratio)
        * (1 + 0.1 * curvature_variation / (2 * np.pi))
        * (1 + 0.05 * max_curvature * L / (2 * np.pi))
    )

    # Sampling density should increase with:
    # - Max curvature (sharp features need more samples)
    # - Curvature variation (complex shape)
    # - Jacobian ratio (variable speed parameterization)
    sampling_density_factor = (
        (1 + max_curvature * L / (4 * np.pi))
        * np.sqrt(1 + curvature_variation / (2 * np.pi))
        * np.sqrt(jacobian_ratio)
    )

    # Newton convergence factor (expected iterations multiplier)
    # Higher jacobian ratio = slower convergence
    # Higher curvature = more likely to need damping
    newton_convergence_factor = np.sqrt(jacobian_ratio) * (
        1 + 0.1 * max_curvature * L / (2 * np.pi)
    )

    return ComplexityEstimates(
        total_curvature=total_curvature,
        curvature_variation=curvature_variation,
        max_curvature=max_curvature,
        mean_curvature=mean_curvature,
        curvature_std=curvature_std,
        winding_number=whewell.winding_number,
        total_arc_length=L,
        log_deriv_variation=log_deriv_variation,
        arg_deriv_variation=arg_deriv_variation,
        min_jacobian=min_jacobian,
        max_jacobian=max_jacobian,
        jacobian_ratio=jacobian_ratio,
        inversion_difficulty=inversion_difficulty,
        sampling_density_factor=sampling_density_factor,
        newton_convergence_factor=newton_convergence_factor,
    )


@dataclass
class IntrinsicCurveAnalysis:
    """
    Complete intrinsic curve analysis of a bijection.

    Bundles together:
    - Log bijection data
    - Cesàro representation
    - Whewell representation
    - Complexity estimates
    """

    log_data: LogBijectionData
    cesaro: CesaroRepresentation
    whewell: WhewellRepresentation
    complexity: ComplexityEstimates

    def to_dict(self) -> dict:
        return {
            "log_data": self.log_data.to_dict(),
            "cesaro": self.cesaro.to_dict(),
            "whewell": self.whewell.to_dict(),
            "complexity": self.complexity.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "IntrinsicCurveAnalysis":
        return cls(
            log_data=LogBijectionData.from_dict(d["log_data"]),
            cesaro=CesaroRepresentation.from_dict(d["cesaro"]),
            whewell=WhewellRepresentation.from_dict(d["whewell"]),
            complexity=ComplexityEstimates.from_dict(d["complexity"]),
        )

    def summary(self) -> str:
        """Human-readable summary."""
        return self.complexity.summary()


def analyze_bijection(
    lmap: LaurentMapResult,
    curve_scale: float,
    samples: int = 4096,
) -> IntrinsicCurveAnalysis:
    """
    Perform complete intrinsic curve analysis of a Laurent bijection.

    This is the main entry point for complexity estimation.

    Parameters
    ----------
    lmap : LaurentMapResult
        The fitted Laurent map z(ζ)
    curve_scale : float
        The diameter/scale of the curve
    samples : int
        Number of samples for analysis

    Returns
    -------
    IntrinsicCurveAnalysis
        Complete analysis including Cesàro, Whewell, and complexity estimates

    Example
    -------
    >>> from analytic_continuation.laurent import fit_laurent_map
    >>> from analytic_continuation.intrinsic_curve import analyze_bijection
    >>>
    >>> # After fitting a Laurent map
    >>> result = fit_laurent_map(spline_export)
    >>> if result.ok:
    ...     analysis = analyze_bijection(result.laurent_map, result.curve_scale)
    ...     print(analysis.summary())
    ...
    ...     # Use complexity estimates to tune parameters
    ...     if analysis.complexity.inversion_difficulty > 2.0:
    ...         # Increase Newton iterations
    ...         pass
    """
    # Step 1: Compute log of bijection
    log_data = compute_log_bijection(lmap, curve_scale, samples)

    # Step 2: Convert to Cesàro form
    cesaro = compute_cesaro_form(log_data)

    # Step 3: Convert to Whewell form
    whewell = compute_whewell_form(cesaro)

    # Step 4: Estimate complexity
    complexity = estimate_complexity(log_data, cesaro, whewell)

    return IntrinsicCurveAnalysis(
        log_data=log_data,
        cesaro=cesaro,
        whewell=whewell,
        complexity=complexity,
    )


def suggest_inversion_config(
    complexity: ComplexityEstimates,
    base_theta_grid: int = 256,
    base_max_iters: int = 40,
) -> Dict[str, Any]:
    """
    Suggest inversion configuration based on complexity analysis.

    Parameters
    ----------
    complexity : ComplexityEstimates
        The complexity analysis
    base_theta_grid : int
        Base number of theta samples
    base_max_iters : int
        Base max Newton iterations

    Returns
    -------
    dict
        Suggested InvertConfig parameters
    """
    # Scale grid with sampling density factor
    theta_grid = int(base_theta_grid * complexity.sampling_density_factor)
    theta_grid = min(max(theta_grid, 128), 2048)  # Clamp to reasonable range

    # Scale iterations with Newton convergence factor
    max_iters = int(base_max_iters * complexity.newton_convergence_factor)
    max_iters = min(max(max_iters, 20), 200)

    # More backtracks if high jacobian ratio
    max_backtracks = 12
    if complexity.jacobian_ratio > 5:
        max_backtracks = 20
    if complexity.jacobian_ratio > 10:
        max_backtracks = 30

    return {
        "theta_grid": theta_grid,
        "max_iters": max_iters,
        "max_backtracks": max_backtracks,
        "damping": True,  # Always use damping for complex curves
        "estimated_cost_ratio": complexity.inversion_difficulty,
    }


# =============================================================================
# Quick Pre-Check for Raw User Contours (Stage 1 Gate)
# =============================================================================


@dataclass
class ContourPreCheckResult:
    """
    Result of quick pre-check on a raw user-drawn contour.

    This is a fast "fail early" gate before expensive Laurent fitting.
    """

    # Overall verdict
    ok: bool
    proceed: bool  # True = safe to continue, False = warn user or abort

    # Specific checks
    is_closed: bool
    is_simple: bool  # No self-intersections
    has_sufficient_points: bool
    has_reasonable_aspect: bool  # Not too thin/elongated
    has_reasonable_curvature: bool  # No extremely sharp turns

    # Metrics
    num_points: int
    perimeter: float
    bounding_box: Tuple[float, float, float, float]  # (x_min, y_min, x_max, y_max)
    aspect_ratio: float  # width/height or height/width, whichever > 1
    estimated_diameter: float
    min_segment_length: float
    max_segment_length: float
    max_turning_angle: float  # Maximum angle change between consecutive segments (radians)

    # Warnings and errors
    warnings: List[str]
    errors: List[str]

    # Estimated complexity (rough, before Laurent fitting)
    estimated_difficulty: str  # "easy", "moderate", "hard", "extreme", "infeasible"
    estimated_fit_time_seconds: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "proceed": self.proceed,
            "is_closed": self.is_closed,
            "is_simple": self.is_simple,
            "has_sufficient_points": self.has_sufficient_points,
            "has_reasonable_aspect": self.has_reasonable_aspect,
            "has_reasonable_curvature": self.has_reasonable_curvature,
            "num_points": self.num_points,
            "perimeter": self.perimeter,
            "bounding_box": list(self.bounding_box),
            "aspect_ratio": self.aspect_ratio,
            "estimated_diameter": self.estimated_diameter,
            "min_segment_length": self.min_segment_length,
            "max_segment_length": self.max_segment_length,
            "max_turning_angle": self.max_turning_angle,
            "warnings": self.warnings,
            "errors": self.errors,
            "estimated_difficulty": self.estimated_difficulty,
            "estimated_fit_time_seconds": self.estimated_fit_time_seconds,
        }


def _segments_intersect(
    p1: complex, p2: complex, p3: complex, p4: complex, eps: float = 1e-10
) -> bool:
    """Check if segment p1-p2 intersects p3-p4 (excluding endpoints)."""
    d1 = p2 - p1
    d2 = p4 - p3
    d3 = p3 - p1

    cross = d1.real * d2.imag - d1.imag * d2.real
    if abs(cross) < eps:
        return False  # Parallel

    t = (d3.real * d2.imag - d3.imag * d2.real) / cross
    s = (d3.real * d1.imag - d3.imag * d1.real) / cross

    return eps < t < 1 - eps and eps < s < 1 - eps


def _check_simple_polyline(
    points: List[complex], eps: float = 1e-10
) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """
    Check if a closed polyline is simple (non-self-intersecting).

    Returns (is_simple, first_intersection_indices or None).

    Detects:
    1. Segment-segment crossings (proper intersections)
    2. Near-coincident vertices (curve passes through same point twice)
    """
    n = len(points)
    if n < 4:
        return True, None

    # First check for near-coincident vertices (excluding adjacent)
    # This catches cases like figure-8 where curve passes through origin twice
    for i in range(n):
        for j in range(i + 2, n):
            # Skip adjacent vertices (including wrap-around)
            if i == 0 and j == n - 1:
                continue
            dist = abs(points[i] - points[j])
            # Use a relative tolerance based on typical segment length
            seg_len = abs(points[(i + 1) % n] - points[i])
            tol = max(eps, seg_len * 0.01)  # 1% of segment length or eps
            if dist < tol:
                return False, (i, j)

    # Then check for segment-segment crossings
    for i in range(n):
        p1, p2 = points[i], points[(i + 1) % n]
        # Check against non-adjacent segments
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue  # Adjacent when wrapping
            p3, p4 = points[j], points[(j + 1) % n]
            if _segments_intersect(p1, p2, p3, p4, eps):
                return False, (i, j)

    return True, None


def _compute_turning_angles(points: List[complex]) -> np.ndarray:
    """Compute turning angles at each vertex of a closed polyline."""
    n = len(points)
    angles = np.zeros(n)

    for i in range(n):
        p_prev = points[(i - 1) % n]
        p_curr = points[i]
        p_next = points[(i + 1) % n]

        v1 = p_curr - p_prev
        v2 = p_next - p_curr

        if abs(v1) < 1e-14 or abs(v2) < 1e-14:
            angles[i] = 0
            continue

        # Angle between vectors
        cos_angle = (v1.real * v2.real + v1.imag * v2.imag) / (abs(v1) * abs(v2))
        cos_angle = np.clip(cos_angle, -1, 1)
        angles[i] = np.arccos(cos_angle)

    return angles


def precheck_contour(
    points: List[Tuple[float, float]],
    closed: bool = True,
    min_points: int = 8,
    max_aspect_ratio: float = 20.0,
    max_turning_angle_deg: float = 170.0,
    min_segment_ratio: float = 0.001,  # min_segment / perimeter
) -> ContourPreCheckResult:
    """
    Quick pre-check on a raw user-drawn contour before Laurent fitting.

    This is a fast "fail early" gate at Stage 1 to catch obviously bad
    contours before wasting time on expensive computations.

    Parameters
    ----------
    points : List[Tuple[float, float]]
        The contour points (x, y) from user input or adaptive polyline
    closed : bool
        Whether the contour should be treated as closed
    min_points : int
        Minimum number of points required
    max_aspect_ratio : float
        Maximum allowed aspect ratio (rejects very thin curves)
    max_turning_angle_deg : float
        Maximum turning angle in degrees (rejects near-cusps)
    min_segment_ratio : float
        Minimum segment length as fraction of perimeter

    Returns
    -------
    ContourPreCheckResult
        Pre-check results with pass/fail and diagnostics
    """
    warnings = []
    errors = []

    # Convert to complex
    pts = [complex(p[0], p[1]) for p in points]
    n = len(pts)

    # Basic point count check
    has_sufficient_points = n >= min_points
    if not has_sufficient_points:
        errors.append(f"Too few points: {n} < {min_points} minimum")

    if n < 3:
        return ContourPreCheckResult(
            ok=False,
            proceed=False,
            is_closed=closed,
            is_simple=False,
            has_sufficient_points=False,
            has_reasonable_aspect=False,
            has_reasonable_curvature=False,
            num_points=n,
            perimeter=0,
            bounding_box=(0, 0, 0, 0),
            aspect_ratio=float("inf"),
            estimated_diameter=0,
            min_segment_length=0,
            max_segment_length=0,
            max_turning_angle=0,
            warnings=warnings,
            errors=["Need at least 3 points to form a contour"],
            estimated_difficulty="infeasible",
        )

    # Compute bounding box
    x_coords = [p.real for p in pts]
    y_coords = [p.imag for p in pts]
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    width = x_max - x_min
    height = y_max - y_min

    if width < 1e-10 or height < 1e-10:
        errors.append("Degenerate contour: zero width or height")
        return ContourPreCheckResult(
            ok=False,
            proceed=False,
            is_closed=closed,
            is_simple=False,
            has_sufficient_points=has_sufficient_points,
            has_reasonable_aspect=False,
            has_reasonable_curvature=False,
            num_points=n,
            perimeter=0,
            bounding_box=(x_min, y_min, x_max, y_max),
            aspect_ratio=float("inf"),
            estimated_diameter=0,
            min_segment_length=0,
            max_segment_length=0,
            max_turning_angle=0,
            warnings=warnings,
            errors=errors,
            estimated_difficulty="infeasible",
        )

    aspect_ratio = max(width / height, height / width)
    has_reasonable_aspect = aspect_ratio <= max_aspect_ratio
    if not has_reasonable_aspect:
        warnings.append(
            f"Very elongated contour: aspect ratio {aspect_ratio:.1f} > {max_aspect_ratio}"
        )

    # Compute perimeter and segment lengths
    segment_lengths = []
    for i in range(n):
        j = (i + 1) % n if closed else min(i + 1, n - 1)
        if i != j:
            segment_lengths.append(abs(pts[j] - pts[i]))

    perimeter = sum(segment_lengths)
    min_seg = min(segment_lengths) if segment_lengths else 0
    max_seg = max(segment_lengths) if segment_lengths else 0

    # Check for very short segments (relative to perimeter)
    if perimeter > 0 and min_seg / perimeter < min_segment_ratio:
        warnings.append(
            f"Very short segment detected: {min_seg:.2e} ({100 * min_seg / perimeter:.3f}% of perimeter)"
        )

    # Estimate diameter (max pairwise distance, sampled)
    diameter = 0
    step = max(1, n // 50)  # Sample ~50 points for speed
    for i in range(0, n, step):
        for j in range(i + step, n, step):
            d = abs(pts[i] - pts[j])
            if d > diameter:
                diameter = d

    # Check for self-intersections
    is_simple, intersection = _check_simple_polyline(pts)
    if not is_simple:
        errors.append(
            f"Self-intersection detected between segments {intersection[0]} and {intersection[1]}"
        )

    # Compute turning angles
    turning_angles = _compute_turning_angles(pts)
    max_turning = np.max(turning_angles)
    max_turning_threshold = np.radians(max_turning_angle_deg)
    has_reasonable_curvature = max_turning <= max_turning_threshold

    if not has_reasonable_curvature:
        warnings.append(
            f"Sharp turn detected: {np.degrees(max_turning):.1f}° (threshold: {max_turning_angle_deg}°)"
        )

    # Check closure
    if closed:
        closure_gap = abs(pts[-1] - pts[0])
        if closure_gap > perimeter * 0.01:
            warnings.append(f"Contour not fully closed: gap = {closure_gap:.4f}")

    # Estimate difficulty based on heuristics
    difficulty_score = 1.0

    # Aspect ratio penalty
    if aspect_ratio > 5:
        difficulty_score *= 1 + (aspect_ratio - 5) * 0.1

    # Sharp turns penalty
    sharp_turns = np.sum(turning_angles > np.radians(120))
    difficulty_score *= 1 + sharp_turns * 0.2

    # Self-intersection = infeasible
    if not is_simple:
        difficulty_score = float("inf")

    # Point density penalty (too few points for perimeter)
    points_per_unit = n / perimeter if perimeter > 0 else 0
    if points_per_unit < 0.1:
        difficulty_score *= 1.5
        warnings.append("Low point density - consider adding more control points")

    # Map score to difficulty level
    if difficulty_score == float("inf"):
        estimated_difficulty = "infeasible"
        estimated_time = None
    elif difficulty_score < 1.5:
        estimated_difficulty = "easy"
        estimated_time = 2.0
    elif difficulty_score < 3.0:
        estimated_difficulty = "moderate"
        estimated_time = 10.0
    elif difficulty_score < 6.0:
        estimated_difficulty = "hard"
        estimated_time = 60.0
    elif difficulty_score < 15.0:
        estimated_difficulty = "extreme"
        estimated_time = 300.0
    else:
        estimated_difficulty = "infeasible"
        estimated_time = None
        warnings.append("Contour complexity may result in very long computation times")

    # Overall verdict
    ok = len(errors) == 0
    proceed = ok and estimated_difficulty != "infeasible"

    return ContourPreCheckResult(
        ok=ok,
        proceed=proceed,
        is_closed=closed,
        is_simple=is_simple,
        has_sufficient_points=has_sufficient_points,
        has_reasonable_aspect=has_reasonable_aspect,
        has_reasonable_curvature=has_reasonable_curvature,
        num_points=n,
        perimeter=perimeter,
        bounding_box=(x_min, y_min, x_max, y_max),
        aspect_ratio=aspect_ratio,
        estimated_diameter=diameter,
        min_segment_length=min_seg,
        max_segment_length=max_seg,
        max_turning_angle=max_turning,
        warnings=warnings,
        errors=errors,
        estimated_difficulty=estimated_difficulty,
        estimated_fit_time_seconds=estimated_time,
    )


def precheck_contour_from_spline_export(
    control_points: List[Tuple[float, float]],
    adaptive_polyline: Optional[List[Tuple[float, float]]] = None,
    closed: bool = True,
) -> ContourPreCheckResult:
    """
    Pre-check a contour from SplineExport data.

    Uses adaptive polyline if available (more accurate), otherwise control points.

    Parameters
    ----------
    control_points : List[Tuple[float, float]]
        Control points from the spline
    adaptive_polyline : List[Tuple[float, float]], optional
        Adaptive polyline (if available, more accurate)
    closed : bool
        Whether the contour is closed

    Returns
    -------
    ContourPreCheckResult
    """
    # Prefer adaptive polyline if available and has enough points
    if adaptive_polyline and len(adaptive_polyline) >= len(control_points):
        return precheck_contour(adaptive_polyline, closed=closed)
    else:
        return precheck_contour(control_points, closed=closed)
