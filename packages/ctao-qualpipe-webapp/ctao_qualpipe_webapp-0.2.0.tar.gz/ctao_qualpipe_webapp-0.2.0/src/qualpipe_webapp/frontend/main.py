"""
Main application module for the QualPipe frontend.

This module sets up the FastAPI application, mounts static files, and defines
routes for rendering HTML templates using Jinja2.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

import httpx
import sass
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(level=logging.INFO)

# Store discovered backend endpoints with methods and schemas
BACKEND_ENDPOINTS = {}  # {path: {"methods": set, "schemas": dict}}


def _extract_endpoint_schemas(method_info: dict, method: str) -> dict:
    """Extract schemas from a method definition."""
    schemas = {}
    if "parameters" in method_info:
        schemas[f"{method}_parameters"] = method_info["parameters"]
    if "requestBody" in method_info:
        schemas[f"{method}_requestBody"] = method_info["requestBody"]
    if "responses" in method_info:
        schemas[f"{method}_responses"] = method_info["responses"]
    return schemas


def _parse_openapi_path(path: str, path_info: dict) -> tuple[str, dict]:
    """Parse a single OpenAPI path and return endpoint info."""
    clean_path = path.lstrip("/")
    allowed_methods = set()
    endpoint_schemas = {}

    for method, method_info in path_info.items():
        if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            allowed_methods.add(method.upper())
            endpoint_schemas.update(_extract_endpoint_schemas(method_info, method))

    return clean_path, {
        "methods": allowed_methods,
        "schemas": endpoint_schemas,
    }


def _use_fallback_endpoints():
    """Set fallback endpoints when discovery fails."""
    global BACKEND_ENDPOINTS
    BACKEND_ENDPOINTS.update(
        {
            "v1/health": {"methods": {"GET"}, "schemas": {}},
            "v1/ob_date_map": {"methods": {"GET"}, "schemas": {}},
            "v1/data": {"methods": {"GET"}, "schemas": {}},
        }
    )
    logging.info("Using fallback endpoints")


async def discover_backend_endpoints():
    """Discover available endpoints from backend OpenAPI spec."""
    global BACKEND_ENDPOINTS
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/openapi.json")

        if response.status_code != 200:
            logging.error("Failed to get OpenAPI spec: %d", response.status_code)
            _use_fallback_endpoints()
            return

        spec = response.json()
        paths = spec.get("paths", {})

        for path, path_info in paths.items():
            clean_path, endpoint_info = _parse_openapi_path(path, path_info)
            BACKEND_ENDPOINTS[clean_path] = endpoint_info

            logging.info(
                "Discovered endpoint: %s with methods: %s",
                clean_path,
                ", ".join(sorted(endpoint_info["methods"])),
            )

        logging.info("Total discovered endpoints: %d", len(BACKEND_ENDPOINTS))

    except Exception as e:
        logging.error("Error discovering backend endpoints: %s", e)
        _use_fallback_endpoints()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize backend endpoint discovery on startup."""
    await discover_backend_endpoints()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for demo/demo testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _valid_url(u):
    p = urlparse(u)
    return p.scheme in ("http", "https") and bool(p.netloc)


# Backend service URL (use DNS Kubernetes)
BACKEND_URL = os.getenv("BACKEND_URL") or "http://qualpipe-webapp-backend:8000"
if not _valid_url(BACKEND_URL):
    raise ValueError(f"Invalid BACKEND_URL: {BACKEND_URL}")


project_root = Path(__file__).resolve().parents[0]
static_path = project_root / "static"
view_path = project_root / "view"

# Compile SCSS file to CSS
sass.compile(dirname=(str(static_path / "css"), str(static_path / "css")))

app.mount("/static", StaticFiles(directory=static_path), name="static")
view = Jinja2Templates(directory=view_path)


def validate_query_parameters(path: str, method: str, query_params: dict):
    """Validate query parameters against OpenAPI schema."""
    endpoint_info = BACKEND_ENDPOINTS.get(path, {})
    schemas = endpoint_info.get("schemas", {})
    parameters_key = f"{method.lower()}_parameters"

    if parameters_key in schemas:
        required_params = []
        allowed_params = set()

        for param in schemas[parameters_key]:
            param_name = param.get("name")
            if param_name:
                allowed_params.add(param_name)
                if param.get("required", False):
                    required_params.append(param_name)

        # Check for unknown parameters
        unknown_params = set(query_params.keys()) - allowed_params
        if unknown_params:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown query parameters: {', '.join(unknown_params)}",
            )

        # Check for missing required parameters
        missing_params = set(required_params) - set(query_params.keys())
        if missing_params:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required parameters: {', '.join(missing_params)}",
            )


async def proxy_backend_endpoint(request: Request, path: str):
    """Proxy specific backend endpoint with method and schema validation."""
    # Validate endpoint exists
    path = path.lstrip("/")
    if path not in BACKEND_ENDPOINTS:
        raise HTTPException(status_code=404, detail=f"Endpoint not found: {path}")

    endpoint_info = BACKEND_ENDPOINTS[path]
    allowed_methods = endpoint_info.get("methods", set())

    # Validate HTTP method
    if request.method not in allowed_methods:
        raise HTTPException(
            status_code=405,
            detail=f"Method {request.method} not allowed for {path}. Allowed: {', '.join(sorted(allowed_methods))}",
        )

    # Validate query parameters if schema is available
    query_params = dict(request.query_params)
    if query_params:
        validate_query_parameters(path, request.method, query_params)

    # Build backend URL
    from urllib.parse import quote, urljoin

    safe_path = quote(path, safe="/")
    backend_url = urljoin(f"{BACKEND_URL}/", safe_path)

    # Build query params
    query_params = str(request.url.query)
    if query_params:
        backend_url = f"{backend_url}?{query_params}"

    # Copy headers (except host)
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Forward request to backend
            if request.method == "GET":
                response = await client.get(backend_url, headers=headers)
            elif request.method == "POST":
                body = await request.body()
                response = await client.post(backend_url, content=body, headers=headers)
            elif request.method == "PUT":
                body = await request.body()
                response = await client.put(backend_url, content=body, headers=headers)
            elif request.method == "DELETE":
                response = await client.delete(backend_url, headers=headers)
            elif request.method == "PATCH":
                body = await request.body()
                response = await client.patch(
                    backend_url, content=body, headers=headers
                )
            else:
                return JSONResponse({"error": "Method not allowed"}, status_code=405)

            # Return response from backend
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
        except httpx.RequestError as e:
            return JSONResponse(
                content={"error": f"Backend connection error: {str(e)}"},
                status_code=503,
            )


@app.get("/api/_debug/endpoints")
async def debug_endpoints():
    """Debug endpoint to show discovered backend endpoints."""
    return {"endpoints": BACKEND_ENDPOINTS, "total_count": len(BACKEND_ENDPOINTS)}


template_404 = "templates/404.html"


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes.

    Returns
    -------
    dict
        A simple status dictionary indicating the service is healthy.
    """
    return {"status": "ok", "service": "frontend"}


# ============================================================
# PROXY ROUTES FOR BACKEND API DOCS (MUST BE BEFORE CATCH-ALL)
# ============================================================


@app.get("/api/docs", response_class=HTMLResponse)
async def proxy_swagger_ui(request: Request):
    """Proxy Swagger UI from backend."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/docs",
                headers={
                    k: v for k, v in request.headers.items() if k.lower() != "host"
                },
            )
            return HTMLResponse(
                content=response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.RequestError as e:
            return HTMLResponse(
                content=f"<h1>Error connecting to backend</h1><pre>{str(e)}</pre>",
                status_code=503,
            )


@app.get("/api/redoc", response_class=HTMLResponse)
async def proxy_redoc(request: Request):
    """Proxy ReDoc from backend."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/redoc",
                headers={
                    k: v for k, v in request.headers.items() if k.lower() != "host"
                },
            )
            return HTMLResponse(
                content=response.text,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.RequestError as e:
            return HTMLResponse(
                content=f"<h1>Error connecting to backend</h1><pre>{str(e)}</pre>",
                status_code=503,
            )


@app.get("/api/openapi.json", response_class=JSONResponse)
async def proxy_openapi_spec(request: Request):
    """Proxy OpenAPI spec from backend with path normalization."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/openapi.json",
                headers={
                    k: v for k, v in request.headers.items() if k.lower() != "host"
                },
            )

            # Get the original spec and rewrite paths to be absolute
            spec = response.json()

            # Set server URL to /api
            spec["servers"] = [{"url": "/api"}]

            # Remove leading slashes from paths so they combine cleanly with server URL
            if "paths" in spec:
                new_paths = {}
                for path, path_info in spec["paths"].items():
                    # Remove leading slash: /v1/health -> v1/health
                    # So /api + v1/health = /api/v1/health (not /api//v1/health)
                    clean_path = path.lstrip("/")
                    new_paths[clean_path] = path_info
                spec["paths"] = new_paths

            return JSONResponse(
                content=spec,
                status_code=response.status_code,
            )
        except httpx.RequestError as e:
            return JSONResponse(
                content={"error": str(e)},
                status_code=503,
            )


# ============================================================
# CATCH-ALL API PROXY (MUST BE AFTER ALL SPECIFIC API ROUTES)
# ============================================================


# Separate routes for each HTTP method to avoid Swagger UI confusion
@app.get("/api/{path:path}")
async def proxy_get(request: Request, path: str):
    """GET requests to backend endpoints."""
    return await proxy_backend_endpoint(request, path)


@app.post("/api/{path:path}")
async def proxy_post(request: Request, path: str):
    """POST requests to backend endpoints."""
    return await proxy_backend_endpoint(request, path)


@app.put("/api/{path:path}")
async def proxy_put(request: Request, path: str):
    """PUT requests to backend endpoints."""
    return await proxy_backend_endpoint(request, path)


@app.delete("/api/{path:path}")
async def proxy_delete(request: Request, path: str):
    """DELETE requests to backend endpoints."""
    return await proxy_backend_endpoint(request, path)


@app.patch("/api/{path:path}")
async def proxy_patch(request: Request, path: str):
    """PATCH requests to backend endpoints."""
    return await proxy_backend_endpoint(request, path)


# ============================================================
# FRONTEND HTML ROUTES
# ============================================================


@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    """Create homepage."""
    return view.TemplateResponse(
        request=request, name="pages/home.html", context={"array_element": "home"}
    )


@app.get("/LSTs", response_class=HTMLResponse)
async def read_lst(request: Request):  # noqa: N802
    """Create LSTs placeholder."""
    return view.TemplateResponse(
        request=request,
        name="pages/array_element_type/LSTs-summary.html",
        context={"array_element": "LSTs"},
    )


@app.get("/MSTs", response_class=HTMLResponse)
async def read_mst(request: Request):  # noqa: N802
    """Create MSTs placeholder."""
    return view.TemplateResponse(
        request=request,
        name="pages/array_element_type/MSTs-summary.html",
        context={"array_element": "MSTs"},
    )


@app.get("/SSTs", response_class=HTMLResponse)
async def read_sst(request: Request):  # noqa: N802
    """Create SSTs placeholder."""
    return view.TemplateResponse(
        request=request,
        name="pages/array_element_type/SSTs-summary.html",
        context={"array_element": "SSTs"},
    )


@app.get("/Auxiliary", response_class=HTMLResponse)
async def read_auxiliary(request: Request):  # noqa: N802
    """Create Auxiliary placeholder."""
    return view.TemplateResponse(
        request=request,
        name="templates/501.html",
        context={"array_element": "Auxiliary"},
        status_code=501,
    )


@app.get("/{array_element_type}/{subitem}", response_class=HTMLResponse)
async def read_array_element_type_subitem(
    array_element_type: str, subitem: str, request: Request
):
    """Create ArrayElementType subitem pages."""
    # Check if the ArrayElementType is valid
    valid_array_element_types = [
        "LSTs",
        "MSTs",
        "SSTs",
        "Auxiliary",
    ]
    if array_element_type not in valid_array_element_types:
        return view.TemplateResponse(
            request=request,
            name=template_404,
            status_code=404,
        )
    if array_element_type in ["Auxiliary"]:
        # Check if the subitem is valid
        valid_subitems = [
            "Lidar",
            "FRAM",
            "Weather Station",
        ]
        if subitem not in valid_subitems:
            return view.TemplateResponse(
                request=request,
                name=template_404,
                status_code=404,
            )
        return view.TemplateResponse(
            request=request,
            name="templates/501.html",
            context={
                "array_element": array_element_type,
                "active_subitem": subitem,
                "subitem": subitem.replace("_", " "),
            },
            status_code=501,
        )
    else:
        # Check if the subitem is valid
        valid_subitems = [
            "event_rates",
            "trigger_tags",
            "pointings",
            "interleaved_pedestals",
            "interleaved_flat_field_charge",
            "interleaved_flat_field_time",
            "cosmics",
            "pixel_problems",
            "muons",
            "interleaved_pedestals_averages",
            "interleaved_FF_averages",
            "cosmics_averages",
        ]
        if subitem not in valid_subitems:
            return view.TemplateResponse(
                request=request,
                name=template_404,
                status_code=404,
            )

        # Render the appropriate template based on the subitem
        return view.TemplateResponse(
            request=request,
            name=f"pages/array_element_type/{subitem}.html",
            context={
                "array_element": array_element_type,
                "active_subitem": subitem,
                "subitem": subitem.replace("_", " "),
            },
        )


@app.exception_handler(404)
async def not_found(request: Request, exc):
    """Handle 404 errors."""
    return view.TemplateResponse(
        request=request,
        name=template_404,
        status_code=404,
    )
