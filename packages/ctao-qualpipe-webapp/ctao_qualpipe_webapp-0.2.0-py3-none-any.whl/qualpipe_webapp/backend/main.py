"""
FastAPI application to serve data for a specific observation.

This application provides endpoints to retrieve data for a specific observation
based on site, date, observation number, telescope type, and telescope ID.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from .backends.base import BackendAPI
from .backends.factory import create_backend


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    app.state.backend = create_backend()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    lifespan=lifespan,
    title="QualPipe Backend API",
    root_path="/api",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/health")
def health_check():
    """Health check endpoint for Kubernetes probes.

    Returns
    -------
    dict
        A simple status dictionary indicating the service is healthy.
    """
    return {"status": "ok", "service": "backend"}


def get_backend(request: Request) -> BackendAPI:
    """Dependency injection for backend."""
    return request.app.state.backend


@app.get("/v1/ob_date_map")
async def get_ob_date_map(backend: BackendAPI = Depends(get_backend)):
    """Get observation date mapping by scanning data files."""
    # Run in threadpool since HDF5 operations are blocking
    return await run_in_threadpool(backend.get_ob_date_map)


@app.get("/v1/data")
async def get_data(
    site: str,
    date: str,
    ob: int,
    telescope_type: str,
    telescope_id: int,
    backend: BackendAPI = Depends(get_backend),
):
    """
    Retrieve data for a specific observation and telescope.

    Parameters
    ----------
    site : str
        The site identifier (e.g., 'North', 'South').
    date : str
        The observation date in 'YYYY-MM-DD' format.
    ob : int
        The observation block number (OBSID).
    telescope_type : str
        The type of telescope ('LST', 'MST', or 'SST').
    telescope_id : int
        The unique identifier for the telescope.

    Returns
    -------
    dict
        The data extracted from HDF5 files for the specified observation.

    Raises
    ------
    HTTPException
        If the telescope type is invalid, the data file does not exist, or an
        error occurs while reading the file.
    """
    # Validate telescope type
    if telescope_type not in {"LST", "MST", "SST"}:
        raise HTTPException(status_code=400, detail="Invalid telescope type")

    try:
        # Fetch data using backend (in threadpool for blocking I/O)
        data = await run_in_threadpool(
            backend.fetch_data,
            ob,
            telescope_id,
            site,
            date,
            None,
        )
        return data
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"No data found for observation {ob}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@app.get("/v1/telescope_info/{obsid}")
async def get_telescope_info(obsid: int, backend: BackendAPI = Depends(get_backend)):
    """Get telescope info for observation."""
    observations = await run_in_threadpool(backend.scan_observations)
    for obs in observations:
        if obs.obsid == obsid:
            return obs.dict()
    raise HTTPException(
        status_code=404, detail=f"No telescope info found for observation {obsid}"
    )
