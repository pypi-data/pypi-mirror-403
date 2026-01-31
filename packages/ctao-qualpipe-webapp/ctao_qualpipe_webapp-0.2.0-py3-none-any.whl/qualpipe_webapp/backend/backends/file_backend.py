"""
FileBackend module for reading and extracting data from HDF5 files in a directory structure.

Provides the FileBackend class implementing BackendAPI for scanning, parsing, and fetching observation data.
"""

import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import h5py
import hdf5plugin  # noqa: F401

from .base import BackendAPI, DataItem, ObservationInfo

logger = logging.getLogger(__name__)

# HDF5 dataset configuration mapping
DATASET_CONFIGS = [
    {
        "path": "dl1/monitoring/telescope/quality/pedestal_charge_mean/tel_001",
        # Frontend expects this historical key name (see interleaved_pedestals.html)
        "base_key": "interleaved_pedestals_pedestal_mean_charge",
        "title": "Pedestal mean charge",
        "field": "mean",
    },
    {
        "path": "dl1/monitoring/telescope/quality/pedestal_charge_std/tel_001",
        "base_key": "interleaved_pedestals_pedestal_charge_std",
        "title": "Pedestal std charge",
        "field": "mean",
    },
    {
        "path": "dl1/monitoring/telescope/quality/flatfield_charge_mean/tel_001",
        # Frontend expects this key name (see interleaved_flat_field_charge.html)
        "base_key": "interleaved_flat_field_charge_FF_mean_charge",
        "title": "Flatfield mean charge",
        "field": "mean",
    },
    {
        "path": "dl1/monitoring/telescope/quality/flatfield_charge_std/tel_001",
        "base_key": "interleaved_flat_field_charge_FF_charge_std",
        "title": "Flatfield charge std",
        "field": "mean",
    },
    {
        "path": "dl1/monitoring/telescope/quality/flatfield_timing_mean/tel_001",
        # Frontend expects this key name (see interleaved_flat_field_time.html)
        "base_key": "interleaved_flat_field_time_FF_mean_relative_time",
        "title": "Flatfield mean relative time",
        "field": "mean",
    },
    {
        "path": "dl1/monitoring/telescope/quality/flatfield_timing_std/tel_001",
        "base_key": "interleaved_flat_field_time_FF_relative_time_std",
        "title": "Flatfield relative time std",
        "field": "mean",
    },
]


class FileBackend(BackendAPI):
    """
    Backend for reading data directly from HDF5 files.

    Assumes directory structure: /prefix/site/date/files
    """

    def __init__(self, data_dir: str):
        """
        Initialize file backend.

        Args:
            data_dir: Base directory prefix containing site subdirectories (ctao-north, ctao-south)
        """
        self.data_prefix = Path(data_dir)

        if not self.data_prefix.exists():
            raise FileNotFoundError(
                f"Data prefix directory does not exist: {self.data_prefix}"
            )

    def _parse_filename(self, filename: str) -> dict[str, Any] | None:
        """
        Parse telescope filename to extract metadata.

        Supports format: TEL001_SDH0000_20251022T235008_SBID0000000002000000078_OBSID0000000002000000239_CALIB_CHUNK000.mon.dl1.h5

        Creator IDs in SBID/OBSID: 1=SDMC-SUSS, 2=CTAO-North, 3=CTAO-South, 4=SDMC-DPPS
        The creator ID must be the same for both SBID and OBSID (used for cross-validation).
        """
        # Updated pattern to include SDH field (ignored) and new extension format
        pattern = r"TEL(\d+)_SDH\d+_(\d{8}T\d{6})_SBID(\d{19})_OBSID(\d{19})_(.+)\.mon\.dl1\.h5"

        match = re.match(pattern, filename)
        if match:
            tel_id, timestamp, sbid_full, obsid_full, suffix = match.groups()

            # Extract creator ID and actual ID from SBID and OBSID
            # First 10 digits are creator ID, remaining digits are actual ID
            sbid_creator = int(sbid_full[:10])
            sbid_actual = int(sbid_full[10:])
            obsid_creator = int(obsid_full[:10])
            obsid_actual = int(obsid_full[10:])

            # Cross-check: creator ID must be the same for both SBID and OBSID
            if sbid_creator != obsid_creator:
                logger.warning(
                    "Creator ID mismatch in %s: SBID creator=%d, OBSID creator=%d",
                    filename,
                    sbid_creator,
                    obsid_creator,
                )
                return None

            return {
                "tel_id": int(tel_id),
                "timestamp": timestamp,
                "sbid": sbid_actual,  # Use actual SBID for compatibility
                "sbid_full": int(sbid_full),
                "obsid": obsid_actual,  # Use actual OBSID for compatibility
                "obsid_full": int(obsid_full),
                "creator": sbid_creator,  # Single creator field since they must match
                "suffix": suffix,
                "filename": filename,
            }

        return None

    def _extract_dataset_value(
        self, h5_file: h5py.File, dataset_path: str, field: str
    ) -> Any:
        """
        Extract specific dataset value from HDF5 file.

        Args:
            h5_file: Open HDF5 file handle
            dataset_path: Path to the dataset in HDF5 file
            field: Field name within the dataset

        Returns
        -------
            Extracted dataset value or None if not found
        """
        try:
            obj = h5_file.get(dataset_path)
            if obj is None:
                logger.warning("Dataset path not found: %s", dataset_path)
                return None

            # Path may point either to a group that contains datasets (e.g. /.../tel_001/mean)
            # or to a dataset with a compound dtype that contains fields (e.g. /.../tel_001['mean']).
            if isinstance(obj, h5py.Group):
                if field in obj:
                    return obj[field][:]

                logger.warning("Field '%s' not found in group %s", field, dataset_path)
                return None

            if isinstance(obj, h5py.Dataset):
                dtype_fields = getattr(obj.dtype, "fields", None)
                dtype_names = getattr(obj.dtype, "names", None)
                if dtype_fields and field in dtype_fields:
                    return obj[field][:]
                if dtype_names and field in dtype_names:
                    return obj[field][:]

                logger.warning(
                    "Field '%s' not found in dataset %s (dtype=%s)",
                    field,
                    dataset_path,
                    obj.dtype,
                )
                return None

            logger.warning("Unsupported HDF5 object at %s: %s", dataset_path, type(obj))
            return None
        except Exception as e:
            logger.error("Error extracting dataset %s[%s]: %s", dataset_path, field, e)
            return None

    def scan_observations(self) -> list[ObservationInfo]:
        """Scan both sites for available HDF5 files using prefix/site/date/files structure."""
        observations = []

        # Scan both sites
        for site_name in ["ctao-north", "ctao-south"]:
            site_dir = self.data_prefix / site_name
            if not site_dir.exists():
                logger.debug("Site directory not found: %s", site_dir)
                continue

            # Scan through date directories in this site
            for date_dir in site_dir.iterdir():
                # Look for HDF5 files in date directory
                for h5_file in date_dir.glob("*.h5"):
                    parsed = self._parse_filename(h5_file.name)
                    if not parsed:
                        logger.warning("Could not parse filename: %s", h5_file.name)
                        continue

                    try:
                        # Convert timestamp to date
                        datetime_obj = datetime.strptime(
                            parsed["timestamp"], "%Y%m%dT%H%M%S"
                        )
                        date_str = datetime_obj.strftime("%Y-%m-%d")

                        # Convert site directory name to display format
                        site_display = "North" if site_name == "ctao-north" else "South"

                        observation = ObservationInfo(
                            site=site_display,
                            date=date_str,
                            obsid=parsed["obsid"],
                            tel_id=parsed["tel_id"],
                            telescope_type="",  # No longer determining telescope type
                            h5_file=str(h5_file),
                        )
                        observations.append(observation)
                    except ValueError:
                        logger.warning(
                            "Could not parse timestamp from %s", h5_file.name
                        )
                        continue

        return observations

    def get_ob_date_map(self) -> dict[str, list[int]]:
        """Generate observation date mapping."""
        ob_map = defaultdict(list)
        observations = self.scan_observations()

        for obs in observations:
            if obs.obsid not in ob_map[obs.date]:
                ob_map[obs.date].append(obs.obsid)

        # Sort observation IDs for each date
        for date in ob_map:
            ob_map[date].sort()

        return dict(ob_map)

    def fetch_data(
        self,
        obsid: int,
        tel_id: int,
        site: str,
        date: str,
        keys: list[str] | None = None,
    ) -> dict[str, DataItem]:
        """
        Fetch data for specific observation and telescope by extracting from HDF5 on-the-fly.

        Args:
            obsid: Observation ID
            tel_id: Telescope ID
            site: Site name ("North" or "South")
            date: Date string in YYYY-MM-DD format
            keys: Optional list of data keys to fetch
        """
        # Find HDF5 file for this observation and telescope
        h5_file_path = self._find_h5_file(obsid, tel_id, site, date)
        if not h5_file_path:
            raise FileNotFoundError(
                f"No HDF5 file found for observation {obsid} telescope {tel_id} at {site} on {date}"
            )

        return self._extract_hdf5_data(h5_file_path, keys)

    def _find_h5_file(
        self, obsid: int, tel_id: int, site: str, date: str
    ) -> Path | None:
        """Find HDF5 file containing specific observation and telescope using direct path."""
        # Validate and convert site to directory name
        site_lower = site.lower()
        if site_lower == "north":
            site_name = "ctao-north"
        elif site_lower == "south":
            site_name = "ctao-south"
        else:
            logger.warning(
                "Invalid site name: %s. Valid sites are 'North' or 'South'", site
            )
            return None

        # Build direct path to date directory
        date_dir = self.data_prefix / site_name / date

        if not date_dir.exists():
            logger.warning("Date directory not found: %s", date_dir)
            return None

        # Look for HDF5 files in the specific date directory
        for h5_file in date_dir.glob("*.h5"):
            parsed = self._parse_filename(h5_file.name)
            if parsed and parsed["obsid"] == obsid and parsed["tel_id"] == tel_id:
                return h5_file
        return None

    def _extract_hdf5_data(
        self, h5_file_path: Path, keys: list[str] | None = None
    ) -> dict[str, DataItem]:
        data = {}

        try:
            with h5py.File(h5_file_path, "r") as h5file:
                for config in DATASET_CONFIGS:
                    try:
                        values = self._extract_dataset_value(
                            h5file, config["path"], config["field"]
                        )

                        if values is None:
                            continue

                        # Match the previously working behavior:
                        # - convert numpy arrays to python lists
                        # - drop the leading record dimension (usually length-1)
                        # so values[gain] selects gain arrays.
                        try:
                            values_list: Any = values.tolist()  # numpy -> list
                        except Exception:
                            values_list = values
                        if isinstance(values_list, list) and len(values_list) == 1:
                            values_list = values_list[0]

                        # Generate plot configurations for both gains
                        for gain in [0, 1]:
                            if (
                                isinstance(values_list, list)
                                and len(values_list) > gain
                            ):
                                gain_values = values_list[gain]
                            else:
                                gain_values = []
                            pixel_ids = list(range(len(gain_values)))

                            # Generate the three plot types
                            plots = self._generate_plot_configs(
                                config["base_key"],
                                config["title"],
                                gain,
                                gain_values,
                                pixel_ids,
                            )

                            # Filter by requested keys if specified
                            for plot_key, plot_data in plots.items():
                                if keys is None or plot_key in keys:
                                    data[plot_key] = DataItem(**plot_data)

                    except Exception as e:
                        logger.warning("Error processing %s: %s", config["path"], e)
                        continue

        except Exception as e:
            raise RuntimeError(f"Error reading HDF5 file {h5_file_path}: {e}")

        return data

    def _generate_plot_configs(
        self,
        base_key: str,
        title: str,
        gain: int,
        gain_values: list[float],
        pixel_ids: list[int],
    ) -> dict[str, dict]:
        """Generate the three plot configurations: 3D cameraview, 2D scatter, 1D histogram."""
        plots = {}

        # 3D Camera view
        plots[f"{base_key}_3D_gain_{gain}_cameraView"] = {
            "fetchedData": {"x": gain_values},
            "fetchedMetadata": {
                "plotConfiguration": {
                    "x": {"label": "X position", "scale": "linear"},
                    "y": {"label": "Y position", "scale": "linear"},
                    "plotType": "cameraview",
                    "title": f"{title} (Gain {gain})",
                }
            },
        }

        # 2D Scatter plot
        plots[f"{base_key}_2D_gain_{gain}"] = {
            "fetchedData": {"x": pixel_ids, "y": gain_values},
            "fetchedMetadata": {
                "criteriaReport": {},
                "plotConfiguration": {
                    "x": {"label": "Pixel ID", "scale": "linear"},
                    "y": {"label": title, "scale": "linear"},
                    "plotType": "scatterplot",
                    "line": "none",
                    "title": f"{title} (Gain {gain})",
                },
            },
        }

        # 1D Histogram
        plots[f"{base_key}_1D_gain_{gain}"] = {
            "fetchedData": {"x": gain_values},
            "fetchedMetadata": {
                "criteriaReport": {},
                "plotConfiguration": {
                    "x": {"label": title, "scale": "linear"},
                    "y": {"label": "Count", "scale": "linear"},
                    "plotType": "histogram1d",
                    "title": f"{title} (Gain {gain})",
                },
            },
        }

        # Frontend pages request keys without gain suffix (e.g. *_3D, *_2D, *_1D).
        # Provide only gain-0 views so there is a single set of plots.
        if gain == 0:
            plots[f"{base_key}_2D"] = plots[f"{base_key}_2D_gain_{gain}"].copy()
            plots[f"{base_key}_2D"]["fetchedMetadata"] = {
                **plots[f"{base_key}_2D_gain_{gain}"]["fetchedMetadata"],
                "plotConfiguration": {
                    **plots[f"{base_key}_2D_gain_{gain}"]["fetchedMetadata"][
                        "plotConfiguration"
                    ],
                    "title": f"{title} vs Pixel ID",
                },
            }

            plots[f"{base_key}_1D"] = plots[f"{base_key}_1D_gain_{gain}"].copy()
            plots[f"{base_key}_1D"]["fetchedMetadata"] = {
                **plots[f"{base_key}_1D_gain_{gain}"]["fetchedMetadata"],
                "plotConfiguration": {
                    **plots[f"{base_key}_1D_gain_{gain}"]["fetchedMetadata"][
                        "plotConfiguration"
                    ],
                    "title": f"{title} Histogram",
                },
            }

            plots[f"{base_key}_3D"] = plots[
                f"{base_key}_3D_gain_{gain}_cameraView"
            ].copy()
            plots[f"{base_key}_3D"]["fetchedMetadata"] = {
                **plots[f"{base_key}_3D_gain_{gain}_cameraView"]["fetchedMetadata"],
                "plotConfiguration": {
                    **plots[f"{base_key}_3D_gain_{gain}_cameraView"]["fetchedMetadata"][
                        "plotConfiguration"
                    ],
                    "title": f"{title} CDF",
                },
            }

        return plots
