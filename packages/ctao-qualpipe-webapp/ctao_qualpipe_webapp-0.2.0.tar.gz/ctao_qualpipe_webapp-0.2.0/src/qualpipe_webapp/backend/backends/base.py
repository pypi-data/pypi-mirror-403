"""
Base backend interface and data models for qualpipe-webapp.

Defines abstract classes and Pydantic models for representing observation
information, data items, and the backend API contract. All backend
implementations should inherit from BackendAPI and implement its methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ObservationInfo(BaseModel):
    """Information about an available observation."""

    site: str
    date: str
    obsid: int
    tel_id: int
    telescope_type: str
    h5_file: str | None = None


class DataItem(BaseModel):
    """Single data item with plot data and metadata."""

    # Accept both snake_case (internal) and the camelCase keys used by the frontend.
    model_config = ConfigDict(populate_by_name=True)

    fetched_data: Mapping[str, Any] = Field(alias="fetchedData")
    fetched_metadata: Mapping[str, Any] = Field(alias="fetchedMetadata")


class BackendAPI(ABC):
    """
    Abstract backend interface for data retrieval.

    All backends (file, DB, etc.) must implement these methods.
    """

    @abstractmethod
    def scan_observations(self) -> list[ObservationInfo]:
        """Scan storage and return available observations."""

    @abstractmethod
    def get_ob_date_map(self) -> Mapping[str, list[int]]:
        """Return mapping of date strings to observation IDs.

        Format: {"2025-10-22": [20251022230327, ...], ...}
        """

    @abstractmethod
    def fetch_data(
        self,
        obsid: int,
        tel_id: int,
        site: str,
        date: str,
        keys: list[str] | None = None,
    ) -> Mapping[str, DataItem]:
        """
        Fetch data for specific observation and telescope.

        Parameters
        ----------
        obsid : int
            Observation ID
        keys : Optional[List[str]]
            Specific data keys to fetch (None = all available)

        Returns
        -------
        Mapping[str, DataItem]
            Dictionary mapping data keys to DataItem objects
        """
