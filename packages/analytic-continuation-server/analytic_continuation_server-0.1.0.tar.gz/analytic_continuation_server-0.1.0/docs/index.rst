Analytic Continuation Server
============================

FastAPI server for domain coloring visualization, coordinate transforms,
Laurent series fitting, and analytic continuation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api
   models

Installation
------------

Install from PyPI::

    pip install analytic-continuation-server

Or install with optional domain coloring support::

    pip install analytic-continuation-server[domaincolor]

Quick Start
-----------

Run the server with uvicorn::

    uvicorn analytic_continuation_server:app --reload

Or use the CLI entry point::

    serve-analytic-continuation --port 8000

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/health

API Overview
------------

The server provides the following endpoint groups:

**Health** (``/api/health``)
    Health check and API information

**Transform** (``/api/transform/*``)
    Coordinate transformation between screen and logical space:

    - ``POST /api/transform/point`` - Transform a single point
    - ``POST /api/transform/points`` - Transform multiple points
    - ``POST /api/transform/params-from-bounds`` - Create params from view bounds
    - ``POST /api/transform/zoom`` - Apply zoom to parameters
    - ``POST /api/transform/pan`` - Apply pan to parameters

**Meromorphic** (``/api/meromorphic/*``)
    Build meromorphic functions from zeros and poles:

    - ``POST /api/meromorphic/build`` - Build expression from zeros/poles
    - ``POST /api/meromorphic/domaincolor`` - Build and visualize

**Domain Coloring** (``/api/domaincolor``)
    Generate domain coloring images:

    - ``POST /api/domaincolor`` - Generate PNG image
    - ``GET /api/domaincolor/validate`` - Validate expression
    - ``POST /api/domaincolor/validation-render`` - Render with overlays

**Laurent** (``/api/laurent/*``)
    Laurent series fitting and analytic continuation:

    - ``POST /api/laurent/precheck`` - Quick contour validation
    - ``POST /api/laurent/fit`` - Fit Laurent map to curve
    - ``POST /api/laurent/invert`` - Invert point through map
    - ``POST /api/laurent/compose`` - Compute continuation
    - ``POST /api/laurent/webgl-data`` - Get WebGL render data

**Session** (``/api/session/*``)
    Session management and progress tracking:

    - ``POST /api/session/start`` - Start new session
    - ``GET /api/session/{id}/progress/stream`` - SSE progress stream
    - ``GET /api/session/{id}/continuation`` - Get continuation definition

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
