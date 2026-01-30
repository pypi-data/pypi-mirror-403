"""
Analytic continuation pipeline: Stages 4-6.

Stage 4: Check that f's poles are outside the annulus image
Stage 5: Invert z(ζ) = z_query to find ζ
Stage 6: Compute the composition A(f(B(z))) via shared parameterization
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict, Any

from .laurent import LaurentMapResult, LaurentFitConfig


@dataclass
class Pole:
    """A pole of the meromorphic function f."""
    z: complex
    multiplicity: int = 1


@dataclass
class HolomorphicCheckConfig:
    """Configuration for pole checking (Stage 4)."""
    theta_grid: int = 2048
    rho_samples: List[float] = field(default_factory=lambda: [0.97, 1.0, 1.03])
    pole_margin_factor: float = 1.0
    shrink_steps: List[float] = field(default_factory=lambda: [0.99, 0.985, 0.98, 0.975])

    @classmethod
    def from_pipeline_config(cls, cfg: dict) -> "HolomorphicCheckConfig":
        hc = cfg.get("fHolomorphicCheck", {})
        return cls(
            theta_grid=hc.get("theta_grid", 2048),
            rho_samples=hc.get("rho_samples", [0.97, 1.0, 1.03]),
            pole_margin_factor=hc.get("poleMarginFactor", 1.0),
            shrink_steps=hc.get("onFailure", {}).get("shrinkSteps", [0.99, 0.985, 0.98, 0.975]),
        )


@dataclass
class InvertConfig:
    """Configuration for map inversion (Stage 5)."""
    theta_grid: int = 256
    seed_radii: List[float] = field(default_factory=lambda: [0.99, 1.0, 1.01])
    max_iters: int = 40
    tol_abs_factor: float = 1e-10
    tol_rel_factor: float = 1e-10
    damping: bool = True
    max_backtracks: int = 12

    @classmethod
    def from_pipeline_config(cls, cfg: dict) -> "InvertConfig":
        inv = cfg.get("invertZ", {})
        init = inv.get("initStrategy", {})
        newton = inv.get("newton", {})
        return cls(
            theta_grid=init.get("theta_grid", 256),
            seed_radii=init.get("alsoSeedRadii", [0.99, 1.0, 1.01]),
            max_iters=newton.get("maxIters", 40),
            tol_abs_factor=newton.get("tolAbsFactor", 1e-10),
            tol_rel_factor=newton.get("tolRelFactor", 1e-10),
            damping=newton.get("damping", True),
            max_backtracks=newton.get("maxBacktracks", 12),
        )


@dataclass
class HolomorphicCheckResult:
    """Result of checking if f is holomorphic on annulus image."""
    ok: bool
    min_pole_distance: float
    closest_pole: Optional[complex] = None
    failure_reason: Optional[str] = None
    updated_rho_in: Optional[float] = None
    updated_rho_out: Optional[float] = None


@dataclass
class InvertResult:
    """Result of inverting z(ζ) = z_query."""
    converged: bool
    zeta: Optional[complex] = None
    residual: float = float('inf')
    iters: int = 0


@dataclass
class CompositionResult:
    """Result of computing the composition."""
    ok: bool
    value: Optional[complex] = None
    zeta: Optional[complex] = None
    residual: Optional[float] = None
    N: Optional[int] = None
    failure_reason: Optional[str] = None


def check_f_holomorphic_on_annulus(
    poles: List[Pole],
    lmap: LaurentMapResult,
    curve_scale: float,
    min_distance_param: float,
    cfg: Optional[HolomorphicCheckConfig] = None,
) -> HolomorphicCheckResult:
    """
    Stage 4: Check that f's poles are sufficiently far from the annulus image.

    Parameters
    ----------
    poles : List[Pole]
        The poles of the meromorphic function f
    lmap : LaurentMapResult
        The fitted Laurent map
    curve_scale : float
        The diameter of the curve (for scaling)
    min_distance_param : float
        The minDistance parameter from SplineExport (for pole margin)
    cfg : HolomorphicCheckConfig, optional
        Configuration

    Returns
    -------
    HolomorphicCheckResult
    """
    if cfg is None:
        cfg = HolomorphicCheckConfig()

    if not poles:
        return HolomorphicCheckResult(
            ok=True,
            min_pole_distance=float('inf'),
        )

    pole_margin = cfg.pole_margin_factor * min_distance_param

    # Sample the annulus image
    thetas = np.linspace(0, 2 * np.pi, cfg.theta_grid, endpoint=False)
    all_image_points = []

    for rho in cfg.rho_samples:
        zeta = rho * np.exp(1j * thetas)
        z = lmap.eval_array(zeta)
        all_image_points.extend(z)

    all_image_points = np.array(all_image_points)

    # Find minimum distance from any pole to the image
    min_dist = float('inf')
    closest_pole = None

    for pole in poles:
        distances = np.abs(all_image_points - pole.z)
        pole_min_dist = np.min(distances)
        if pole_min_dist < min_dist:
            min_dist = pole_min_dist
            closest_pole = pole.z

    if min_dist >= pole_margin:
        return HolomorphicCheckResult(
            ok=True,
            min_pole_distance=min_dist,
            closest_pole=closest_pole,
        )
    else:
        # Try shrinking the annulus
        for shrink in cfg.shrink_steps:
            # Shrink both rho_in and rho_out toward 1
            new_rho_in = 1 - shrink * (1 - cfg.rho_samples[0])
            new_rho_out = 1 + shrink * (cfg.rho_samples[-1] - 1)

            # Resample with shrunk annulus
            shrunk_rhos = [new_rho_in, 1.0, new_rho_out]
            all_shrunk = []
            for rho in shrunk_rhos:
                zeta = rho * np.exp(1j * thetas)
                z = lmap.eval_array(zeta)
                all_shrunk.extend(z)
            all_shrunk = np.array(all_shrunk)

            # Recheck distances
            shrunk_min_dist = float('inf')
            for pole in poles:
                distances = np.abs(all_shrunk - pole.z)
                pole_min_dist = np.min(distances)
                if pole_min_dist < shrunk_min_dist:
                    shrunk_min_dist = pole_min_dist

            if shrunk_min_dist >= pole_margin:
                return HolomorphicCheckResult(
                    ok=True,
                    min_pole_distance=shrunk_min_dist,
                    closest_pole=closest_pole,
                    updated_rho_in=new_rho_in,
                    updated_rho_out=new_rho_out,
                )

        return HolomorphicCheckResult(
            ok=False,
            min_pole_distance=min_dist,
            closest_pole=closest_pole,
            failure_reason=f"Pole at {closest_pole} is too close to curve (dist={min_dist:.6g}, margin={pole_margin:.6g})",
        )


def invert_z(
    z_query: complex,
    lmap: LaurentMapResult,
    curve_scale: float,
    cfg: Optional[InvertConfig] = None,
) -> InvertResult:
    """
    Stage 5: Invert z(ζ) = z_query using multi-start Newton iteration.

    Parameters
    ----------
    z_query : complex
        The point to invert
    lmap : LaurentMapResult
        The Laurent map
    curve_scale : float
        The diameter of the curve (for tolerance scaling)
    cfg : InvertConfig, optional
        Configuration

    Returns
    -------
    InvertResult
    """
    if cfg is None:
        cfg = InvertConfig()

    tol_abs = cfg.tol_abs_factor * curve_scale
    tol_rel = cfg.tol_rel_factor

    # Generate seed points
    thetas = np.linspace(0, 2 * np.pi, cfg.theta_grid, endpoint=False)
    seeds = []
    for r in cfg.seed_radii:
        for theta in thetas:
            seeds.append(r * np.exp(1j * theta))

    converged_roots = []

    for zeta0 in seeds:
        zeta = zeta0
        converged = False

        for it in range(cfg.max_iters):
            z = lmap.eval(zeta)
            residual = z - z_query

            if abs(residual) < tol_abs or abs(residual) < tol_rel * abs(z_query):
                converged = True
                break

            dz = lmap.deriv(zeta)
            if abs(dz) < 1e-14:
                break  # Singular derivative

            step = residual / dz

            if cfg.damping:
                # Backtracking line search
                alpha = 1.0
                for _ in range(cfg.max_backtracks):
                    zeta_new = zeta - alpha * step
                    z_new = lmap.eval(zeta_new)
                    if abs(z_new - z_query) < abs(residual):
                        break
                    alpha *= 0.5
                zeta = zeta_new
            else:
                zeta = zeta - step

        if converged:
            converged_roots.append((zeta, abs(lmap.eval(zeta) - z_query), it + 1))

    if not converged_roots:
        return InvertResult(converged=False)

    # Select root closest to unit circle
    best = min(converged_roots, key=lambda x: abs(abs(x[0]) - 1))
    return InvertResult(
        converged=True,
        zeta=best[0],
        residual=best[1],
        iters=best[2],
    )


def compute_composition(
    z_query: complex,
    f: Callable[[complex], complex],
    lmap: LaurentMapResult,
    curve_scale: float,
    invert_cfg: Optional[InvertConfig] = None,
) -> CompositionResult:
    """
    Stage 6: Compute A(f(B(z_query))) using the shared parameterization shortcut.

    Because reflections A and B are defined via the shared parameter ζ:
        B(z(ζ)) = z(1/conj(ζ))
        A(w(ζ)) = w(1/conj(ζ)) where w(ζ) = f(z(ζ))

    The composition simplifies:
        A(f(B(z(ζ)))) = f(z(ζ))

    So we just need to:
    1. Invert z_query to find ζ
    2. Return f(z(ζ)) = f(z_query) if ζ is on the unit circle

    Parameters
    ----------
    z_query : complex
        The query point
    f : Callable[[complex], complex]
        The meromorphic function to evaluate
    lmap : LaurentMapResult
        The Laurent map
    curve_scale : float
        The diameter of the curve
    invert_cfg : InvertConfig, optional
        Configuration for inversion

    Returns
    -------
    CompositionResult
    """
    # Step 1: Invert to find ζ
    inv = invert_z(z_query, lmap, curve_scale, invert_cfg)

    if not inv.converged:
        return CompositionResult(
            ok=False,
            failure_reason="Inversion did not converge",
        )

    # Step 2: Use the identity shortcut
    # A(f(B(z))) = f(z) when z is on the curve (ζ on unit circle)
    # More generally, f(z(ζ)) for the inverted ζ
    try:
        z_on_curve = lmap.eval(inv.zeta)
        value = f(z_on_curve)
    except Exception as e:
        return CompositionResult(
            ok=False,
            failure_reason=f"Function evaluation failed: {e}",
            zeta=inv.zeta,
            residual=inv.residual,
        )

    return CompositionResult(
        ok=True,
        value=value,
        zeta=inv.zeta,
        residual=inv.residual,
        N=lmap.N,
    )


def compute_continuation_grid(
    f: Callable[[complex], complex],
    lmap: LaurentMapResult,
    curve_scale: float,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    resolution: int,
    invert_cfg: Optional[InvertConfig] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the analytic continuation of f on a grid.

    Returns both the computed values and a mask indicating which points converged.

    Parameters
    ----------
    f : Callable
        The meromorphic function
    lmap : LaurentMapResult
        The Laurent map
    curve_scale : float
        Curve diameter for tolerance scaling
    x_range, y_range : Tuple[float, float]
        The range of the grid
    resolution : int
        Number of grid points per axis
    invert_cfg : InvertConfig, optional
        Inversion configuration

    Returns
    -------
    values : np.ndarray
        Complex array of shape (resolution, resolution) with computed values
    converged : np.ndarray
        Boolean array indicating which points converged
    """
    x = np.linspace(x_range[0], x_range[1], resolution)
    y = np.linspace(y_range[0], y_range[1], resolution)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y

    values = np.zeros_like(Z, dtype=complex)
    converged = np.zeros(Z.shape, dtype=bool)

    for i in range(resolution):
        for j in range(resolution):
            z_query = Z[i, j]
            result = compute_composition(z_query, f, lmap, curve_scale, invert_cfg)
            if result.ok and result.value is not None:
                values[i, j] = result.value
                converged[i, j] = True

    return values, converged
