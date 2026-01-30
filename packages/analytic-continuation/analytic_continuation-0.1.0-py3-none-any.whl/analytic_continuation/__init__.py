"""
analytic_continuation - Coordinate transforms and Laurent series pipeline utilities.

Provides screen/logical space transformations for complex analysis visualizations,
and implements the Laurent/Schwarz-reflection analytic continuation pipeline.
"""

from .space_adapter import SpaceAdapter, TransformParams
from .types import Point, Spline, SplineExport, LaurentMap, Complex
from .meromorphic import (
    Singularity,
    MeromorphicBuilder,
    build_meromorphic_expression,
    meromorphic_from_points,
)
from .laurent import (
    LaurentFitConfig,
    LaurentMapResult,
    FitResult,
    fit_laurent_map,
    load_polyline_from_export,
    estimate_diameter,
)
from .continuation import (
    Pole,
    HolomorphicCheckConfig,
    InvertConfig,
    HolomorphicCheckResult,
    InvertResult,
    CompositionResult,
    check_f_holomorphic_on_annulus,
    invert_z,
    compute_composition,
    compute_continuation_grid,
)
from .logging_config import (
    PipelineLogger,
    TaskStatus,
    TaskProgress,
    PipelineSession,
    get_logger,
)
from .progress import (
    ProgressTracker,
    StageInfo,
    PIPELINE_STAGES,
    format_cli_progress,
)
from .intrinsic_curve import (
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
    # Quick pre-check for raw contours (Stage 1 gate)
    ContourPreCheckResult,
    precheck_contour,
    precheck_contour_from_spline_export,
)
from .schemas import (
    get_schema,
    get_config,
    get_example,
    validate,
    list_schemas,
    list_configs,
    list_examples,
    SchemaNotFoundError,
    ValidationError,
)

__version__ = "0.1.0"
__all__ = [
    # Space adapter
    "SpaceAdapter",
    "TransformParams",
    # Types
    "Point",
    "Spline",
    "SplineExport",
    "LaurentMap",
    "Complex",
    # Meromorphic builder
    "Singularity",
    "MeromorphicBuilder",
    "build_meromorphic_expression",
    "meromorphic_from_points",
    # Laurent fitting (Stage 3)
    "LaurentFitConfig",
    "LaurentMapResult",
    "FitResult",
    "fit_laurent_map",
    "load_polyline_from_export",
    "estimate_diameter",
    # Continuation pipeline (Stages 4-6)
    "Pole",
    "HolomorphicCheckConfig",
    "InvertConfig",
    "HolomorphicCheckResult",
    "InvertResult",
    "CompositionResult",
    "check_f_holomorphic_on_annulus",
    "invert_z",
    "compute_composition",
    "compute_continuation_grid",
    # Logging and progress
    "PipelineLogger",
    "TaskStatus",
    "TaskProgress",
    "PipelineSession",
    "get_logger",
    "ProgressTracker",
    "StageInfo",
    "PIPELINE_STAGES",
    "format_cli_progress",
    # Intrinsic curve analysis (Cesàro/Whewell)
    "CesaroRepresentation",
    "WhewellRepresentation",
    "LogBijectionData",
    "ComplexityEstimates",
    "IntrinsicCurveAnalysis",
    "analyze_bijection",
    "compute_log_bijection",
    "compute_cesaro_form",
    "compute_whewell_form",
    "estimate_complexity",
    "suggest_inversion_config",
    # Quick pre-check for raw contours (Stage 1 gate)
    "ContourPreCheckResult",
    "precheck_contour",
    "precheck_contour_from_spline_export",
    # Schema utilities
    "get_schema",
    "get_config",
    "get_example",
    "validate",
    "list_schemas",
    "list_configs",
    "list_examples",
    "SchemaNotFoundError",
    "ValidationError",
]
