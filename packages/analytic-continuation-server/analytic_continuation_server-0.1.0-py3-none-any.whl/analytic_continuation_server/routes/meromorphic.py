"""
Meromorphic function building API endpoints.

Provides routes for:
- Building meromorphic expressions from zeros and poles
- Combined meromorphic + domain coloring generation
"""

from typing import Optional, Tuple
from fastapi import APIRouter

from analytic_continuation import (
    SpaceAdapter,
    Singularity,
    build_meromorphic_expression,
)

from ..models import (
    MeromorphicRequest,
    MeromorphicResponse,
    SingularityModel,
    DomainColorRequest,
)
from ..converters import params_model_to_params

router = APIRouter(prefix="/api/meromorphic", tags=["meromorphic"])


@router.post("/build")
async def build_meromorphic(request: MeromorphicRequest) -> MeromorphicResponse:
    """
    Build a meromorphic function expression from zeros and poles.

    Accepts points in either screen or logical coordinates.
    Returns the sympy-compatible expression and points in logical coords.

    Example request:
    {
        "zeros": [{"x": 1, "y": 0}, {"x": -1, "y": 0}],
        "poles": [{"x": 0, "y": 1}, {"x": 0, "y": -1}],
        "coords": "logical"
    }

    Returns:
    {
        "expression": "(z-1)*(z+1)/((z-i)*(z+i))",
        "zeros": [...],
        "poles": [...]
    }
    """
    # Transform to logical coordinates if needed
    if request.coords == "screen" and request.params:
        adapter = SpaceAdapter(params_model_to_params(request.params))

        logical_zeros = []
        for z in request.zeros:
            lx, ly = adapter.screen_to_logical(z.x, z.y)
            logical_zeros.append(SingularityModel(x=lx, y=ly, multiplicity=z.multiplicity))

        logical_poles = []
        for p in request.poles:
            lx, ly = adapter.screen_to_logical(p.x, p.y)
            logical_poles.append(SingularityModel(x=lx, y=ly, multiplicity=p.multiplicity))
    else:
        logical_zeros = request.zeros
        logical_poles = request.poles

    # Convert to Singularity objects and build expression
    zero_sings = [Singularity(z.x, z.y, z.multiplicity) for z in logical_zeros]
    pole_sings = [Singularity(p.x, p.y, p.multiplicity) for p in logical_poles]

    expression = build_meromorphic_expression(zero_sings, pole_sings)

    return MeromorphicResponse(
        expression=expression,
        zeros=logical_zeros,
        poles=logical_poles,
    )


@router.post("/domaincolor")
async def meromorphic_domain_color(
    request: MeromorphicRequest,
    x_range: Tuple[float, float] = (-2.0, 2.0),
    y_range: Optional[Tuple[float, float]] = None,
    resolution: int = 800,
):
    """
    Build a meromorphic function from zeros/poles and generate domain coloring.

    Combines /api/meromorphic/build and /api/domaincolor into one call.
    """
    # Import here to avoid circular imports
    from .domaincolor import generate_domain_color

    # First build the expression
    build_response = await build_meromorphic(request)

    # Then generate the domain coloring
    dc_request = DomainColorRequest(
        expression=build_response.expression,
        x_range=x_range,
        y_range=y_range,
        resolution=resolution,
    )

    return await generate_domain_color(dc_request)
