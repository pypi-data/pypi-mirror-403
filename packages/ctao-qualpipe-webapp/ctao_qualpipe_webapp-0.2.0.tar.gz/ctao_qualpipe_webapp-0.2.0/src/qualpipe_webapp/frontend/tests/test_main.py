import re
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from qualpipe_webapp.frontend.main import BACKEND_ENDPOINTS, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _setup_backend_endpoints():
    """Set up mock backend endpoints for testing."""
    # Clear existing endpoints
    BACKEND_ENDPOINTS.clear()
    # Add test endpoints
    BACKEND_ENDPOINTS.update(
        {
            "v1/health": {"methods": {"GET"}, "schemas": {}},
            "v1/ob_date_map": {"methods": {"GET"}, "schemas": {}},
            "v1/data": {"methods": {"GET"}, "schemas": {}},
            "v1/test": {
                "methods": {"GET", "POST", "PUT", "DELETE", "PATCH"},
                "schemas": {},
            },
            "docs": {"methods": {"GET"}, "schemas": {}},  # For /api/docs
            "redoc": {"methods": {"GET"}, "schemas": {}},  # For /api/redoc
            "openapi.json": {
                "methods": {"GET"},
                "schemas": {},
            },  # For /api/openapi.json
        }
    )
    yield
    # Clean up after test
    BACKEND_ENDPOINTS.clear()


def assert_html_utf8(response):
    """Check if 'html' and 'utf-8' is in response."""
    assert "text/html" in response.headers["content-type"]
    assert "charset=utf-8" in response.headers["content-type"]


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "frontend"}


def test_read_home():
    """Test the home page endpoint."""
    response = client.get("/home")
    assert response.status_code == 200
    assert_html_utf8(response)
    assert "home" in response.text or "<html" in response.text
    assert '<nav id="first-nav" class="first-nav' in response.text
    assert '<nav id="second-nav" class="second-nav' not in response.text


scopes = ["LSTs", "MSTs", "SSTs"]
pages = [
    ("", "{scope}"),
    ("/pointings", "Pointings"),
    ("/event_rates", "Event rates"),
    ("/trigger_tags", "Trigger tags"),
    ("/interleaved_pedestals", "Interleaved pedestals"),
    ("/interleaved_flat_field_charge", "Interleaved flat field charge"),
    ("/interleaved_flat_field_time", "Interleaved flat field time"),
    ("/cosmics", "Cosmics"),
    ("/pixel_problems", "Pixel problems"),
    ("/muons", "Muons"),
    ("/interleaved_pedestals_averages", "Interleaved pedestals averages"),
    ("/interleaved_FF_averages", "Interleaved FF averages"),
    ("/cosmics_averages", "Cosmics averages"),
]


@pytest.mark.parametrize("scope", scopes)
@pytest.mark.parametrize(("page", "keyword"), pages)
def test_read_scopes(scope, page, keyword):
    """Test the scope and page endpoints."""
    endpoint = f"/{scope}{page}"
    expected_keyword = keyword.format(scope=scope)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert_html_utf8(response)
    assert expected_keyword in response.text or "<!DOCTYPE html>" in response.text
    assert '<nav id="first-nav" class="first-nav' in response.text
    assert re.search(r"<nav\s+id=\"second-nav\"\s+class=\"second-nav", response.text)
    expected_keyword = expected_keyword.replace(" ", "[\\s]*")
    pattern = (
        rf'href="{re.escape(endpoint)}"[\w\s\n=:;<>\".\-]*>{expected_keyword}</a[\s]*>'
    )
    assert re.search(pattern, response.text)


def test_not_found():
    """Test the 404 page."""
    response = client.get("/nonexistent-page")
    assert response.status_code == 404
    assert_html_utf8(response)
    assert "404" in response.text or "not found" in response.text.lower()


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE", "PATCH"])
def test_api_proxy_endpoints(mock_client_class, method):
    """Test API proxy endpoints with different HTTP methods."""
    # Mock the backend response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"result": "success"}'
    mock_response.content = b'{"result": "success"}'
    mock_response.headers = {"content-type": "application/json"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client_class.return_value = mock_client  # Set the method response
    if method == "GET":
        mock_client.get.return_value = mock_response
        response = client.get("/api/v1/test")
    elif method == "POST":
        mock_client.post.return_value = mock_response
        response = client.post("/api/v1/test", json={"test": "data"})
    elif method == "PUT":
        mock_client.put.return_value = mock_response
        response = client.put("/api/v1/test", json={"test": "data"})
    elif method == "DELETE":
        mock_client.delete.return_value = mock_response
        response = client.delete("/api/v1/test")
    elif method == "PATCH":
        mock_client.patch.return_value = mock_response
        response = client.patch("/api/v1/test", json={"test": "data"})

    # Now we can assert exact expected behavior
    assert response.status_code == 200


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_proxy_with_query_params(mock_client_class):
    """Test API proxy with query parameters."""
    # Mock backend response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"data": "result"}'
    mock_response.content = b'{"data": "result"}'
    mock_response.headers = {"content-type": "application/json"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    response = client.get("/api/v1/data?param1=value1&param2=value2")
    assert response.status_code == 200

    # Verify the backend was called with correct URL including query params
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args[0][0]
    assert "param1=value1" in call_args
    assert "param2=value2" in call_args


def test_api_proxy_blocks_path_traversal_attacks():
    """Test that path traversal attacks are blocked by endpoint discovery.

    FastAPI normalizes the path, resolving ../ sequences before routing.
    The test path resolves to /api/etc/passwd, which is blocked as unknown.
    """
    response = client.get("/api/v1/test/../../../etc/passwd")
    assert response.status_code == 404


def test_api_proxy_empty_path():
    """Test API proxy with empty path."""
    response = client.get("/api/")
    # With endpoint discovery replacing nginx proxy, empty paths return 404 (endpoint not found)
    assert response.status_code == 404


def test_api_proxy_absolute_path():
    """Test API proxy with absolute path."""
    response = client.get("/api//absolute/path")
    # With endpoint discovery replacing nginx proxy, unknown endpoints return 404
    assert response.status_code == 404


def test_health_endpoint_content():
    """Test health endpoint returns correct JSON structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["status"] == "ok"
    assert data["service"] == "frontend"


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_proxy_with_special_query_params(mock_client_class):
    """Test API proxy with various query parameters."""
    # Mock backend response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"result": "ok"}'
    mock_response.content = b'{"result": "ok"}'
    mock_response.headers = {"content-type": "application/json"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    # Test with valid special characters in query params
    response = client.get("/api/v1/test?param=value%20with%20spaces&other=123")
    assert response.status_code == 200


def test_root_path():
    """Test root path behavior."""
    response = client.get("/", follow_redirects=False)
    # Root path returns 404 (not configured)
    assert response.status_code == 404


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_proxy_connection_error(mock_client_class):
    """Test API proxy handles connection errors properly."""
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    # Simulate connection error
    mock_client.get.side_effect = httpx.RequestError("Connection failed")
    mock_client_class.return_value = mock_client

    response = client.get("/api/v1/health")
    # Should return 503 Service Unavailable for connection errors
    assert response.status_code == 503
    assert "application/json" in response.headers["content-type"]


def test_debug_endpoints():
    """Test the debug endpoint that shows discovered endpoints."""
    response = client.get("/api/_debug/endpoints")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data
    assert "total_count" in data
    assert isinstance(data["endpoints"], dict)
    assert data["total_count"] == len(data["endpoints"])


def test_method_validation():
    """Test that unsupported methods are rejected."""
    # v1/health only supports GET
    response = client.post("/api/v1/health", json={"test": "data"})
    assert response.status_code == 405
    assert "Method POST not allowed" in response.json()["detail"]


def test_unknown_endpoint():
    """Test that unknown endpoints are rejected."""
    response = client.get("/api/v1/unknown")
    assert response.status_code == 404
    # Check if response is JSON or HTML
    if "application/json" in response.headers.get("content-type", ""):
        assert "Endpoint not found" in response.json()["detail"]
    else:
        # If it's HTML (default 404 page), just verify it's a 404
        assert response.status_code == 404


# ============================================================
# UNIT TESTS FOR HELPER FUNCTIONS
# ============================================================


def test_extract_endpoint_schemas():
    """Test _extract_endpoint_schemas function."""
    from qualpipe_webapp.frontend.main import _extract_endpoint_schemas

    method_info = {
        "parameters": [{"name": "param1", "required": True}],
        "requestBody": {"content": {"application/json": {}}},
        "responses": {"200": {"description": "Success"}},
    }

    result = _extract_endpoint_schemas(method_info, "get")
    assert "get_parameters" in result
    assert "get_requestBody" in result
    assert "get_responses" in result
    assert result["get_parameters"] == method_info["parameters"]


def test_extract_endpoint_schemas_empty():
    """Test _extract_endpoint_schemas with empty method info."""
    from qualpipe_webapp.frontend.main import _extract_endpoint_schemas

    result = _extract_endpoint_schemas({}, "post")
    assert result == {}


def test_parse_openapi_path():
    """Test _parse_openapi_path function."""
    from qualpipe_webapp.frontend.main import _parse_openapi_path

    path_info = {
        "get": {"parameters": [{"name": "id", "required": True}]},
        "post": {"requestBody": {"content": {"application/json": {}}}},
        "options": {},  # Should be ignored
    }

    clean_path, endpoint_info = _parse_openapi_path("/v1/test", path_info)
    assert clean_path == "v1/test"
    assert endpoint_info["methods"] == {"GET", "POST"}
    assert "get_parameters" in endpoint_info["schemas"]
    assert "post_requestBody" in endpoint_info["schemas"]


def test_use_fallback_endpoints():
    """Test _use_fallback_endpoints function."""
    from qualpipe_webapp.frontend.main import BACKEND_ENDPOINTS, _use_fallback_endpoints

    BACKEND_ENDPOINTS.clear()
    _use_fallback_endpoints()

    assert "v1/health" in BACKEND_ENDPOINTS
    assert "v1/ob_date_map" in BACKEND_ENDPOINTS
    assert "v1/data" in BACKEND_ENDPOINTS
    assert BACKEND_ENDPOINTS["v1/health"]["methods"] == {"GET"}


def test_valid_url():
    """Test _valid_url function."""
    from qualpipe_webapp.frontend.main import _valid_url

    assert _valid_url("http://example.com") is True
    assert _valid_url("https://example.com:8000") is True
    assert _valid_url("ftp://example.com") is False
    assert _valid_url("not-a-url") is False
    assert _valid_url("") is False


# ============================================================
# BACKEND ENDPOINT DISCOVERY TESTS
# ============================================================


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
@pytest.mark.anyio()
async def test_discover_backend_endpoints_success(mock_client_class):
    """Test successful backend endpoint discovery."""
    from qualpipe_webapp.frontend.main import (
        BACKEND_ENDPOINTS,
        discover_backend_endpoints,
    )

    # Mock OpenAPI spec response
    mock_spec = {
        "paths": {
            "/v1/health": {"get": {"responses": {"200": {"description": "OK"}}}},
            "/v1/data": {
                "get": {"parameters": [{"name": "id", "required": True}]},
                "post": {"requestBody": {"content": {"application/json": {}}}},
            },
        }
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_spec

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    BACKEND_ENDPOINTS.clear()
    await discover_backend_endpoints()

    assert "v1/health" in BACKEND_ENDPOINTS
    assert "v1/data" in BACKEND_ENDPOINTS
    assert BACKEND_ENDPOINTS["v1/health"]["methods"] == {"GET"}
    assert BACKEND_ENDPOINTS["v1/data"]["methods"] == {"GET", "POST"}


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
@pytest.mark.anyio()
async def test_discover_backend_endpoints_http_error(mock_client_class):
    """Test backend endpoint discovery with HTTP error."""
    from qualpipe_webapp.frontend.main import (
        BACKEND_ENDPOINTS,
        discover_backend_endpoints,
    )

    mock_response = Mock()
    mock_response.status_code = 404

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    BACKEND_ENDPOINTS.clear()
    await discover_backend_endpoints()

    # Should fall back to default endpoints
    assert "v1/health" in BACKEND_ENDPOINTS
    assert "v1/ob_date_map" in BACKEND_ENDPOINTS
    assert "v1/data" in BACKEND_ENDPOINTS


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
@pytest.mark.anyio()
async def test_discover_backend_endpoints_connection_error(mock_client_class):
    """Test backend endpoint discovery with connection error."""
    import httpx

    from qualpipe_webapp.frontend.main import (
        BACKEND_ENDPOINTS,
        discover_backend_endpoints,
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = httpx.RequestError("Connection failed")
    mock_client_class.return_value = mock_client

    BACKEND_ENDPOINTS.clear()
    await discover_backend_endpoints()

    # Should fall back to default endpoints
    assert "v1/health" in BACKEND_ENDPOINTS
    assert "v1/ob_date_map" in BACKEND_ENDPOINTS
    assert "v1/data" in BACKEND_ENDPOINTS


# ============================================================
# QUERY PARAMETER VALIDATION TESTS
# ============================================================


def test_validate_query_parameters_success():
    """Test successful query parameter validation."""
    from qualpipe_webapp.frontend.main import (
        BACKEND_ENDPOINTS,
        validate_query_parameters,
    )

    BACKEND_ENDPOINTS["v1/test"] = {
        "methods": {"GET"},
        "schemas": {
            "get_parameters": [
                {"name": "required_param", "required": True},
                {"name": "optional_param", "required": False},
            ]
        },
    }

    # Should not raise exception
    validate_query_parameters(
        "v1/test", "GET", {"required_param": "value1", "optional_param": "value2"}
    )


def test_validate_query_parameters_missing_required():
    """Test query parameter validation with missing required parameter."""
    from qualpipe_webapp.frontend.main import (
        BACKEND_ENDPOINTS,
        validate_query_parameters,
    )

    BACKEND_ENDPOINTS["v1/test"] = {
        "methods": {"GET"},
        "schemas": {
            "get_parameters": [
                {"name": "required_param", "required": True},
                {"name": "optional_param", "required": False},
            ]
        },
    }

    with pytest.raises(HTTPException) as exc_info:
        validate_query_parameters("v1/test", "GET", {"optional_param": "value"})

    assert exc_info.value.status_code == 400
    assert "Missing required parameters" in exc_info.value.detail


def test_validate_query_parameters_unknown():
    """Test query parameter validation with unknown parameter."""
    from qualpipe_webapp.frontend.main import (
        BACKEND_ENDPOINTS,
        validate_query_parameters,
    )

    BACKEND_ENDPOINTS["v1/test"] = {
        "methods": {"GET"},
        "schemas": {"get_parameters": [{"name": "allowed_param", "required": False}]},
    }

    with pytest.raises(HTTPException) as exc_info:
        validate_query_parameters(
            "v1/test", "GET", {"allowed_param": "value", "unknown_param": "value"}
        )

    assert exc_info.value.status_code == 400
    assert "Unknown query parameters" in exc_info.value.detail


def test_validate_query_parameters_no_schema():
    """Test query parameter validation when no schema exists."""
    from qualpipe_webapp.frontend.main import (
        BACKEND_ENDPOINTS,
        validate_query_parameters,
    )

    BACKEND_ENDPOINTS["v1/test"] = {"methods": {"GET"}, "schemas": {}}

    # Should not raise exception when no schema is defined
    validate_query_parameters("v1/test", "GET", {"any_param": "value"})


# ============================================================
# API DOCUMENTATION PROXY TESTS
# ============================================================


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_docs_proxy(mock_client_class):
    """Test the /api/docs endpoint proxy."""
    # Clear BACKEND_ENDPOINTS to ensure this test uses the specific route, not catch-all
    BACKEND_ENDPOINTS.clear()

    # Mock the backend swagger docs response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><head><title>FastAPI</title></head></html>"
    mock_response.content = b"<html><head><title>FastAPI</title></head></html>"
    mock_response.headers = {"content-type": "text/html"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_docs_proxy_error(mock_client_class):
    """Test the /api/docs endpoint proxy with connection error."""
    import httpx

    # Clear BACKEND_ENDPOINTS to ensure this test uses the specific route, not catch-all
    BACKEND_ENDPOINTS.clear()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = httpx.RequestError("Connection failed")
    mock_client_class.return_value = mock_client

    response = client.get("/api/docs")
    assert response.status_code == 503
    assert "text/html" in response.headers["content-type"]
    assert "Error connecting to backend" in response.text
    assert "Connection failed" in response.text


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_redoc_proxy(mock_client_class):
    """Test the /api/redoc endpoint proxy."""
    # Clear BACKEND_ENDPOINTS to ensure this test uses the specific route, not catch-all
    BACKEND_ENDPOINTS.clear()

    # Mock the backend ReDoc response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><head><title>ReDoc</title></head></html>"
    mock_response.content = b"<html><head><title>ReDoc</title></head></html>"
    mock_response.headers = {"content-type": "text/html"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    response = client.get("/api/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    mock_client.get.assert_called_once()


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_redoc_proxy_error(mock_client_class):
    """Test the /api/redoc endpoint proxy with connection error."""
    import httpx

    # Clear BACKEND_ENDPOINTS to ensure this test uses the specific route, not catch-all
    BACKEND_ENDPOINTS.clear()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = httpx.RequestError("Connection failed")
    mock_client_class.return_value = mock_client

    response = client.get("/api/redoc")
    assert response.status_code == 503
    assert "text/html" in response.headers["content-type"]
    assert "Error connecting to backend" in response.text
    assert "Connection failed" in response.text


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_openapi_json_proxy(mock_client_class):
    """Test the /api/openapi.json endpoint proxy with path normalization."""
    # Clear BACKEND_ENDPOINTS to ensure this test uses the specific route, not catch-all
    BACKEND_ENDPOINTS.clear()

    # Mock the backend OpenAPI spec response with paths that have leading slashes
    mock_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API"},
        "paths": {
            "/v1/health": {"get": {"responses": {"200": {"description": "OK"}}}},
            "/v1/data": {"get": {"responses": {"200": {"description": "OK"}}}},
        },
    }
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_spec
    mock_response.headers = {"content-type": "application/json"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    response = client.get("/api/openapi.json")
    assert response.status_code == 200

    result_spec = response.json()

    # Verify server URL is set correctly
    assert result_spec["servers"] == [{"url": "/api"}]

    # Verify paths are normalized (leading slashes removed)
    assert "v1/health" in result_spec["paths"]
    assert "v1/data" in result_spec["paths"]

    # Verify original paths with leading slashes are not present
    assert "/v1/health" not in result_spec["paths"]
    assert "/v1/data" not in result_spec["paths"]

    mock_client.get.assert_called_once()


@patch("qualpipe_webapp.frontend.main.httpx.AsyncClient")
def test_api_openapi_json_proxy_error(mock_client_class):
    """Test the /api/openapi.json endpoint proxy with connection error."""
    import httpx

    # Clear BACKEND_ENDPOINTS to ensure this test uses the specific route, not catch-all
    BACKEND_ENDPOINTS.clear()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = httpx.RequestError("Connection failed")
    mock_client_class.return_value = mock_client

    response = client.get("/api/openapi.json")
    assert response.status_code == 503
    assert "Connection failed" in response.json()["error"]


# ============================================================
# FRONTEND HTML ROUTE TESTS
# ============================================================


def test_auxiliary_subitem_routes():
    """Test auxiliary subitem routes return 501."""
    response = client.get("/Auxiliary/Lidar")
    assert response.status_code == 501
    assert_html_utf8(response)

    response = client.get("/Auxiliary/FRAM")
    assert response.status_code == 501
    assert_html_utf8(response)

    response = client.get("/Auxiliary/Weather Station")
    assert response.status_code == 501
    assert_html_utf8(response)


def test_auxiliary_invalid_subitem():
    """Test auxiliary with invalid subitem returns 404."""
    response = client.get("/Auxiliary/InvalidItem")
    assert response.status_code == 404


def test_invalid_array_element_type():
    """Test invalid array element type returns 404."""
    response = client.get("/InvalidType/pointings")
    assert response.status_code == 404


def test_404_exception_handler():
    """Test the 404 exception handler."""
    response = client.get("/nonexistent-page")
    assert response.status_code == 404
    assert_html_utf8(response)
