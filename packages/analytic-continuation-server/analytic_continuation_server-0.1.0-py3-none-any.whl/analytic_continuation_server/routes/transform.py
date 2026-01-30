"""
Coordinate transformation API endpoints.

Provides routes for:
- Single point transformation
- Batch point transformation
- Spline export transformation
- Transform parameter creation from view bounds
- Zoom and pan operations
"""

from typing import List
from fastapi import APIRouter, HTTPException

from analytic_continuation import SpaceAdapter, TransformParams

from ..models import (
    PointModel,
    TransformParamsModel,
    ViewBoundsModel,
    TransformPointRequest,
    TransformPointsRequest,
    TransformSplineExportRequest,
    SplineExportModel,
    ZoomRequest,
    PanRequest,
)
from ..converters import (
    point_model_to_point,
    point_to_point_model,
    params_model_to_params,
    params_to_params_model,
    spline_export_model_to_export,
    spline_export_to_model,
)

router = APIRouter(prefix="/api/transform", tags=["transform"])


@router.post("/point")
async def transform_point(request: TransformPointRequest) -> PointModel:
    """Transform a single point between screen and logical space."""
    adapter = SpaceAdapter(params_model_to_params(request.params))
    point = point_model_to_point(request.point)

    if request.direction == "to_logical":
        result = adapter.transform_point_to_logical(point)
    else:
        result = adapter.transform_point_to_screen(point)

    return point_to_point_model(result)


@router.post("/points")
async def transform_points(request: TransformPointsRequest) -> List[PointModel]:
    """Transform multiple points between screen and logical space."""
    adapter = SpaceAdapter(params_model_to_params(request.params))
    points = [point_model_to_point(p) for p in request.points]

    if request.direction == "to_logical":
        results = adapter.transform_points_to_logical(points)
    else:
        results = adapter.transform_points_to_screen(points)

    return [point_to_point_model(r) for r in results]


@router.post("/spline-export")
async def transform_spline_export(request: TransformSplineExportRequest) -> SplineExportModel:
    """Transform a full SplineExport between screen and logical space."""
    adapter = SpaceAdapter(params_model_to_params(request.params))
    export = spline_export_model_to_export(request.export)

    if request.direction == "to_logical":
        result = adapter.transform_spline_export_to_logical(export)
    else:
        raise HTTPException(
            status_code=501,
            detail="to_screen direction for spline exports not yet implemented"
        )

    return spline_export_to_model(result)


@router.post("/params-from-bounds")
async def params_from_bounds(bounds: ViewBoundsModel) -> TransformParamsModel:
    """Create transform parameters from screen dimensions and logical view bounds."""
    params = TransformParams.from_view_bounds(
        screen_width=bounds.screen_width,
        screen_height=bounds.screen_height,
        logical_x_range=(bounds.logical_x_min, bounds.logical_x_max),
        logical_y_range=(bounds.logical_y_min, bounds.logical_y_max),
        uniform=bounds.uniform,
    )
    return params_to_params_model(params)


@router.post("/zoom")
async def zoom(request: ZoomRequest) -> TransformParamsModel:
    """Apply zoom to transform parameters."""
    adapter = SpaceAdapter(params_model_to_params(request.params))

    center = None
    if request.center_x is not None and request.center_y is not None:
        center = (request.center_x, request.center_y)

    new_adapter = adapter.zoom(request.factor, center)
    return params_to_params_model(new_adapter.params)


@router.post("/pan")
async def pan(request: PanRequest) -> TransformParamsModel:
    """Apply pan to transform parameters."""
    adapter = SpaceAdapter(params_model_to_params(request.params))
    new_adapter = adapter.pan(request.delta_x, request.delta_y)
    return params_to_params_model(new_adapter.params)
