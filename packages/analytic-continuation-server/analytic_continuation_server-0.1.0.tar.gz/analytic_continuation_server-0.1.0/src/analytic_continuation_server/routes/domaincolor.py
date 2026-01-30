"""
Domain coloring API endpoints.

Provides routes for:
- Domain coloring image generation
- Expression validation
- Validation renders with overlays
"""

import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models import DomainColorRequest, ValidationRenderRequest

router = APIRouter(prefix="/api/domaincolor", tags=["domaincolor"])


@router.post("")
async def generate_domain_color(request: DomainColorRequest):
    """
    Generate a domain coloring image.

    Returns a PNG image as a streaming response.
    """
    try:
        # Import py_domaincolor (optional dependency)
        from py_domaincolor import domain_color_array, get_callable
        import numpy as np
        from PIL import Image

        y_range = request.y_range or request.x_range

        # Get the function
        f = get_callable(request.expression)

        # Generate the domain coloring array
        img_array = domain_color_array(
            f,
            x_range=request.x_range,
            y_range=y_range,
            resolution=request.resolution,
            mode=request.mode,
            mod_contours=request.mod_contours,
            arg_contours=request.arg_contours,
        )

        # Convert to PIL Image
        img = Image.fromarray((img_array * 255).astype(np.uint8))

        # Save to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="image/png")

    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="py_domaincolor package not installed. Install with: pip install py-domaincolor"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/validate")
async def validate_expression(expression: str):
    """Validate a complex function expression without generating an image."""
    try:
        from py_domaincolor import validate_expression

        is_valid, error = validate_expression(expression)
        return {"valid": is_valid, "error": error}
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="py_domaincolor package not installed"
        )


@router.post("/validation-render")
async def validation_render(request: ValidationRenderRequest):
    """
    Generate a Python-rendered domain coloring with zeros/poles overlay.

    This serves as ground truth for validating the WebGL renderer.
    Returns a PNG image with:
    - Domain coloring of the meromorphic function
    - Zero markers (green circles)
    - Pole markers (red X's)
    - Optional curve overlay
    - Axis tick marks on border
    """
    try:
        import numpy as np
        from PIL import Image, ImageDraw
        from py_domaincolor import get_callable, complex_to_rgb, create_domain_grid

        y_range = request.y_range or request.x_range

        # Build the meromorphic function from zeros and poles
        if request.zeros or request.poles:
            numerator_terms = []
            for z in request.zeros:
                for _ in range(z.multiplicity):
                    if z.y >= 0:
                        numerator_terms.append(f"(z - ({z.x}+{z.y}*I))")
                    else:
                        numerator_terms.append(f"(z - ({z.x}{z.y}*I))")

            denominator_terms = []
            for p in request.poles:
                for _ in range(p.multiplicity):
                    if p.y >= 0:
                        denominator_terms.append(f"(z - ({p.x}+{p.y}*I))")
                    else:
                        denominator_terms.append(f"(z - ({p.x}{p.y}*I))")

            numerator = "*".join(numerator_terms) if numerator_terms else "1"
            denominator = "*".join(denominator_terms) if denominator_terms else "1"

            if request.expression and request.expression.strip() != "1":
                full_expr = f"({request.expression}) * {numerator} / ({denominator})"
            else:
                full_expr = f"{numerator} / ({denominator})"
        else:
            full_expr = request.expression

        # Get the callable function
        f = get_callable(full_expr)

        # Create the grid and evaluate
        X, Y, Z = create_domain_grid(request.x_range, y_range, request.resolution)

        with np.errstate(all='ignore'):
            W = f(Z)

        # Generate domain coloring
        rgb = complex_to_rgb(
            W,
            mode='standard',
            mod_contours=request.mod_contours,
            arg_contours_flag=request.arg_contours
        )

        # Convert to PIL Image (flip Y for standard orientation)
        img_array = (rgb * 255).astype(np.uint8)
        img_array = np.flipud(img_array)
        img = Image.fromarray(img_array)

        # Draw overlays
        draw = ImageDraw.Draw(img)

        # Helper to convert complex coords to pixel coords
        def complex_to_pixel(re, im):
            px = int((re - request.x_range[0]) / (request.x_range[1] - request.x_range[0]) * request.resolution)
            py = int((y_range[1] - im) / (y_range[1] - y_range[0]) * request.resolution)
            return px, py

        # Draw curve if provided
        if request.curve_points and len(request.curve_points) >= 2:
            curve_pixels = [complex_to_pixel(p['re'], p['im']) for p in request.curve_points]
            for i in range(len(curve_pixels) - 1):
                draw.line(
                    [curve_pixels[i], curve_pixels[i + 1]],
                    fill=request.curve_color,
                    width=int(request.curve_width)
                )

        # Draw zeros (green circles)
        for z in request.zeros:
            px, py = complex_to_pixel(z.x, z.y)
            r = 8 + 2 * (z.multiplicity - 1)
            draw.ellipse([px - r, py - r, px + r, py + r], outline='#00ff88', width=2)
            if z.multiplicity > 1:
                draw.text((px + r + 2, py - 6), str(z.multiplicity), fill='#00ff88')

        # Draw poles (red X's)
        for p in request.poles:
            px, py = complex_to_pixel(p.x, p.y)
            r = 8 + 2 * (p.multiplicity - 1)
            draw.line([px - r, py - r, px + r, py + r], fill='#ff4444', width=2)
            draw.line([px + r, py - r, px - r, py + r], fill='#ff4444', width=2)
            if p.multiplicity > 1:
                draw.text((px + r + 2, py - 6), str(p.multiplicity), fill='#ff4444')

        # Draw axis tick marks on border
        if request.show_axis_ticks:
            tick_len = 10
            # Real axis ticks
            x_start = np.ceil(request.x_range[0] / request.tick_interval) * request.tick_interval
            x_end = np.floor(request.x_range[1] / request.tick_interval) * request.tick_interval
            for x_val in np.arange(x_start, x_end + 0.001, request.tick_interval):
                px, _ = complex_to_pixel(x_val, 0)
                draw.line([px, request.resolution - 1, px, request.resolution - tick_len], fill='white', width=1)
                draw.line([px, 0, px, tick_len], fill='white', width=1)
                label = f"{x_val:.0f}" if x_val == int(x_val) else f"{x_val:.1f}"
                draw.text((px - 8, request.resolution - tick_len - 12), label, fill='white')

            # Imaginary axis ticks
            y_start = np.ceil(y_range[0] / request.tick_interval) * request.tick_interval
            y_end = np.floor(y_range[1] / request.tick_interval) * request.tick_interval
            for y_val in np.arange(y_start, y_end + 0.001, request.tick_interval):
                _, py = complex_to_pixel(0, y_val)
                draw.line([0, py, tick_len, py], fill='white', width=1)
                draw.line([request.resolution - 1, py, request.resolution - tick_len, py], fill='white', width=1)
                label = f"{y_val:.0f}i" if y_val == int(y_val) else f"{y_val:.1f}i"
                draw.text((tick_len + 2, py - 6), label, fill='white')

        # Save to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="image/png")

    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"Required package not installed: {e}")
    except Exception as e:
        import traceback
        raise HTTPException(status_code=400, detail=f"{str(e)}\n{traceback.format_exc()}")
