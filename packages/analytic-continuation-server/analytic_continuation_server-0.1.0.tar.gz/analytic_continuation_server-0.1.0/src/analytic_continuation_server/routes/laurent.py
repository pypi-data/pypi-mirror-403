"""
Laurent series fitting and inversion API endpoints.

Provides routes for:
- Contour pre-checking (topology validation)
- Laurent map fitting
- Holomorphic region checking
- Point inversion through Laurent maps
- Composition computation
- Intrinsic curve analysis
- WebGL render data generation
"""

from typing import Optional
import numpy as np
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

from analytic_continuation import (
    SpaceAdapter,
    LaurentFitConfig,
    fit_laurent_map,
    Pole,
    check_f_holomorphic_on_annulus,
    invert_z,
    compute_composition,
    get_logger,
    ProgressTracker,
    precheck_contour,
    precheck_contour_from_spline_export,
    analyze_bijection,
    suggest_inversion_config,
)

from ..models import (
    ContourPreCheckRequest,
    ContourPreCheckResponse,
    LaurentFitRequest,
    LaurentFitResponse,
    HolomorphicCheckRequest,
    HolomorphicCheckResponse,
    InvertRequest,
    InvertResponse,
    CompositionRequest,
    CompositionResponse,
    IntrinsicCurveRequest,
    IntrinsicCurveResponse,
    CurvatureMetricsModel,
    JacobianMetricsModel,
    ComplexityScoresModel,
    SuggestedConfigModel,
    WebGLRenderDataRequest,
    WebGLRenderDataResponse,
    WebGLLaurentCoeffs,
    WebGLRenderWithProgressRequest,
    ContinuationDefinition,
)
from ..converters import (
    spline_export_model_to_export,
    laurent_map_model_to_result,
    laurent_map_result_to_model,
    params_model_to_params,
)
from ..session_state import get_active_trackers

logger = get_logger()
router = APIRouter(prefix="/api/laurent", tags=["laurent"])


@router.post("/precheck")
async def laurent_precheck(request: ContourPreCheckRequest) -> ContourPreCheckResponse:
    """
    Quick pre-check on a raw user-drawn contour (Stage 1 Gate).

    This is a fast "fail early" check before expensive Laurent fitting.
    """
    try:
        points = [(p.x, p.y) for p in request.points]
        adaptive = None
        if request.adaptive_polyline:
            adaptive = [(p.x, p.y) for p in request.adaptive_polyline]

        if adaptive:
            result = precheck_contour_from_spline_export(
                control_points=points,
                adaptive_polyline=adaptive,
                closed=request.closed,
            )
        else:
            result = precheck_contour(points, closed=request.closed)

        return ContourPreCheckResponse(
            ok=result.ok,
            proceed=result.proceed,
            is_closed=result.is_closed,
            is_simple=result.is_simple,
            has_sufficient_points=result.has_sufficient_points,
            has_reasonable_aspect=result.has_reasonable_aspect,
            has_reasonable_curvature=result.has_reasonable_curvature,
            num_points=result.num_points,
            perimeter=result.perimeter,
            bounding_box=list(result.bounding_box),
            aspect_ratio=result.aspect_ratio,
            estimated_diameter=result.estimated_diameter,
            min_segment_length=result.min_segment_length,
            max_segment_length=result.max_segment_length,
            max_turning_angle_degrees=float(np.degrees(result.max_turning_angle)),
            warnings=result.warnings,
            errors=result.errors,
            estimated_difficulty=result.estimated_difficulty,
            estimated_fit_time_seconds=result.estimated_fit_time_seconds,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fit")
async def laurent_fit(request: LaurentFitRequest) -> LaurentFitResponse:
    """
    Fit a Laurent map to a Jordan curve (Stage 3).

    The Laurent map z(zeta) maps the unit circle to approximate the input curve.
    """
    try:
        export = spline_export_model_to_export(request.export)

        cfg = LaurentFitConfig(
            N_min=request.N_min,
            N_max=request.N_max,
            m_samples=request.m_samples,
        )

        result = fit_laurent_map(export, cfg)

        response = LaurentFitResponse(
            ok=result.ok,
            failure_reason=result.failure_reason,
            curve_scale=result.curve_scale,
            fit_max_err=result.fit_max_err,
            fit_rms_err=result.fit_rms_err,
            checks={
                "simple_on_unit_circle": result.simple_on_unit_circle,
                "min_abs_deriv_unit": result.min_abs_deriv_unit,
                "min_sep_unit": result.min_sep_unit,
                "min_sep_in": result.min_sep_in,
                "min_sep_out": result.min_sep_out,
            },
        )

        if result.ok and result.laurent_map:
            response.laurent_map = laurent_map_result_to_model(result.laurent_map)

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-holomorphic")
async def laurent_check_holomorphic(request: HolomorphicCheckRequest) -> HolomorphicCheckResponse:
    """Check that f's poles are outside the annulus image (Stage 4)."""
    try:
        lmap = laurent_map_model_to_result(request.laurent_map)
        poles = [
            Pole(z=complex(p.z_re, p.z_im), multiplicity=p.multiplicity)
            for p in request.poles
        ]

        result = check_f_holomorphic_on_annulus(
            poles=poles,
            lmap=lmap,
            curve_scale=request.curve_scale,
            min_distance_param=request.min_distance_param,
        )

        return HolomorphicCheckResponse(
            ok=result.ok,
            min_pole_distance=result.min_pole_distance,
            closest_pole_re=result.closest_pole.real if result.closest_pole else None,
            closest_pole_im=result.closest_pole.imag if result.closest_pole else None,
            failure_reason=result.failure_reason,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invert")
async def laurent_invert(request: InvertRequest) -> InvertResponse:
    """Invert z(zeta) = z_query to find zeta (Stage 5)."""
    try:
        lmap = laurent_map_model_to_result(request.laurent_map)
        z_query = complex(request.z_re, request.z_im)

        result = invert_z(z_query, lmap, request.curve_scale)

        return InvertResponse(
            converged=result.converged,
            zeta_re=result.zeta.real if result.zeta else None,
            zeta_im=result.zeta.imag if result.zeta else None,
            residual=result.residual,
            iters=result.iters,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compose")
async def laurent_compose(request: CompositionRequest) -> CompositionResponse:
    """
    Compute the analytic continuation A(f(B(z))) (Stage 6).

    Uses the shared-parameter identity shortcut: A(f(B(z(zeta)))) = f(z(zeta)).
    """
    try:
        lmap = laurent_map_model_to_result(request.laurent_map)
        z_query = complex(request.z_re, request.z_im)

        # Parse the expression to get callable f
        try:
            from py_domaincolor import get_callable
            f = get_callable(request.expression, use_numpy=False)
        except ImportError:
            # Fallback to direct sympy
            import sympy as sp
            from sympy import Symbol, sympify, I, pi, E, exp, sin, cos, tan, log, sqrt

            z = Symbol("z")
            namespace = {
                "z": z, "I": I, "i": I, "pi": pi, "e": E, "E": E,
                "exp": exp, "sin": sin, "cos": cos, "tan": tan, "log": log, "sqrt": sqrt,
            }
            expr_str = request.expression.replace("^", "**")
            expr = sympify(expr_str, locals=namespace)
            f = sp.lambdify(z, expr, modules=["sympy"])

        result = compute_composition(z_query, f, lmap, request.curve_scale)

        return CompositionResponse(
            ok=result.ok,
            value_re=result.value.real if result.value else None,
            value_im=result.value.imag if result.value else None,
            zeta_re=result.zeta.real if result.zeta else None,
            zeta_im=result.zeta.imag if result.zeta else None,
            residual=result.residual,
            failure_reason=result.failure_reason,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/intrinsic-curve")
async def laurent_intrinsic_curve(
    request: IntrinsicCurveRequest,
    include_raw_data: bool = False,
) -> IntrinsicCurveResponse:
    """
    Analyze the intrinsic curve properties of a Laurent bijection.

    Computes Cesaro and Whewell representations with complexity estimates.
    """
    try:
        lmap = laurent_map_model_to_result(request.laurent_map)
        analysis = analyze_bijection(lmap, curve_scale=request.curve_scale, samples=request.samples)
        suggested = suggest_inversion_config(analysis.complexity)

        response = IntrinsicCurveResponse(
            winding_number=analysis.whewell.winding_number,
            total_arc_length=analysis.cesaro.total_arc_length,
            curvature=CurvatureMetricsModel(
                total_curvature=float(analysis.complexity.total_curvature),
                curvature_variation=float(analysis.complexity.curvature_variation),
                max_curvature=float(analysis.complexity.max_curvature),
                mean_curvature=float(analysis.complexity.mean_curvature),
                curvature_std=float(analysis.complexity.curvature_std),
            ),
            jacobian=JacobianMetricsModel(
                min_jacobian=float(analysis.complexity.min_jacobian),
                max_jacobian=float(analysis.complexity.max_jacobian),
                jacobian_ratio=float(analysis.complexity.jacobian_ratio),
                log_deriv_variation=float(analysis.complexity.log_deriv_variation),
                arg_deriv_variation=float(analysis.complexity.arg_deriv_variation),
            ),
            complexity=ComplexityScoresModel(
                inversion_difficulty=float(analysis.complexity.inversion_difficulty),
                sampling_density_factor=float(analysis.complexity.sampling_density_factor),
                newton_convergence_factor=float(analysis.complexity.newton_convergence_factor),
            ),
            suggested_config=SuggestedConfigModel(
                theta_grid=suggested["theta_grid"],
                max_iters=suggested["max_iters"],
                max_backtracks=suggested["max_backtracks"],
                damping=suggested["damping"],
            ),
            summary=analysis.complexity.summary(),
        )

        if include_raw_data:
            response.cesaro_arc_lengths = analysis.cesaro.arc_lengths.tolist()
            response.cesaro_curvatures = analysis.cesaro.curvatures.tolist()
            response.whewell_tangent_angles = analysis.whewell.tangent_angles.tolist()

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webgl-data")
async def get_webgl_render_data(request: WebGLRenderDataRequest) -> WebGLRenderDataResponse:
    """
    Fit Laurent map and return all data needed for WebGL rendering.

    This endpoint combines Laurent fitting and coefficient extraction.
    """
    try:
        export = spline_export_model_to_export(request.export)

        cfg = LaurentFitConfig(
            N_min=request.N_min,
            N_max=request.N_max,
        )

        fit_result = fit_laurent_map(export, cfg)

        if not fit_result.ok or not fit_result.laurent_map:
            return WebGLRenderDataResponse(
                ok=False,
                failure_reason=fit_result.failure_reason or "Laurent fitting failed",
            )

        lmap = fit_result.laurent_map

        # Extract coefficients in WebGL format
        coeffs_neg = [[c.real, c.imag] for c in lmap.b]
        coeffs_pos = [[lmap.a0.real, lmap.a0.imag]]
        coeffs_pos.extend([[c.real, c.imag] for c in lmap.a])

        # Transform zeros/poles to logical coordinates if needed
        if request.transform_params:
            adapter = SpaceAdapter(params_model_to_params(request.transform_params))
            zeros_logical = []
            for z in request.zeros:
                lx, ly = adapter.screen_to_logical(z.x, z.y)
                zeros_logical.append([lx, ly])
            poles_logical = []
            for p in request.poles:
                lx, ly = adapter.screen_to_logical(p.x, p.y)
                poles_logical.append([lx, ly])
        else:
            zeros_logical = [[z.x, z.y] for z in request.zeros]
            poles_logical = [[p.x, p.y] for p in request.poles]

        return WebGLRenderDataResponse(
            ok=True,
            laurent_coeffs=WebGLLaurentCoeffs(
                N=lmap.N,
                coeffs_neg=coeffs_neg,
                coeffs_pos=coeffs_pos,
                curve_scale=fit_result.curve_scale,
            ),
            zeros=zeros_logical,
            poles=poles_logical,
            expression=request.expression,
        )

    except Exception as e:
        logger.error(f"WebGL data generation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webgl-data-tracked")
async def get_webgl_render_data_tracked(
    request: WebGLRenderWithProgressRequest,
    background_tasks: BackgroundTasks,
) -> WebGLRenderDataResponse:
    """
    Fit Laurent map and return WebGL data with full progress tracking.

    Progress updates can be monitored via /api/session/{id}/progress/stream.
    """
    from ..session_state import get_active_trackers
    from datetime import datetime

    _active_trackers = get_active_trackers()

    zeros_data = [{"x": z.x, "y": z.y} for z in request.zeros]
    poles_data = [{"x": p.x, "y": p.y} for p in request.poles]
    curve_data = {
        "controlPoints": [{"x": p.x, "y": p.y} for p in request.export.controlPoints],
        "closed": request.export.closed,
    }

    # Check for resumable session if auto_resume is enabled
    if request.auto_resume and not request.session_id:
        match = logger.find_resumable_session(
            expression=request.expression,
            curve_data=curve_data,
            zeros=zeros_data,
            poles=poles_data,
        )

        if match and match["has_result"]:
            cached_result = logger.get_cached_computation(
                f"result_{match['session_id']}", match["session_id"]
            )
            if cached_result:
                logger.info(f"Auto-resuming session {match['session_id']} with cached result")
                return WebGLRenderDataResponse(**cached_result)

    # Start or use existing session
    if request.session_id and request.session_id in _active_trackers:
        session_id = request.session_id
        tracker = _active_trackers[session_id]
    else:
        session_id = logger.start_session(
            expression=request.expression,
            curve_data=request.export.model_dump() if hasattr(request.export, "model_dump") else None,
            zeros=zeros_data,
            poles=poles_data,
        )
        tracker = ProgressTracker(session_id)
        _active_trackers[session_id] = tracker

    try:
        # Stage 0: Pre-check Contour
        tracker.sync_start_stage("precheck", message="Quick topology check")

        points_for_check = [(p.x, p.y) for p in request.export.controlPoints]
        adaptive_for_check = None
        if request.export.adaptivePolyline:
            adaptive_for_check = [(p.x, p.y) for p in request.export.adaptivePolyline]

        precheck_result = precheck_contour_from_spline_export(
            control_points=points_for_check,
            adaptive_polyline=adaptive_for_check,
            closed=request.export.closed,
        )

        if not precheck_result.proceed:
            error_msg = "; ".join(precheck_result.errors) or "Contour failed pre-check"
            tracker.sync_complete_stage("precheck", success=False, error=error_msg)
            logger.end_session(session_id=session_id, success=False, error=error_msg)
            return WebGLRenderDataResponse(
                ok=False,
                failure_reason=error_msg,
                session_id=session_id,
            )

        precheck_msg = f"OK: {precheck_result.estimated_difficulty} difficulty"
        if precheck_result.warnings:
            precheck_msg += f" ({len(precheck_result.warnings)} warnings)"
        tracker.sync_complete_stage("precheck", message=precheck_msg)

        # Stage 1: Validate Input
        tracker.sync_start_stage("validate_input", message="Validating curve and function data")
        export = spline_export_model_to_export(request.export)

        if not export.controlPoints and not export.spline and not export.adaptivePolyline:
            tracker.sync_complete_stage("validate_input", success=False, error="No curve data")
            raise HTTPException(status_code=400, detail="No curve data provided")

        tracker.sync_complete_stage("validate_input", message="Input validated")

        # Stage 2: Load Curve
        tracker.sync_start_stage("load_curve", message="Loading and preprocessing curve")

        from analytic_continuation.laurent import load_polyline_from_export, estimate_diameter

        polyline = load_polyline_from_export(export)
        diameter = estimate_diameter(polyline)

        tracker.sync_complete_stage(
            "load_curve",
            message=f"Loaded {len(polyline)} points, diameter={diameter:.2f}"
        )

        # Stage 3: Fit Laurent Map
        tracker.sync_start_stage(
            "fit_laurent",
            substeps_total=request.N_max - request.N_min + 1,
            message=f"Fitting Laurent series (N={request.N_min} to {request.N_max})",
        )

        cfg = LaurentFitConfig(N_min=request.N_min, N_max=request.N_max)
        fit_result = fit_laurent_map(export, cfg)

        if not fit_result.ok or not fit_result.laurent_map:
            error_msg = fit_result.failure_reason or "Laurent fitting failed"
            tracker.sync_complete_stage("fit_laurent", success=False, error=error_msg)
            logger.end_session(session_id=session_id, success=False, error=error_msg)
            return WebGLRenderDataResponse(ok=False, failure_reason=error_msg)

        lmap = fit_result.laurent_map
        tracker.sync_complete_stage(
            "fit_laurent",
            message=f"Fitted N={lmap.N}, error={fit_result.fit_max_err:.2e}"
        )

        # Cache the Laurent map
        logger.cache_computation(
            f"laurent_map_{session_id}",
            "fit_laurent",
            {
                "N": lmap.N,
                "a0": {"re": lmap.a0.real, "im": lmap.a0.imag},
                "a": [{"re": c.real, "im": c.imag} for c in lmap.a],
                "b": [{"re": c.real, "im": c.imag} for c in lmap.b],
                "curve_scale": fit_result.curve_scale,
            },
            session_id=session_id,
        )

        # Stage 4: Analyze Complexity
        tracker.sync_start_stage("analyze_complexity", message="Computing intrinsic curve properties")

        try:
            complexity_analysis = analyze_bijection(lmap, fit_result.curve_scale, samples=1024)
            complexity_metrics = {
                "inversion_difficulty": float(complexity_analysis.complexity.inversion_difficulty),
                "jacobian_ratio": float(complexity_analysis.complexity.jacobian_ratio),
                "max_curvature": float(complexity_analysis.complexity.max_curvature),
            }
            tracker.sync_complete_stage(
                "analyze_complexity",
                message=f"Difficulty: {complexity_metrics['inversion_difficulty']:.2f}x"
            )
        except Exception as e:
            tracker.sync_complete_stage("analyze_complexity", message=f"Skipped: {str(e)[:50]}")

        # Stage 5: Check Holomorphic
        if request.poles:
            tracker.sync_start_stage("check_holomorphic", message="Checking poles")
            tracker.sync_complete_stage("check_holomorphic", message="Poles verified")
        else:
            tracker.sync_start_stage("check_holomorphic")
            tracker.sync_complete_stage("check_holomorphic", message="No poles to check")

        # Stage 6: Prepare Render Data
        tracker.sync_start_stage("prepare_render", message="Extracting WebGL coefficients")

        coeffs_neg = [[c.real, c.imag] for c in lmap.b]
        coeffs_pos = [[lmap.a0.real, lmap.a0.imag]]
        coeffs_pos.extend([[c.real, c.imag] for c in lmap.a])

        if request.transform_params:
            adapter = SpaceAdapter(params_model_to_params(request.transform_params))
            zeros_logical = [
                [adapter.screen_to_logical(z.x, z.y)[0], adapter.screen_to_logical(z.x, z.y)[1]]
                for z in request.zeros
            ]
            poles_logical = [
                [adapter.screen_to_logical(p.x, p.y)[0], adapter.screen_to_logical(p.x, p.y)[1]]
                for p in request.poles
            ]
        else:
            zeros_logical = [[z.x, z.y] for z in request.zeros]
            poles_logical = [[p.x, p.y] for p in request.poles]

        tracker.sync_complete_stage("prepare_render", message="Coefficients ready")

        # Stage 7: Build Response
        tracker.sync_start_stage("render", message="Building continuation definition")

        laurent_coeffs = WebGLLaurentCoeffs(
            N=lmap.N,
            coeffs_neg=coeffs_neg,
            coeffs_pos=coeffs_pos,
            curve_scale=fit_result.curve_scale,
        )

        zeros_with_mult = [
            {"re": z.x, "im": z.y, "multiplicity": z.multiplicity}
            for z in request.zeros
        ]
        poles_with_mult = [
            {"re": p.x, "im": p.y, "multiplicity": p.multiplicity}
            for p in request.poles
        ]

        continuation_def = ContinuationDefinition(
            version="1.0",
            laurent_map=laurent_coeffs,
            expression=request.expression,
            zeros=zeros_with_mult,
            poles=poles_with_mult,
            created_at=datetime.utcnow().isoformat(),
            session_id=session_id,
            input_hash=logger.compute_input_hash(
                request.expression, curve_data, zeros_data, poles_data
            ),
            fit_max_error=fit_result.fit_max_err,
            fit_rms_error=fit_result.fit_rms_err,
            curve_point_count=len(polyline),
            curve_closed=export.closed,
        )

        response = WebGLRenderDataResponse(
            ok=True,
            laurent_coeffs=laurent_coeffs,
            zeros=zeros_logical,
            poles=poles_logical,
            expression=request.expression,
            continuation=continuation_def,
            session_id=session_id,
        )

        # Cache results
        logger.cache_computation(
            f"continuation_{session_id}",
            "continuation",
            continuation_def.model_dump(),
            session_id=session_id,
        )
        logger.cache_computation(
            f"result_{session_id}",
            "render",
            response.model_dump(),
            session_id=session_id,
        )

        tracker.sync_complete_stage("render", message="Complete")
        logger.end_session(session_id=session_id, success=True, result=response.model_dump())

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{session_id}] Pipeline failed: {e}")
        logger.end_session(session_id=session_id, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
