"""Factory for creating backend API instances based on environment configuration.

This module provides the create_backend function, which instantiates the appropriate
backend (e.g., FileBackend) according to environment variables.
"""

import os
from pathlib import Path

from .base import BackendAPI
from .file_backend import FileBackend


def create_backend() -> BackendAPI:
    """
    Create backend instance based on environment configuration.

    Environment Variables
    ---------------------
    BACKEND_TYPE : str, default="file"
        Backend type to use ("file", "sqlite", "postgres", etc.)
    DATA_DIR : str, default="/app/data"
        Base directory containing site subdirectories (ctao-north, ctao-south)
    """
    backend_type = os.environ.get("BACKEND_TYPE", "file").lower()
    data_dir = Path(os.environ.get("DATA_DIR", "/app/data"))

    if backend_type == "file":
        return FileBackend(data_dir=data_dir)
    elif backend_type == "postgres":
        # Future: PostgresBackend(db_url=os.environ.get("DB_URL"))
        raise NotImplementedError("PostgreSQL backend not yet implemented")
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
