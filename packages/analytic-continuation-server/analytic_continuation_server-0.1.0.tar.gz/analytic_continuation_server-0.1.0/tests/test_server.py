"""Tests for FastAPI server routes."""

import pytest
from fastapi.testclient import TestClient

from analytic_continuation_server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Health endpoint returns OK."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "endpoints" in data


class TestTransformPointEndpoint:
    """Test /api/transform/point endpoint."""

    def test_to_logical(self, client):
        """Transform point to logical coordinates."""
        response = client.post("/api/transform/point", json={
            "point": {"x": 500, "y": 200},
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "direction": "to_logical",
        })
        assert response.status_code == 200
        data = response.json()
        assert abs(data["x"] - 1.0) < 1e-10
        assert abs(data["y"] - 1.0) < 1e-10

    def test_to_screen(self, client):
        """Transform point to screen coordinates."""
        response = client.post("/api/transform/point", json={
            "point": {"x": 1, "y": 1},
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "direction": "to_screen",
        })
        assert response.status_code == 200
        data = response.json()
        assert abs(data["x"] - 500) < 1e-10
        assert abs(data["y"] - 200) < 1e-10

    def test_preserves_index(self, client):
        """Index is preserved in transformation."""
        response = client.post("/api/transform/point", json={
            "point": {"x": 400, "y": 300, "index": 42},
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "direction": "to_logical",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["index"] == 42


class TestTransformPointsEndpoint:
    """Test /api/transform/points endpoint."""

    def test_multiple_points(self, client):
        """Transform multiple points."""
        response = client.post("/api/transform/points", json={
            "points": [
                {"x": 400, "y": 300},
                {"x": 500, "y": 200},
            ],
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "direction": "to_logical",
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert abs(data[0]["x"]) < 1e-10  # Origin
        assert abs(data[1]["x"] - 1) < 1e-10  # (1, 1)

    def test_empty_list(self, client):
        """Empty list returns empty list."""
        response = client.post("/api/transform/points", json={
            "points": [],
            "params": {"offset_x": 0, "offset_y": 0, "scale_x": 1},
            "direction": "to_logical",
        })
        assert response.status_code == 200
        assert response.json() == []


class TestParamsFromBoundsEndpoint:
    """Test /api/transform/params-from-bounds endpoint."""

    def test_uniform_square(self, client):
        """Create params for uniform square view."""
        response = client.post("/api/transform/params-from-bounds", json={
            "screen_width": 800,
            "screen_height": 800,
            "logical_x_min": -2,
            "logical_x_max": 2,
            "logical_y_min": -2,
            "logical_y_max": 2,
            "uniform": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["scale_x"] == 200  # 800 / 4
        assert data["scale_y"] is None  # Uniform

    def test_non_uniform(self, client):
        """Create params for non-uniform view."""
        response = client.post("/api/transform/params-from-bounds", json={
            "screen_width": 800,
            "screen_height": 400,
            "logical_x_min": -2,
            "logical_x_max": 2,
            "logical_y_min": -2,
            "logical_y_max": 2,
            "uniform": False,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["scale_x"] == 200  # 800 / 4
        assert data["scale_y"] == 100  # 400 / 4


class TestZoomEndpoint:
    """Test /api/transform/zoom endpoint."""

    def test_zoom_in(self, client):
        """Zoom in doubles scale."""
        response = client.post("/api/transform/zoom", json={
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "factor": 2.0,
            "center_x": 400,
            "center_y": 300,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["scale_x"] == 200

    def test_zoom_out(self, client):
        """Zoom out halves scale."""
        response = client.post("/api/transform/zoom", json={
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "factor": 0.5,
            "center_x": 400,
            "center_y": 300,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["scale_x"] == 50


class TestPanEndpoint:
    """Test /api/transform/pan endpoint."""

    def test_pan(self, client):
        """Pan shifts offset."""
        response = client.post("/api/transform/pan", json={
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "delta_x": 50,
            "delta_y": -25,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["offset_x"] == 450
        assert data["offset_y"] == 275


class TestMeromorphicBuildEndpoint:
    """Test /api/meromorphic/build endpoint."""

    def test_simple_zeros_poles(self, client):
        """Build expression from zeros and poles."""
        response = client.post("/api/meromorphic/build", json={
            "zeros": [{"x": 1, "y": 0}, {"x": -1, "y": 0}],
            "poles": [{"x": 0, "y": 1}, {"x": 0, "y": -1}],
            "coords": "logical",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["expression"] == "(z-1)*(z+1)/((z-i)*(z+i))"
        assert len(data["zeros"]) == 2
        assert len(data["poles"]) == 2

    def test_screen_coords_transform(self, client):
        """Transform from screen coordinates."""
        response = client.post("/api/meromorphic/build", json={
            "zeros": [{"x": 500, "y": 300}],  # -> (1, 0)
            "poles": [{"x": 400, "y": 200}],  # -> (0, 1)
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "coords": "screen",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["expression"] == "(z-1)/(z-i)"
        # Verify transformed coordinates
        assert abs(data["zeros"][0]["x"] - 1) < 1e-10
        assert abs(data["poles"][0]["y"] - 1) < 1e-10

    def test_with_multiplicities(self, client):
        """Build with multiplicities."""
        response = client.post("/api/meromorphic/build", json={
            "zeros": [{"x": 0, "y": 0, "multiplicity": 2}],
            "poles": [{"x": 1, "y": 0, "multiplicity": 3}],
            "coords": "logical",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["expression"] == "z^2/(z-1)^3"

    def test_empty_zeros_poles(self, client):
        """Empty zeros and poles returns '1'."""
        response = client.post("/api/meromorphic/build", json={
            "zeros": [],
            "poles": [],
            "coords": "logical",
        })
        assert response.status_code == 200
        assert response.json()["expression"] == "1"

    def test_only_zeros(self, client):
        """Only zeros, no poles."""
        response = client.post("/api/meromorphic/build", json={
            "zeros": [{"x": 1, "y": 0}, {"x": 2, "y": 0}],
            "poles": [],
            "coords": "logical",
        })
        assert response.status_code == 200
        assert response.json()["expression"] == "(z-1)*(z-2)"

    def test_only_poles(self, client):
        """Only poles, no zeros."""
        response = client.post("/api/meromorphic/build", json={
            "zeros": [],
            "poles": [{"x": 0, "y": 0}],
            "coords": "logical",
        })
        assert response.status_code == 200
        assert response.json()["expression"] == "1/z"


class TestSplineExportEndpoint:
    """Test /api/transform/spline-export endpoint."""

    def test_transform_to_logical(self, client):
        """Transform spline export to logical coordinates."""
        response = client.post("/api/transform/spline-export", json={
            "export": {
                "version": "1.0",
                "timestamp": "2026-01-22T00:00:00Z",
                "closed": True,
                "parameters": {
                    "tension": 0.5,
                    "adaptiveTolerance": 3.0,
                    "minDistance": 100.0,
                },
                "controlPoints": [
                    {"x": 400, "y": 300, "index": 0},
                    {"x": 500, "y": 200, "index": 1},
                ],
            },
            "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
            "direction": "to_logical",
        })
        assert response.status_code == 200
        data = response.json()

        # Check transformed points
        assert abs(data["controlPoints"][0]["x"]) < 1e-10
        assert abs(data["controlPoints"][0]["y"]) < 1e-10
        assert abs(data["controlPoints"][1]["x"] - 1) < 1e-10
        assert abs(data["controlPoints"][1]["y"] - 1) < 1e-10

        # Check scaled minDistance: 100 / 100 = 1.0
        assert abs(data["parameters"]["minDistance"] - 1.0) < 1e-10


class TestValidation:
    """Test request validation."""

    def test_invalid_direction(self, client):
        """Invalid direction should fail validation."""
        response = client.post("/api/transform/point", json={
            "point": {"x": 0, "y": 0},
            "params": {"offset_x": 0, "offset_y": 0, "scale_x": 1},
            "direction": "invalid",
        })
        assert response.status_code == 422  # Validation error

    def test_invalid_coords(self, client):
        """Invalid coords should fail validation."""
        response = client.post("/api/meromorphic/build", json={
            "zeros": [],
            "poles": [],
            "coords": "invalid",
        })
        assert response.status_code == 422


class TestWebGLDataEndpoint:
    """Test /api/laurent/webgl-data endpoint.

    Note: Full fitting tests are very slow due to the iterative nature of Laurent fitting.
    These tests verify the API structure with degenerate inputs that fail fast.
    """

    def test_webgl_data_degenerate_curve(self, client):
        """Verify the response structure when fitting fails quickly (degenerate curve)."""
        # Degenerate curve - all points the same -> fails fast with "zero diameter"
        degenerate_points = [{"x": 400, "y": 300, "index": i} for i in range(20)]

        response = client.post("/api/laurent/webgl-data", json={
            "export": {
                "version": "1.0",
                "timestamp": "2026-01-22T00:00:00Z",
                "closed": True,
                "parameters": {
                    "tension": 0.5,
                    "adaptiveTolerance": 3.0,
                    "minDistance": 15.0,
                },
                "controlPoints": degenerate_points[:5],
                "spline": degenerate_points,
                "adaptivePolyline": degenerate_points,
            },
            "zeros": [],
            "poles": [],
        })

        assert response.status_code == 200
        data = response.json()

        # Should fail gracefully with degenerate input
        assert data["ok"] is False
        assert "failure_reason" in data
        reason = data["failure_reason"].lower()
        assert any(word in reason for word in ["short", "degenerate", "diameter"])

    def test_webgl_data_too_short_curve(self, client):
        """Verify handling of curves that are too short."""
        # Only 2 points - not enough for fitting
        short_points = [{"x": 400, "y": 300, "index": 0}, {"x": 410, "y": 300, "index": 1}]

        response = client.post("/api/laurent/webgl-data", json={
            "export": {
                "version": "1.0",
                "timestamp": "2026-01-22T00:00:00Z",
                "closed": True,
                "parameters": {
                    "tension": 0.5,
                    "adaptiveTolerance": 3.0,
                    "minDistance": 15.0,
                },
                "controlPoints": short_points,
                "spline": short_points,
                "adaptivePolyline": short_points,
            },
            "zeros": [],
            "poles": [],
        })

        assert response.status_code == 200
        data = response.json()

        # Should fail due to insufficient points
        assert data["ok"] is False
        assert "failure_reason" in data
