"""
Laurent map fitting and evaluation for analytic continuation.

Implements Stage 3 of the pipeline: fitting z(ζ) so that the unit circle
maps to approximate a Jordan curve.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import json

from .types import Point, SplineExport, LaurentMap, Complex


@dataclass
class LaurentFitConfig:
    """Configuration for Laurent map fitting."""
    N_min: int = 6
    N_max: int = 64
    m_samples: int = 2048
    lambda_init: float = 1e-6
    lambda_increase_factor: float = 10.0
    max_lambda_tries: int = 6
    reparam_iters: int = 2
    theta_search_grid: int = 2048
    theta_refine_iters: int = 3
    fit_tol_max_factor: float = 0.002
    prefer_smallest_N: bool = True
    rho_in: float = 0.97
    rho_out: float = 1.03
    check_theta_grid: int = 4096
    min_abs_deriv_factor: float = 1e-8
    min_sep_factor: float = 1e-5
    poly_eps_factor: float = 0.0005

    @classmethod
    def from_pipeline_config(cls, cfg: dict) -> "LaurentFitConfig":
        """Create from pipeline_config.json structure."""
        fit_cfg = cfg.get("fitLaurentMap", {})
        deg = fit_cfg.get("degree", {})
        samp = fit_cfg.get("sampling", {})
        reg = fit_cfg.get("regularization", {})
        lam_auto = reg.get("lambdaAuto", {})
        reparam = fit_cfg.get("reparameterization", {})
        theta_search = reparam.get("thetaSearch", {})
        stopping = fit_cfg.get("stopping", {})
        checks = fit_cfg.get("checks", {})

        return cls(
            N_min=deg.get("N_min", 6),
            N_max=deg.get("N_max", 64),
            m_samples=samp.get("m_samples", 2048),
            lambda_init=lam_auto.get("lambda0Factor", 1e-6),
            lambda_increase_factor=lam_auto.get("increaseFactorOnFailure", 10.0),
            max_lambda_tries=lam_auto.get("maxTries", 6),
            reparam_iters=reparam.get("iters", 2),
            theta_search_grid=theta_search.get("grid", 2048),
            theta_refine_iters=theta_search.get("localRefineIters", 3),
            fit_tol_max_factor=stopping.get("fitTolMaxFactor", 0.002),
            prefer_smallest_N=stopping.get("preferSmallestN", True),
            rho_in=checks.get("rho_in", 0.97),
            rho_out=checks.get("rho_out", 1.03),
            check_theta_grid=checks.get("theta_grid", 4096),
            min_abs_deriv_factor=checks.get("minAbsDerivFactor", 1e-8),
            min_sep_factor=checks.get("minSepFactor", 1e-5),
            poly_eps_factor=checks.get("simplicity", {}).get("polyEpsFactor", 0.0005),
        )


@dataclass
class LaurentMapResult:
    """Result of Laurent map evaluation."""
    N: int
    a0: complex
    a: np.ndarray  # [a_1, ..., a_N]
    b: np.ndarray  # [b_1, ..., b_N]

    def eval(self, zeta: complex) -> complex:
        """Evaluate z(ζ) = a0 + Σ a_k ζ^k + Σ b_k ζ^{-k}."""
        z = self.a0
        p = zeta
        for k in range(self.N):
            z += self.a[k] * p
            p *= zeta
        q = 1.0 / zeta
        p = q
        for k in range(self.N):
            z += self.b[k] * p
            p *= q
        return z

    def eval_array(self, zeta: np.ndarray) -> np.ndarray:
        """Vectorized evaluation."""
        z = np.full_like(zeta, self.a0)
        p = zeta.copy()
        for k in range(self.N):
            z += self.a[k] * p
            p *= zeta
        q = 1.0 / zeta
        p = q.copy()
        for k in range(self.N):
            z += self.b[k] * p
            p *= q
        return z

    def deriv(self, zeta: complex) -> complex:
        """Evaluate z'(ζ) = Σ k a_k ζ^{k-1} - Σ k b_k ζ^{-k-1}."""
        dz = 0.0
        p = 1.0
        for k in range(self.N):
            dz += (k + 1) * self.a[k] * p
            p *= zeta
        q = 1.0 / zeta
        p = q * q
        for k in range(self.N):
            dz -= (k + 1) * self.b[k] * p
            p *= q
        return dz

    def deriv_array(self, zeta: np.ndarray) -> np.ndarray:
        """Vectorized derivative."""
        dz = np.zeros_like(zeta)
        p = np.ones_like(zeta)
        for k in range(self.N):
            dz += (k + 1) * self.a[k] * p
            p *= zeta
        q = 1.0 / zeta
        p = q * q
        for k in range(self.N):
            dz -= (k + 1) * self.b[k] * p
            p *= q
        return dz

    def to_laurent_map(self) -> LaurentMap:
        """Convert to serializable LaurentMap type."""
        return LaurentMap(
            N=self.N,
            a0=Complex.from_complex(self.a0),
            a=[Complex.from_complex(c) for c in self.a],
            b=[Complex.from_complex(c) for c in self.b],
        )

    @classmethod
    def from_laurent_map(cls, lm: LaurentMap) -> "LaurentMapResult":
        """Create from serializable LaurentMap type."""
        return cls(
            N=lm.N,
            a0=lm.a0.to_complex(),
            a=np.array([c.to_complex() for c in lm.a]),
            b=np.array([c.to_complex() for c in lm.b]),
        )


@dataclass
class FitResult:
    """Result of fitting a Laurent map."""
    ok: bool
    failure_reason: Optional[str] = None
    curve_scale: float = 0.0
    polyline_used: List[complex] = field(default_factory=list)
    laurent_map: Optional[LaurentMapResult] = None
    fit_max_err: float = float('inf')
    fit_rms_err: float = float('inf')
    simple_on_unit_circle: bool = False
    min_abs_deriv_unit: float = 0.0
    min_sep_unit: float = 0.0
    min_sep_in: float = 0.0
    min_sep_out: float = 0.0


def load_polyline_from_export(
    export: SplineExport,
    field_name: str = "adaptivePolyline",
    drop_duplicate_terminal: bool = True,
) -> List[complex]:
    """
    Load polyline from SplineExport, converting to complex.

    Parameters
    ----------
    export : SplineExport
        The spline export data
    field_name : str
        Which field to use: 'adaptivePolyline', 'spline', or 'controlPoints'
    drop_duplicate_terminal : bool
        If True, remove trailing points that duplicate the first point

    Returns
    -------
    List[complex]
        The polyline as complex numbers
    """
    if field_name == "adaptivePolyline":
        pts = export.adaptivePolyline
    elif field_name == "spline":
        pts = export.spline
    else:
        pts = export.controlPoints

    # Fall back if requested field is empty
    if not pts:
        pts = export.adaptivePolyline or export.spline or export.controlPoints

    poly = [complex(p.x, p.y) for p in pts]

    if drop_duplicate_terminal:
        while len(poly) >= 2 and abs(poly[-1] - poly[0]) < 1e-12:
            poly.pop()

    return poly


def estimate_diameter(poly: List[complex]) -> float:
    """Estimate curve diameter as max pairwise distance."""
    n = len(poly)
    dmax = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            d = abs(poly[i] - poly[j])
            if d > dmax:
                dmax = d
    return dmax


def resample_closed_polyline(poly: List[complex], m: int) -> np.ndarray:
    """
    Resample a closed polyline by arc length to m points.

    Returns array of m complex points, uniformly spaced by arc length.
    """
    n = len(poly)
    if n == 0:
        return np.array([], dtype=complex)

    # Compute cumulative arc length
    cum = [0.0]
    total = 0.0
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        seg = abs(b - a)
        total += seg
        cum.append(total)

    if total < 1e-14:
        return np.full(m, poly[0], dtype=complex)

    # Resample
    result = np.zeros(m, dtype=complex)
    for j in range(m):
        s = total * j / m
        # Binary search for segment
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if cum[mid] < s:
                lo = mid + 1
            else:
                hi = mid
        i = max(0, lo - 1)

        # Interpolate within segment
        seg_len = cum[i + 1] - cum[i]
        if seg_len > 1e-14:
            t = (s - cum[i]) / seg_len
        else:
            t = 0.0
        a = poly[i]
        b = poly[(i + 1) % n]
        result[j] = a + t * (b - a)

    return result


def build_laurent_matrix(thetas: np.ndarray, N: int) -> np.ndarray:
    """
    Build the design matrix for Laurent fitting.

    For m sample points and degree N, produces m x (1 + 2N) complex matrix.
    Column 0: constant term (1)
    Columns 1..N: positive powers ζ^1, ..., ζ^N
    Columns N+1..2N: negative powers ζ^{-1}, ..., ζ^{-N}
    """
    m = len(thetas)
    A = np.zeros((m, 1 + 2 * N), dtype=complex)
    zeta = np.exp(1j * thetas)

    A[:, 0] = 1.0

    # Positive powers
    p = zeta.copy()
    for k in range(N):
        A[:, 1 + k] = p
        p = p * zeta

    # Negative powers
    q = 1.0 / zeta
    p = q.copy()
    for k in range(N):
        A[:, 1 + N + k] = p
        p = p * q

    return A


def solve_tikhonov(
    A: np.ndarray,
    y: np.ndarray,
    N: int,
    lam: float,
) -> np.ndarray:
    """
    Solve regularized least squares with Tikhonov penalty.

    Penalty weights: k^2 on coefficients a_k, b_k (k=1..N), no penalty on a0.

    Uses real-valued formulation: stack real and imaginary parts.
    """
    m, n = A.shape  # n = 1 + 2*N

    # Build penalty weights: w[k] = sqrt(lambda) * k for k >= 1
    w = np.zeros(n)
    for k in range(1, N + 1):
        w[k] = np.sqrt(lam) * k          # a_k
        w[N + k] = np.sqrt(lam) * k      # b_k

    # Convert to real system: [Re(A); Im(A)] @ x = [Re(y); Im(y)]
    A_real = np.vstack([A.real, A.imag])
    y_real = np.hstack([y.real, y.imag])

    # Add regularization rows
    reg_rows = np.diag(w)
    A_aug = np.vstack([A_real, reg_rows])
    y_aug = np.hstack([y_real, np.zeros(n)])

    # Solve least squares
    c, _, _, _ = np.linalg.lstsq(A_aug, y_aug, rcond=None)

    return c


def check_polyline_simple(poly: np.ndarray, eps: float) -> bool:
    """
    Check if a closed polyline is simple (non-self-intersecting).

    Uses segment-segment intersection test with tolerance.
    """
    n = len(poly)
    if n < 4:
        return True

    def segments_intersect(p1, p2, p3, p4, eps):
        """Check if segment p1-p2 intersects p3-p4."""
        d1 = p2 - p1
        d2 = p4 - p3
        d3 = p3 - p1

        cross = d1.real * d2.imag - d1.imag * d2.real
        if abs(cross) < eps:
            return False  # Parallel

        t = (d3.real * d2.imag - d3.imag * d2.real) / cross
        s = (d3.real * d1.imag - d3.imag * d1.real) / cross

        return eps < t < 1 - eps and eps < s < 1 - eps

    # Check all non-adjacent segment pairs
    for i in range(n):
        p1, p2 = poly[i], poly[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue  # Adjacent (wrapping)
            p3, p4 = poly[j], poly[(j + 1) % n]
            if segments_intersect(p1, p2, p3, p4, eps):
                return False

    return True


def check_laurent_map(
    lmap: LaurentMapResult,
    rho_in: float,
    rho_out: float,
    theta_grid: int,
    min_abs_deriv: float,
    min_sep: float,
    poly_eps: float,
) -> Dict[str, Any]:
    """
    Check Laurent map quality on the annulus.

    Returns dict with:
    - simple_on_unit_circle: bool
    - min_abs_deriv_unit: float
    - min_sep_unit, min_sep_in, min_sep_out: float
    - ok: bool
    """
    thetas = np.linspace(0, 2 * np.pi, theta_grid, endpoint=False)

    # Sample on unit circle
    zeta_unit = np.exp(1j * thetas)
    z_unit = lmap.eval_array(zeta_unit)
    dz_unit = lmap.deriv_array(zeta_unit)

    # Check simplicity
    simple = check_polyline_simple(z_unit, poly_eps)

    # Min derivative magnitude on unit circle
    min_deriv = np.min(np.abs(dz_unit))

    # Min separation on each circle
    def min_separation(pts):
        n = len(pts)
        min_sep = float('inf')
        for i in range(n):
            d = abs(pts[(i + 1) % n] - pts[i])
            if d < min_sep:
                min_sep = d
        return min_sep

    sep_unit = min_separation(z_unit)

    # Inner circle
    zeta_in = rho_in * np.exp(1j * thetas)
    z_in = lmap.eval_array(zeta_in)
    sep_in = min_separation(z_in)

    # Outer circle
    zeta_out = rho_out * np.exp(1j * thetas)
    z_out = lmap.eval_array(zeta_out)
    sep_out = min_separation(z_out)

    ok = (
        simple and
        min_deriv >= min_abs_deriv and
        sep_unit >= min_sep and
        sep_in >= min_sep and
        sep_out >= min_sep
    )

    return {
        "ok": ok,
        "simple_on_unit_circle": simple,
        "min_abs_deriv_unit": min_deriv,
        "min_sep_unit": sep_unit,
        "min_sep_in": sep_in,
        "min_sep_out": sep_out,
    }


def reparam_closest_theta(
    lmap: LaurentMapResult,
    targets: np.ndarray,
    theta_grid: int,
    refine_iters: int,
) -> np.ndarray:
    """
    Reparameterize by finding closest theta for each target point.

    For each target z, find θ minimizing |z(e^{iθ}) - z|.
    """
    m = len(targets)
    thetas = np.zeros(m)

    # Coarse grid search
    grid = np.linspace(0, 2 * np.pi, theta_grid, endpoint=False)
    zeta_grid = np.exp(1j * grid)
    z_grid = lmap.eval_array(zeta_grid)

    for j in range(m):
        target = targets[j]

        # Find closest on grid
        dists = np.abs(z_grid - target)
        best_idx = np.argmin(dists)
        best_theta = grid[best_idx]

        # Local refinement (ternary-like search)
        delta = 2 * np.pi / theta_grid
        for _ in range(refine_iters):
            delta /= 3
            candidates = [best_theta - delta, best_theta, best_theta + delta]
            best_dist = float('inf')
            for th in candidates:
                z = lmap.eval(np.exp(1j * th))
                d = abs(z - target)
                if d < best_dist:
                    best_dist = d
                    best_theta = th

        thetas[j] = best_theta % (2 * np.pi)

    return thetas


def fit_laurent_map(
    export: SplineExport,
    cfg: Optional[LaurentFitConfig] = None,
) -> FitResult:
    """
    Fit a Laurent map to a SplineExport curve.

    This is the main entry point for Stage 3.

    Parameters
    ----------
    export : SplineExport
        The input curve data
    cfg : LaurentFitConfig, optional
        Configuration parameters

    Returns
    -------
    FitResult
        The fitting result including the Laurent map if successful
    """
    if cfg is None:
        cfg = LaurentFitConfig()

    # Load and prepare polyline
    poly = load_polyline_from_export(export)
    if len(poly) < 3:
        return FitResult(ok=False, failure_reason="Polyline too short")

    diameter = estimate_diameter(poly)
    if diameter < 1e-14:
        return FitResult(ok=False, failure_reason="Degenerate curve (zero diameter)")

    # Derive tolerances from diameter
    fit_tol_max = cfg.fit_tol_max_factor * diameter
    min_abs_deriv = cfg.min_abs_deriv_factor * diameter
    min_sep = cfg.min_sep_factor * diameter
    poly_eps = cfg.poly_eps_factor * diameter

    # Resample by arc length
    p = resample_closed_polyline(poly, cfg.m_samples)

    # Lambda scaling
    lam = cfg.lambda_init * diameter * diameter

    best_result: Optional[FitResult] = None

    for reg_try in range(cfg.max_lambda_tries):
        for N in range(cfg.N_min, cfg.N_max + 1):
            # Initialize uniform thetas
            thetas = np.linspace(0, 2 * np.pi, cfg.m_samples, endpoint=False)

            # Reparameterization iterations
            lmap = None
            for _ in range(cfg.reparam_iters):
                # Build matrix and solve
                A = build_laurent_matrix(thetas, N)
                coeffs = solve_tikhonov(A, p, N, lam)

                # Extract coefficients
                a0 = coeffs[0]
                a = coeffs[1:N + 1]
                b = coeffs[N + 1:2 * N + 1]

                lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)

                # Update thetas by closest point
                thetas = reparam_closest_theta(
                    lmap, p, cfg.theta_search_grid, cfg.theta_refine_iters
                )

            # Final solve with updated thetas
            A = build_laurent_matrix(thetas, N)
            coeffs = solve_tikhonov(A, p, N, lam)
            a0 = coeffs[0]
            a = coeffs[1:N + 1]
            b = coeffs[N + 1:2 * N + 1]
            lmap = LaurentMapResult(N=N, a0=a0, a=a, b=b)

            # Compute fit errors
            zeta_samples = np.exp(1j * thetas)
            z_fit = lmap.eval_array(zeta_samples)
            errors = np.abs(z_fit - p)
            max_err = np.max(errors)
            rms_err = np.sqrt(np.mean(errors ** 2))

            # Check map quality
            checks = check_laurent_map(
                lmap, cfg.rho_in, cfg.rho_out, cfg.check_theta_grid,
                min_abs_deriv, min_sep, poly_eps
            )

            if checks["ok"]:
                result = FitResult(
                    ok=True,
                    curve_scale=diameter,
                    polyline_used=list(poly),
                    laurent_map=lmap,
                    fit_max_err=max_err,
                    fit_rms_err=rms_err,
                    simple_on_unit_circle=checks["simple_on_unit_circle"],
                    min_abs_deriv_unit=checks["min_abs_deriv_unit"],
                    min_sep_unit=checks["min_sep_unit"],
                    min_sep_in=checks["min_sep_in"],
                    min_sep_out=checks["min_sep_out"],
                )

                # If fit is good enough and we prefer smallest N, return immediately
                if max_err <= fit_tol_max and cfg.prefer_smallest_N:
                    return result

                # Otherwise, record as best if better than previous
                if best_result is None or max_err < best_result.fit_max_err:
                    best_result = result

        # If we found any valid result, return the best
        if best_result is not None:
            return best_result

        # Increase regularization and retry
        lam *= cfg.lambda_increase_factor

    # All attempts failed
    return FitResult(ok=False, failure_reason="Failed to fit after max regularization tries")
