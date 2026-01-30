Quick Start Guide
=================

Starting the Server
-------------------

Using the CLI entry point::

    serve-analytic-continuation --port 8000

Using uvicorn directly::

    uvicorn analytic_continuation_server:app --host 0.0.0.0 --port 8000

For development with auto-reload::

    serve-analytic-continuation --reload

Health Check
------------

Verify the server is running::

    curl http://localhost:8000/api/health

Response::

    {"status": "ok", "version": "0.1.0"}

Example: Coordinate Transform
-----------------------------

Transform a screen point to logical coordinates::

    curl -X POST http://localhost:8000/api/transform/point \
      -H "Content-Type: application/json" \
      -d '{
        "point": {"x": 500, "y": 200},
        "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
        "direction": "to_logical"
      }'

Response::

    {"x": 1.0, "y": 1.0, "index": null}

Example: Build Meromorphic Function
-----------------------------------

Create a function with zeros at +/-1 and poles at +/-i::

    curl -X POST http://localhost:8000/api/meromorphic/build \
      -H "Content-Type: application/json" \
      -d '{
        "zeros": [{"x": 1, "y": 0}, {"x": -1, "y": 0}],
        "poles": [{"x": 0, "y": 1}, {"x": 0, "y": -1}],
        "coords": "logical"
      }'

Response::

    {
      "expression": "(z-1)*(z+1)/((z-i)*(z+i))",
      "zeros": [...],
      "poles": [...]
    }

Example: Python Client
----------------------

Using httpx::

    import httpx

    client = httpx.Client(base_url="http://localhost:8000")

    # Health check
    response = client.get("/api/health")
    print(response.json())

    # Transform points
    response = client.post("/api/transform/points", json={
        "points": [
            {"x": 400, "y": 300},
            {"x": 500, "y": 200},
        ],
        "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
        "direction": "to_logical",
    })
    print(response.json())

API Documentation
-----------------

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Configuration
-------------

Server options::

    serve-analytic-continuation \
      --host 0.0.0.0 \
      --port 8000 \
      --workers 4 \
      --log-level info

For production, consider using gunicorn with uvicorn workers::

    gunicorn analytic_continuation_server:app \
      -w 4 \
      -k uvicorn.workers.UvicornWorker \
      --bind 0.0.0.0:8000
