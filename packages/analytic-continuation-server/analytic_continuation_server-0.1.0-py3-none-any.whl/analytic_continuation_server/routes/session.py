"""
Session management and progress tracking API endpoints.

Provides routes for:
- Session lifecycle management (start, get, end)
- Progress tracking and streaming (SSE)
- Session recovery and resumption
- Continuation export/import
"""

import io
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from analytic_continuation import (
    get_logger,
    ProgressTracker,
    format_cli_progress,
)

from ..models import (
    SessionStartRequest,
    SessionResponse,
    CheckResumableRequest,
    WebGLRenderDataResponse,
    WebGLLaurentCoeffs,
    ContinuationDefinition,
)
from ..session_state import get_active_trackers
from ..codegen import generate_python_continuation_code

logger = get_logger()
router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/start")
async def start_session(request: SessionStartRequest) -> SessionResponse:
    """
    Start a new pipeline session.

    Creates a session ID for tracking progress and recovery.
    """
    _active_trackers = get_active_trackers()

    zeros_data = [{"x": z.x, "y": z.y, "multiplicity": z.multiplicity} for z in request.zeros]
    poles_data = [{"x": p.x, "y": p.y, "multiplicity": p.multiplicity} for p in request.poles]

    session_id = logger.start_session(
        expression=request.expression,
        curve_data=request.curve_data,
        zeros=zeros_data,
        poles=poles_data,
    )

    tracker = ProgressTracker(session_id)
    _active_trackers[session_id] = tracker

    session = logger.get_session(session_id)

    return SessionResponse(
        session_id=session_id,
        status=session.status.value if session else "unknown",
        created_at=session.created_at if session else "",
        expression=request.expression,
    )


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get session details and current progress."""
    _active_trackers = get_active_trackers()

    session = logger.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    progress = None
    if session_id in _active_trackers:
        progress = _active_trackers[session_id].get_state()

    return {
        **session.to_dict(),
        "live_progress": progress,
    }


@router.get("/{session_id}/progress")
async def get_session_progress(session_id: str):
    """Get current progress state for a session."""
    _active_trackers = get_active_trackers()

    if session_id not in _active_trackers:
        session = logger.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "session_id": session_id,
            "status": session.status.value,
            "tasks": [t.to_dict() for t in session.tasks],
        }

    tracker = _active_trackers[session_id]
    return tracker.get_state()


@router.get("/{session_id}/progress/stream")
async def stream_session_progress(session_id: str, request: Request):
    """Stream progress updates via Server-Sent Events (SSE)."""
    _active_trackers = get_active_trackers()

    if session_id not in _active_trackers:
        raise HTTPException(status_code=404, detail="No active session")

    tracker = _active_trackers[session_id]

    async def event_generator():
        async for event in tracker.subscribe():
            if await request.is_disconnected():
                break
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{session_id}/cli-progress")
async def get_cli_progress(session_id: str):
    """Get CLI-formatted progress output (checklist style)."""
    _active_trackers = get_active_trackers()

    if session_id not in _active_trackers:
        raise HTTPException(status_code=404, detail="No active session")

    tracker = _active_trackers[session_id]
    return {
        "cli_output": format_cli_progress(tracker),
        "state": tracker.get_state(),
    }


@router.get("s")
async def list_sessions(limit: int = 20):
    """List recent sessions."""
    sessions = logger.list_sessions(limit)
    return {"sessions": sessions}


@router.delete("/{session_id}")
async def end_session(session_id: str, success: bool = True, error: Optional[str] = None):
    """End a session and clean up resources."""
    _active_trackers = get_active_trackers()

    logger.end_session(session_id=session_id, success=success, error=error)

    if session_id in _active_trackers:
        del _active_trackers[session_id]

    return {"status": "ended", "session_id": session_id}


@router.get("/{session_id}/cache/{cache_key}")
async def get_cached_data(session_id: str, cache_key: str):
    """Retrieve cached computation data from a session."""
    data = logger.get_cached_computation(cache_key, session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Cache entry not found")
    return data


@router.get("/{session_id}/recover")
async def recover_session(session_id: str):
    """Attempt to recover a session's results."""
    session = logger.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = logger.get_cached_computation(f"result_{session_id}", session_id)
    laurent_map = logger.get_cached_computation(f"laurent_map_{session_id}", session_id)

    return {
        "session": session.to_dict(),
        "cached_result": result,
        "cached_laurent_map": laurent_map,
        "recoverable": result is not None or laurent_map is not None,
    }


@router.post("/{session_id}/resume")
async def resume_session(session_id: str):
    """Resume a failed or interrupted session."""
    _active_trackers = get_active_trackers()

    session = logger.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    laurent_map = logger.get_cached_computation(f"laurent_map_{session_id}", session_id)
    cached_result = logger.get_cached_computation(f"result_{session_id}", session_id)

    if cached_result:
        return {
            "status": "complete",
            "session_id": session_id,
            "message": "Session already completed",
            "result": cached_result,
        }

    if not laurent_map:
        return {
            "status": "cannot_resume",
            "reason": "No cached computation data found",
            "suggestion": "Start a new session",
        }

    tracker = ProgressTracker(session_id)
    _active_trackers[session_id] = tracker

    return {
        "status": "resumed",
        "session_id": session_id,
        "available_data": {
            "laurent_map": laurent_map is not None,
            "curve_scale": laurent_map.get("curve_scale") if laurent_map else None,
            "N": laurent_map.get("N") if laurent_map else None,
        },
    }


@router.post("/check-resumable")
async def check_resumable(request: CheckResumableRequest):
    """Check if there's a previous session with matching inputs that can be resumed."""
    curve_data = None
    if request.export:
        curve_data = {
            "controlPoints": [{"x": p.x, "y": p.y} for p in request.export.controlPoints],
            "closed": request.export.closed,
        }

    zeros_data = [{"x": z.x, "y": z.y} for z in request.zeros]
    poles_data = [{"x": p.x, "y": p.y} for p in request.poles]

    match = logger.find_resumable_session(
        expression=request.expression,
        curve_data=curve_data,
        zeros=zeros_data,
        poles=poles_data,
    )

    if not match:
        return {
            "resumable": False,
            "input_hash": logger.compute_input_hash(
                request.expression, curve_data, zeros_data, poles_data
            ),
        }

    return {
        "resumable": True,
        "session_id": match["session_id"],
        "created_at": match["created_at"],
        "status": match["status"],
        "cached_stages": match["cached_stages"],
        "has_result": match["has_result"],
        "input_hash": match["input_hash"],
    }


@router.post("/{session_id}/resume-with-data")
async def resume_with_cached_data(session_id: str) -> WebGLRenderDataResponse:
    """Resume a session and return the cached result directly."""
    session = logger.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    cached_result = logger.get_cached_computation(f"result_{session_id}", session_id)
    if cached_result:
        logger.info(f"[{session_id}] Returning cached result")
        return WebGLRenderDataResponse(**cached_result)

    laurent_map = logger.get_cached_computation(f"laurent_map_{session_id}", session_id)
    if not laurent_map:
        raise HTTPException(status_code=400, detail="No cached data available")

    logger.info(f"[{session_id}] Rebuilding result from cached Laurent map")

    N = laurent_map["N"]
    a0 = laurent_map["a0"]
    a_coeffs = laurent_map["a"]
    b_coeffs = laurent_map["b"]

    coeffs_neg = [[c["re"], c["im"]] for c in b_coeffs]
    coeffs_pos = [[a0["re"], a0["im"]]]
    coeffs_pos.extend([[c["re"], c["im"]] for c in a_coeffs])

    zeros_logical = [[z["x"], z["y"]] for z in session.zeros]
    poles_logical = [[p["x"], p["y"]] for p in session.poles]

    response = WebGLRenderDataResponse(
        ok=True,
        laurent_coeffs=WebGLLaurentCoeffs(
            N=N,
            coeffs_neg=coeffs_neg,
            coeffs_pos=coeffs_pos,
            curve_scale=laurent_map["curve_scale"],
        ),
        zeros=zeros_logical,
        poles=poles_logical,
        expression=session.expression,
    )

    logger.cache_computation(
        f"result_{session_id}",
        "render",
        response.model_dump(),
        session_id=session_id,
    )

    return response


@router.get("/{session_id}/continuation")
async def get_continuation(session_id: str) -> ContinuationDefinition:
    """Get the complete continuation definition for a session."""
    cached = logger.get_cached_computation(f"continuation_{session_id}", session_id)
    if cached:
        return ContinuationDefinition(**cached)

    result = logger.get_cached_computation(f"result_{session_id}", session_id)
    if result and result.get("continuation"):
        return ContinuationDefinition(**result["continuation"])

    laurent_map = logger.get_cached_computation(f"laurent_map_{session_id}", session_id)
    if not laurent_map:
        raise HTTPException(status_code=404, detail="Continuation not found")

    session = logger.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    coeffs_neg = [[c["re"], c["im"]] for c in laurent_map["b"]]
    coeffs_pos = [[laurent_map["a0"]["re"], laurent_map["a0"]["im"]]]
    coeffs_pos.extend([[c["re"], c["im"]] for c in laurent_map["a"]])

    return ContinuationDefinition(
        version="1.0",
        laurent_map=WebGLLaurentCoeffs(
            N=laurent_map["N"],
            coeffs_neg=coeffs_neg,
            coeffs_pos=coeffs_pos,
            curve_scale=laurent_map["curve_scale"],
        ),
        expression=session.expression,
        zeros=[
            {"re": z["x"], "im": z["y"], "multiplicity": z.get("multiplicity", 1)}
            for z in session.zeros
        ],
        poles=[
            {"re": p["x"], "im": p["y"], "multiplicity": p.get("multiplicity", 1)}
            for p in session.poles
        ],
        session_id=session_id,
        created_at=session.created_at,
    )


@router.get("/{session_id}/continuation/export")
async def export_continuation(session_id: str, format: str = "json"):
    """Export the continuation definition in various formats."""
    continuation = await get_continuation(session_id)

    if format == "json":
        return continuation

    elif format == "python":
        code = generate_python_continuation_code(continuation)
        return StreamingResponse(
            io.BytesIO(code.encode()),
            media_type="text/x-python",
            headers={
                "Content-Disposition": f"attachment; filename=continuation_{session_id}.py"
            },
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {format}")


# Continuation import router (separate prefix)
continuation_router = APIRouter(prefix="/api/continuation", tags=["continuation"])


@continuation_router.post("/import")
async def import_continuation(continuation: ContinuationDefinition):
    """Import a continuation definition and create a new session for it."""
    zeros_data = [
        {"x": z["re"], "y": z["im"], "multiplicity": z.get("multiplicity", 1)}
        for z in continuation.zeros
    ]
    poles_data = [
        {"x": p["re"], "y": p["im"], "multiplicity": p.get("multiplicity", 1)}
        for p in continuation.poles
    ]

    session_id = logger.start_session(
        expression=continuation.expression,
        zeros=zeros_data,
        poles=poles_data,
    )

    logger.cache_computation(
        f"continuation_{session_id}",
        "continuation",
        continuation.model_dump(),
        session_id=session_id,
    )

    laurent_map_data = {
        "N": continuation.laurent_map.N,
        "a0": {
            "re": continuation.laurent_map.coeffs_pos[0][0],
            "im": continuation.laurent_map.coeffs_pos[0][1],
        },
        "a": [{"re": c[0], "im": c[1]} for c in continuation.laurent_map.coeffs_pos[1:]],
        "b": [{"re": c[0], "im": c[1]} for c in continuation.laurent_map.coeffs_neg],
        "curve_scale": continuation.laurent_map.curve_scale,
    }
    logger.cache_computation(
        f"laurent_map_{session_id}",
        "fit_laurent",
        laurent_map_data,
        session_id=session_id,
    )

    logger.end_session(session_id=session_id, success=True)

    return {
        "status": "imported",
        "session_id": session_id,
        "continuation": continuation,
    }
