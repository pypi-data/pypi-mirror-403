"""
Model conversion utilities.

Functions to convert between Pydantic models and analytic_continuation types.
"""

from typing import List
import numpy as np

from analytic_continuation import (
    TransformParams,
    Point,
    SplineExport,
    LaurentMapResult,
)
from analytic_continuation.types import SplineParameters

from .models import (
    PointModel,
    TransformParamsModel,
    SplineExportModel,
    SplineParametersModel,
    LaurentMapModel,
    ComplexModel,
)


# =============================================================================
# Point Converters
# =============================================================================


def point_model_to_point(pm: PointModel) -> Point:
    """Convert PointModel to Point."""
    return Point(x=pm.x, y=pm.y, index=pm.index)


def point_to_point_model(p: Point) -> PointModel:
    """Convert Point to PointModel."""
    return PointModel(x=p.x, y=p.y, index=p.index)


# =============================================================================
# Transform Params Converters
# =============================================================================


def params_model_to_params(pm: TransformParamsModel) -> TransformParams:
    """Convert TransformParamsModel to TransformParams."""
    return TransformParams(
        offset_x=pm.offset_x,
        offset_y=pm.offset_y,
        scale_x=pm.scale_x,
        scale_y=pm.scale_y,
    )


def params_to_params_model(p: TransformParams) -> TransformParamsModel:
    """Convert TransformParams to TransformParamsModel."""
    return TransformParamsModel(
        offset_x=p.offset_x,
        offset_y=p.offset_y,
        scale_x=p.scale_x,
        scale_y=p.scale_y,
    )


# =============================================================================
# Spline Export Converters
# =============================================================================


def spline_export_model_to_export(sem: SplineExportModel) -> SplineExport:
    """Convert SplineExportModel to SplineExport."""
    return SplineExport(
        version=sem.version,
        timestamp=sem.timestamp,
        closed=sem.closed,
        parameters=SplineParameters(
            tension=sem.parameters.tension,
            adaptiveTolerance=sem.parameters.adaptiveTolerance,
            minDistance=sem.parameters.minDistance,
        ),
        controlPoints=[point_model_to_point(p) for p in sem.controlPoints],
        spline=[point_model_to_point(p) for p in sem.spline],
        adaptivePolyline=[point_model_to_point(p) for p in sem.adaptivePolyline],
        stats=sem.stats,
    )


def spline_export_to_model(se: SplineExport) -> SplineExportModel:
    """Convert SplineExport to SplineExportModel."""
    return SplineExportModel(
        version=se.version,
        timestamp=se.timestamp,
        closed=se.closed,
        parameters=SplineParametersModel(
            tension=se.parameters.tension,
            adaptiveTolerance=se.parameters.adaptiveTolerance,
            minDistance=se.parameters.minDistance,
        ),
        controlPoints=[point_to_point_model(p) for p in se.controlPoints],
        spline=[point_to_point_model(p) for p in se.spline],
        adaptivePolyline=[point_to_point_model(p) for p in se.adaptivePolyline],
        stats=se.stats,
    )


# =============================================================================
# Laurent Map Converters
# =============================================================================


def laurent_map_model_to_result(lmm: LaurentMapModel) -> LaurentMapResult:
    """Convert Pydantic model to LaurentMapResult."""
    return LaurentMapResult(
        N=lmm.N,
        a0=complex(lmm.a0.re, lmm.a0.im),
        a=np.array([complex(c.re, c.im) for c in lmm.a]),
        b=np.array([complex(c.re, c.im) for c in lmm.b]),
    )


def laurent_map_result_to_model(lmr: LaurentMapResult) -> LaurentMapModel:
    """Convert LaurentMapResult to Pydantic model."""
    return LaurentMapModel(
        N=lmr.N,
        a0=ComplexModel(re=lmr.a0.real, im=lmr.a0.imag),
        a=[ComplexModel(re=c.real, im=c.imag) for c in lmr.a],
        b=[ComplexModel(re=c.real, im=c.imag) for c in lmr.b],
    )
