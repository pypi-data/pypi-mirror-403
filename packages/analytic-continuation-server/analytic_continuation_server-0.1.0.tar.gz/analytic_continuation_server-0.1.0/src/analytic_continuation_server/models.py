"""
Pydantic models for the Analytic Continuation Server API.

This module contains all request/response models organized by domain:
- Transform models: coordinate transformation requests
- Meromorphic models: function building from zeros/poles
- Laurent models: Laurent series fitting and inversion
- Session models: session management and progress tracking
- WebGL models: WebGL-friendly data formats for rendering
"""

from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


# =============================================================================
# Base Models
# =============================================================================


class PointModel(BaseModel):
    """A 2D point with optional index."""
    x: float
    y: float
    index: Optional[int] = None


class ComplexModel(BaseModel):
    """Complex number representation."""
    re: float
    im: float


class TransformParamsModel(BaseModel):
    """Transform parameters for screen/logical coordinate conversion."""
    offset_x: float = 0.0
    offset_y: float = 0.0
    scale_x: float = 1.0
    scale_y: Optional[float] = None  # None means uniform scaling


class ViewBoundsModel(BaseModel):
    """Define transform by screen size and logical view bounds."""
    screen_width: float
    screen_height: float
    logical_x_min: float
    logical_x_max: float
    logical_y_min: float
    logical_y_max: float
    uniform: bool = True


class SingularityModel(BaseModel):
    """A zero or pole location with optional multiplicity."""
    x: float
    y: float
    multiplicity: int = 1


# =============================================================================
# Spline Export Models
# =============================================================================


class SplineParametersModel(BaseModel):
    """Spline drawing parameters."""
    tension: float = 0.5
    adaptiveTolerance: float = 3.0
    minDistance: float = 15.0


class SplineExportModel(BaseModel):
    """Complete spline export data structure."""
    version: str
    timestamp: str
    closed: bool
    parameters: SplineParametersModel
    controlPoints: List[PointModel]
    spline: List[PointModel] = []
    adaptivePolyline: List[PointModel] = []
    stats: Optional[dict] = None


# =============================================================================
# Transform Request/Response Models
# =============================================================================


class TransformPointRequest(BaseModel):
    """Request to transform a single point."""
    point: PointModel
    params: TransformParamsModel
    direction: str = Field("to_logical", pattern="^(to_logical|to_screen)$")


class TransformPointsRequest(BaseModel):
    """Request to transform multiple points."""
    points: List[PointModel]
    params: TransformParamsModel
    direction: str = Field("to_logical", pattern="^(to_logical|to_screen)$")


class TransformSplineExportRequest(BaseModel):
    """Request to transform a full spline export."""
    export: SplineExportModel
    params: TransformParamsModel
    direction: str = Field("to_logical", pattern="^(to_logical|to_screen)$")


class ZoomRequest(BaseModel):
    """Request to apply zoom to transform parameters."""
    params: TransformParamsModel
    factor: float
    center_x: Optional[float] = None
    center_y: Optional[float] = None


class PanRequest(BaseModel):
    """Request to apply pan to transform parameters."""
    params: TransformParamsModel
    delta_x: float
    delta_y: float


# =============================================================================
# Domain Coloring Models
# =============================================================================


class DomainColorRequest(BaseModel):
    """Request for domain coloring image generation."""
    expression: str = Field(..., description="Complex function expression, e.g., 'z^2 + 1'")
    x_range: Tuple[float, float] = (-2.0, 2.0)
    y_range: Optional[Tuple[float, float]] = None
    resolution: int = Field(800, ge=100, le=4000)
    mode: str = Field("standard", pattern="^(standard|phase|modulus)$")
    mod_contours: bool = False
    arg_contours: bool = False
    show_legend: bool = True
    dark_theme: bool = True


class ValidationRenderRequest(BaseModel):
    """Request for validation render with zeros/poles overlay."""
    expression: str = Field(..., description="Complex function expression")
    zeros: List[SingularityModel] = []
    poles: List[SingularityModel] = []
    x_range: Tuple[float, float] = (-3.0, 3.0)
    y_range: Optional[Tuple[float, float]] = None
    resolution: int = Field(600, ge=100, le=2000)
    mod_contours: bool = False
    arg_contours: bool = False
    # Curve overlay
    curve_points: Optional[List[Dict[str, float]]] = None  # [{re, im}, ...]
    curve_color: str = "white"
    curve_width: float = 2.0
    # Axis ticks
    show_axis_ticks: bool = True
    tick_interval: float = 1.0


# =============================================================================
# Meromorphic Function Models
# =============================================================================


class MeromorphicRequest(BaseModel):
    """Request to build a meromorphic function from zeros and poles."""
    zeros: List[SingularityModel] = []
    poles: List[SingularityModel] = []
    params: Optional[TransformParamsModel] = None
    coords: str = Field("logical", pattern="^(logical|screen)$")


class MeromorphicResponse(BaseModel):
    """Response with the built expression and logical coordinates."""
    expression: str
    zeros: List[SingularityModel]
    poles: List[SingularityModel]


# =============================================================================
# Laurent Pipeline Models
# =============================================================================


class LaurentMapModel(BaseModel):
    """Serializable Laurent map."""
    N: int
    a0: ComplexModel
    a: List[ComplexModel]
    b: List[ComplexModel]


class LaurentFitRequest(BaseModel):
    """Request to fit a Laurent map."""
    export: SplineExportModel
    N_min: int = 6
    N_max: int = 64
    m_samples: int = 2048


class LaurentFitResponse(BaseModel):
    """Response from Laurent fitting."""
    ok: bool
    failure_reason: Optional[str] = None
    curve_scale: float = 0.0
    laurent_map: Optional[LaurentMapModel] = None
    fit_max_err: float = 0.0
    fit_rms_err: float = 0.0
    checks: dict = {}


class PoleModel(BaseModel):
    """A pole of a meromorphic function."""
    z_re: float
    z_im: float
    multiplicity: int = 1


class InvertRequest(BaseModel):
    """Request to invert a point through the Laurent map."""
    z_re: float
    z_im: float
    laurent_map: LaurentMapModel
    curve_scale: float


class InvertResponse(BaseModel):
    """Response from point inversion."""
    converged: bool
    zeta_re: Optional[float] = None
    zeta_im: Optional[float] = None
    residual: float = 0.0
    iters: int = 0


class HolomorphicCheckRequest(BaseModel):
    """Request to check if poles are outside annulus image."""
    poles: List[PoleModel]
    laurent_map: LaurentMapModel
    curve_scale: float
    min_distance_param: float


class HolomorphicCheckResponse(BaseModel):
    """Response from holomorphic check."""
    ok: bool
    min_pole_distance: float
    closest_pole_re: Optional[float] = None
    closest_pole_im: Optional[float] = None
    failure_reason: Optional[str] = None


class CompositionRequest(BaseModel):
    """Request to compute the analytic continuation composition."""
    z_re: float
    z_im: float
    expression: str
    laurent_map: LaurentMapModel
    curve_scale: float


class CompositionResponse(BaseModel):
    """Response from composition computation."""
    ok: bool
    value_re: Optional[float] = None
    value_im: Optional[float] = None
    zeta_re: Optional[float] = None
    zeta_im: Optional[float] = None
    residual: Optional[float] = None
    failure_reason: Optional[str] = None


# =============================================================================
# Contour Pre-Check Models
# =============================================================================


class ContourPreCheckRequest(BaseModel):
    """Request for quick pre-check on a raw user-drawn contour."""
    points: List[PointModel] = Field(
        ..., description="Contour points from user input or adaptive polyline"
    )
    closed: bool = Field(default=True, description="Whether the contour is closed")
    adaptive_polyline: Optional[List[PointModel]] = Field(
        None, description="Adaptive polyline (if available, more accurate)"
    )


class ContourPreCheckResponse(BaseModel):
    """Response from quick contour pre-check."""
    ok: bool = Field(..., description="True if no errors detected")
    proceed: bool = Field(..., description="True if safe to continue to Laurent fitting")
    is_closed: bool
    is_simple: bool = Field(..., description="No self-intersections")
    has_sufficient_points: bool
    has_reasonable_aspect: bool = Field(..., description="Not too thin/elongated")
    has_reasonable_curvature: bool = Field(..., description="No extremely sharp turns")
    num_points: int
    perimeter: float
    bounding_box: List[float] = Field(..., description="[x_min, y_min, x_max, y_max]")
    aspect_ratio: float = Field(..., description="width/height or height/width, whichever > 1")
    estimated_diameter: float
    min_segment_length: float
    max_segment_length: float
    max_turning_angle_degrees: float = Field(
        ..., description="Maximum angle change between segments"
    )
    warnings: List[str]
    errors: List[str]
    estimated_difficulty: str = Field(
        ..., description="easy, moderate, hard, extreme, or infeasible"
    )
    estimated_fit_time_seconds: Optional[float] = Field(
        None, description="Rough estimate of Laurent fitting time"
    )


# =============================================================================
# Intrinsic Curve Analysis Models
# =============================================================================


class IntrinsicCurveRequest(BaseModel):
    """Request for intrinsic curve analysis of a bijection."""
    laurent_map: LaurentMapModel
    curve_scale: float
    samples: int = Field(default=2048, ge=32, le=8192, description="Number of samples")


class CurvatureMetricsModel(BaseModel):
    """Curvature-based complexity metrics."""
    total_curvature: float = Field(..., description="Integral of |kappa(s)|ds")
    curvature_variation: float = Field(..., description="Integral of |kappa'(s)|ds")
    max_curvature: float = Field(..., description="max|kappa(s)|")
    mean_curvature: float = Field(..., description="(1/L) * integral of |kappa(s)|ds")
    curvature_std: float = Field(..., description="Standard deviation of |kappa(s)|")


class JacobianMetricsModel(BaseModel):
    """Jacobian (conformal distortion) metrics."""
    min_jacobian: float = Field(..., description="min|z'(zeta)|")
    max_jacobian: float = Field(..., description="max|z'(zeta)|")
    jacobian_ratio: float = Field(..., description="max/min - condition number analog")
    log_deriv_variation: float = Field(..., description="Variation of log|z'(zeta)|")
    arg_deriv_variation: float = Field(..., description="Total variation of arg(z'(zeta))")


class ComplexityScoresModel(BaseModel):
    """Derived complexity scores for computational cost estimation."""
    inversion_difficulty: float = Field(
        ..., description="Estimated relative cost of inversion (1.0 = baseline)"
    )
    sampling_density_factor: float = Field(
        ..., description="Suggested sampling density multiplier"
    )
    newton_convergence_factor: float = Field(
        ..., description="Expected Newton iterations multiplier"
    )


class SuggestedConfigModel(BaseModel):
    """Suggested inversion configuration based on complexity analysis."""
    theta_grid: int = Field(..., description="Suggested number of theta samples")
    max_iters: int = Field(..., description="Suggested max Newton iterations")
    max_backtracks: int = Field(..., description="Suggested max backtracking steps")
    damping: bool = Field(..., description="Whether to use damping")


class IntrinsicCurveResponse(BaseModel):
    """Response from intrinsic curve analysis."""
    winding_number: float = Field(..., description="Should be 1 for simple closed curves")
    total_arc_length: float = Field(..., description="Perimeter L")
    curvature: CurvatureMetricsModel
    jacobian: JacobianMetricsModel
    complexity: ComplexityScoresModel
    suggested_config: SuggestedConfigModel
    cesaro_arc_lengths: Optional[List[float]] = Field(None, description="Arc length samples")
    cesaro_curvatures: Optional[List[float]] = Field(None, description="Curvature samples")
    whewell_tangent_angles: Optional[List[float]] = Field(None, description="Tangent angle samples")
    summary: str = Field(..., description="Human-readable analysis summary")


# =============================================================================
# WebGL Render Data Models
# =============================================================================


class WebGLLaurentCoeffs(BaseModel):
    """Laurent coefficients formatted for WebGL shader consumption."""
    N: int
    coeffs_neg: List[List[float]]  # [[re, im], ...] for a_{-N} to a_{-1}
    coeffs_pos: List[List[float]]  # [[re, im], ...] for a_0 to a_N
    curve_scale: float


class ContinuationDefinition(BaseModel):
    """
    Complete definition of an analytic continuation.

    This captures everything needed to:
    1. Evaluate the continuation F(z) = A(f(B(z))) at any point
    2. Reconstruct the visualization
    3. Export/import the continuation
    """
    version: str = "1.0"
    laurent_map: WebGLLaurentCoeffs
    expression: Optional[str] = None
    zeros: List[Dict[str, float]] = []
    poles: List[Dict[str, float]] = []
    created_at: Optional[str] = None
    session_id: Optional[str] = None
    input_hash: Optional[str] = None
    fit_max_error: Optional[float] = None
    fit_rms_error: Optional[float] = None
    curve_point_count: Optional[int] = None
    curve_closed: bool = True

    def to_evaluation_info(self) -> Dict[str, Any]:
        """Return info needed to evaluate F(z) at a point."""
        return {
            "method": "schwarz_reflection_composition",
            "description": "F(z) = A(f(B(z))) where A,B are Schwarz reflections through the curve",
            "simplified": "Due to shared parameterization, F(z) = f(z(zeta)) where zeta = z^-1(z)",
            "laurent_map": {
                "N": self.laurent_map.N,
                "curve_scale": self.laurent_map.curve_scale,
                "evaluation": "z(zeta) = a_0 + sum_k a_k*zeta^k + sum_k b_k*zeta^-k",
            },
            "function": self.expression
            or f"rational with {len(self.zeros)} zeros, {len(self.poles)} poles",
        }


class WebGLRenderDataRequest(BaseModel):
    """Request for WebGL render data."""
    export: SplineExportModel
    zeros: List[SingularityModel] = []
    poles: List[SingularityModel] = []
    transform_params: Optional[TransformParamsModel] = None
    expression: Optional[str] = None
    N_min: int = 6
    N_max: int = 64


class WebGLRenderDataResponse(BaseModel):
    """Complete data needed for WebGL domain coloring of analytic continuation."""
    ok: bool
    failure_reason: Optional[str] = None
    laurent_coeffs: Optional[WebGLLaurentCoeffs] = None
    zeros: List[List[float]] = []  # [[re, im], ...]
    poles: List[List[float]] = []  # [[re, im], ...]
    expression: Optional[str] = None
    continuation: Optional[ContinuationDefinition] = None
    session_id: Optional[str] = None


class WebGLRenderWithProgressRequest(BaseModel):
    """Request for WebGL render data with progress tracking."""
    session_id: Optional[str] = None
    export: SplineExportModel
    zeros: List[SingularityModel] = []
    poles: List[SingularityModel] = []
    expression: Optional[str] = None
    transform_params: Optional[TransformParamsModel] = None
    N_min: int = 6
    N_max: int = 64
    auto_resume: bool = True


# =============================================================================
# Session Management Models
# =============================================================================


class SessionStartRequest(BaseModel):
    """Request to start a new pipeline session."""
    expression: Optional[str] = None
    curve_data: Optional[dict] = None
    zeros: List[SingularityModel] = []
    poles: List[SingularityModel] = []


class SessionResponse(BaseModel):
    """Response with session information."""
    session_id: str
    status: str
    created_at: str
    expression: Optional[str] = None


class CheckResumableRequest(BaseModel):
    """Request to check if a computation can be resumed from cache."""
    export: Optional[SplineExportModel] = None
    zeros: List[SingularityModel] = []
    poles: List[SingularityModel] = []
    expression: Optional[str] = None
