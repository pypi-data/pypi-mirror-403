"""
Test configuration and fixtures for QualPipe backend tests.

This module provides fixtures for managing test data from the DPPS test data repository,
using ctapipe's get_dataset_path utility with QualPipe-specific defaults.

Test data is intentionally hardcoded and can be staged into the dev/kind-mounted
directory (data/k8s) after tests complete.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from ctapipe.utils.datasets import get_dataset_path

from qualpipe_webapp.backend.backends.file_backend import FileBackend

# Default URL for QualPipe test data
DEFAULT_QUALPIPE_URL = (
    "https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/qualpipe-test-data/"
)

# Test data files available for QualPipe tests
TEST_FILES = [
    "TEL001_SDH0000_20251022T230327_SBID0000000002000000076_OBSID0000000002000000232_CALIB_CHUNK000.mon.dl1.h5",
    "TEL001_SDH0000_20251022T235008_SBID0000000002000000078_OBSID0000000002000000239_CALIB_CHUNK000.mon.dl1.h5",
]

# Hardcoded dev data layout used by FileBackend and kind/dev chart.
STAGE_DATE = "2025-10-22"
STAGE_SITES = ["ctao-north", "ctao-south"]
STAGE_DIR_RELATIVE_TO_REPO_ROOT = Path("data") / "k8s"


def _repo_root() -> Path:
    """Return repository root based on this conftest.py location."""
    # conftest.py -> tests -> backend -> qualpipe_webapp -> src -> repo_root
    return Path(__file__).resolve().parents[4]


def _stage_test_files(dest_dir: Path, files: list[Path]) -> None:
    """Copy local test files into <dest>/<site>/<date>/, creating directories as needed."""
    for site in STAGE_SITES:
        target_dir = dest_dir / site / STAGE_DATE
        target_dir.mkdir(parents=True, exist_ok=True)
        for src in files:
            shutil.copy2(src, target_dir / src.name)


def _populate_multi_site_data_dir(
    dest_dir: Path, sample_h5_files: dict[str, Path]
) -> None:
    """Populate a directory with the same content as the multi-site backend fixture."""
    north_date_dir = dest_dir / STAGE_SITES[0] / STAGE_DATE
    south_date_dir = dest_dir / STAGE_SITES[1] / STAGE_DATE
    north_date_dir.mkdir(parents=True, exist_ok=True)
    south_date_dir.mkdir(parents=True, exist_ok=True)

    for _filename, file_path in sample_h5_files.items():
        shutil.copy2(file_path, north_date_dir)
        shutil.copy2(file_path, south_date_dir)


@pytest.fixture(scope="session")
def sample_h5_files():
    """Fixture providing both HDF5 test files."""
    # Download both test files using ctapipe's get_dataset_path
    files = {}
    for filename in TEST_FILES:
        files[filename] = get_dataset_path(filename, url=DEFAULT_QUALPIPE_URL)
    return files


@pytest.fixture(scope="session")
def sample_h5_file(sample_h5_files):
    """Fixture providing the first sample HDF5 test file (for backward compatibility)."""
    return sample_h5_files[TEST_FILES[0]]


@pytest.fixture(scope="session", params=TEST_FILES)
def parameterized_h5_file(request):
    """Fixture providing each test file as a parameter for parameterized tests."""
    return get_dataset_path(request.param, url=DEFAULT_QUALPIPE_URL)


@pytest.fixture()
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture()
def backend_with_data(temp_data_dir, sample_h5_file):
    """Create a FileBackend with sample data in proper directory structure."""
    # Create proper directory structure: prefix/site/date/files
    north_date_dir = temp_data_dir / STAGE_SITES[0] / STAGE_DATE
    north_date_dir.mkdir(parents=True)

    # Copy sample file to the proper location
    shutil.copy2(sample_h5_file, north_date_dir)

    # Create backend
    backend = FileBackend(data_dir=str(temp_data_dir))

    return backend, temp_data_dir


@pytest.fixture()
def empty_backend(temp_data_dir):
    """Create a FileBackend with empty directory structure."""
    # Create empty site directories
    (temp_data_dir / "ctao-north").mkdir(parents=True)
    (temp_data_dir / "ctao-south").mkdir(parents=True)

    return FileBackend(data_dir=str(temp_data_dir))


@pytest.fixture()
def multi_site_backend(temp_data_dir, sample_h5_files):
    """Create a FileBackend with data in multiple sites."""
    _populate_multi_site_data_dir(temp_data_dir, sample_h5_files)

    return FileBackend(data_dir=str(temp_data_dir))


@pytest.fixture()
def staged_multi_site_data_dir_for_dev(temp_data_dir, sample_h5_files) -> Path:
    """Stage a multi-site data dir into data/k8s for dev/kind mounting.

    This fixture is meant to be run explicitly (e.g. by a dedicated pytest test)
    to create the directory structure expected by FileBackend:

      data/k8s/ctao-north/2025-10-22/*.h5
      data/k8s/ctao-south/2025-10-22/*.h5
    """
    _populate_multi_site_data_dir(temp_data_dir, sample_h5_files)

    dest = _repo_root() / STAGE_DIR_RELATIVE_TO_REPO_ROOT
    for site in STAGE_SITES:
        staged_site_date_dir = dest / site / STAGE_DATE
        if staged_site_date_dir.exists():
            shutil.rmtree(staged_site_date_dir)

    for site in STAGE_SITES:
        src_site_date_dir = temp_data_dir / site / STAGE_DATE
        dest_site_date_dir = dest / site / STAGE_DATE
        dest_site_date_dir.mkdir(parents=True, exist_ok=True)
        for h5 in src_site_date_dir.glob("*.h5"):
            shutil.copy2(h5, dest_site_date_dir / h5.name)

    return dest


@pytest.fixture()
def backend_with_both_files(temp_data_dir, sample_h5_files):
    """Create a FileBackend with both test files in one site."""
    # Create directory structure for north site
    north_date_dir = temp_data_dir / STAGE_SITES[0] / STAGE_DATE
    north_date_dir.mkdir(parents=True)

    # Copy both sample files to the location
    for filename, file_path in sample_h5_files.items():
        shutil.copy2(file_path, north_date_dir)

    # Create backend
    backend = FileBackend(data_dir=str(temp_data_dir))

    return backend, temp_data_dir


@pytest.fixture()
def tmp_test_data_dir():
    """
    Fixture providing a temporary directory for test data.

    This is useful for tests that need to create temporary files
    or modify test data without affecting the cached versions.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="qualpipe_tmp_test_"))
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
