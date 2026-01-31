"""
Test file backend implementation.
"""

from unittest.mock import patch

import pytest

from qualpipe_webapp.backend.backends.base import ObservationInfo
from qualpipe_webapp.backend.backends.factory import create_backend
from qualpipe_webapp.backend.backends.file_backend import FileBackend


class TestFileBackendFactory:
    """Test backend creation via factory."""

    def test_create_file_backend(self, temp_data_dir):
        """Test creating file backend via factory."""
        with patch.dict(
            "os.environ", {"BACKEND_TYPE": "file", "DATA_DIR": str(temp_data_dir)}
        ):
            backend = create_backend()
            assert isinstance(backend, FileBackend)
            assert backend.data_prefix == temp_data_dir

    def test_factory_invalid_backend(self):
        """Test factory with invalid backend type."""
        with patch.dict("os.environ", {"BACKEND_TYPE": "invalid"}):
            with pytest.raises(ValueError, match="Unknown backend type"):
                create_backend()


class TestFileBackendEmpty:
    """Test file backend with empty data."""

    def test_scan_empty_directory(self, empty_backend):
        """Test scanning empty directory."""
        observations = empty_backend.scan_observations()
        assert observations == []

    def test_ob_date_map_empty(self, empty_backend):
        """Test getting observation date map from empty directory."""
        ob_map = empty_backend.get_ob_date_map()
        assert ob_map == {}

    def test_fetch_data_no_file(self, empty_backend):
        """Test fetching data when no file exists."""
        with pytest.raises(FileNotFoundError, match="No HDF5 file found"):
            empty_backend.fetch_data(
                obsid=12345, tel_id=1, site="North", date="2025-10-22"
            )


class TestFileBackendWithData:
    """Test file backend with actual data files."""

    def test_scan_observations_with_data(self, backend_with_data):
        """Test scanning observations with actual HDF5 file."""
        backend, _ = backend_with_data
        observations = backend.scan_observations()

        assert len(observations) == 1
        obs = observations[0]
        assert isinstance(obs, ObservationInfo)
        assert obs.site == "North"
        assert obs.date == "2025-10-22"
        assert obs.obsid == 232
        assert obs.tel_id == 1
        assert obs.h5_file.endswith(".h5")

    def test_ob_date_map_with_data(self, backend_with_data):
        """Test observation date mapping with data."""
        backend, _ = backend_with_data
        ob_map = backend.get_ob_date_map()

        assert "2025-10-22" in ob_map
        assert 232 in ob_map["2025-10-22"]

    def test_parse_filename(self, backend_with_data):
        """Test filename parsing functionality."""
        backend, _ = backend_with_data

        # Test valid filename with new format
        parsed = backend._parse_filename(
            "TEL001_SDH0000_20251022T230327_SBID0000000002000000076_OBSID0000000002000000232_CALIB_CHUNK000.mon.dl1.h5"
        )
        assert parsed is not None
        assert parsed["tel_id"] == 1
        assert parsed["timestamp"] == "20251022T230327"
        assert parsed["sbid"] == 76
        assert parsed["obsid"] == 232
        assert parsed["creator"] == 2  # CTAO-North

        # Test invalid filename
        parsed = backend._parse_filename("invalid_filename.h5")
        assert parsed is None

        # Test creator mismatch validation
        parsed = backend._parse_filename(
            "TEL001_SDH0000_20251022T230327_SBID0000000002000000076_OBSID0000000003000000232_CALIB_CHUNK000.mon.dl1.h5"
        )
        assert parsed is None  # Should reject due to creator mismatch

    def test_find_h5_file(self, backend_with_data):
        """Test finding HDF5 files by obsid and tel_id."""
        backend, _ = backend_with_data

        # Test finding existing file
        h5_file = backend._find_h5_file(
            obsid=232, tel_id=1, site="North", date="2025-10-22"
        )
        assert h5_file is not None
        assert h5_file.name.endswith(".h5")

        # Test file not found
        h5_file = backend._find_h5_file(
            obsid=999, tel_id=1, site="North", date="2025-10-22"
        )
        assert h5_file is None

        # Test wrong site
        h5_file = backend._find_h5_file(
            obsid=232, tel_id=1, site="South", date="2025-10-22"
        )
        assert h5_file is None

    def test_fetch_data_integration(self, backend_with_data):
        """Test complete data fetching workflow."""
        backend, _ = backend_with_data

        # This should work if the HDF5 file has the expected structure
        data_items = backend.fetch_data(
            obsid=232, tel_id=1, site="North", date="2025-10-22"
        )
        # Should return a dictionary (possibly empty if no matching datasets found)
        assert isinstance(data_items, dict)


class TestFileBackendMultiSite:
    """Test file backend with multiple sites."""

    def test_scan_observations_multi_site(self, multi_site_backend):
        """Test scanning observations across multiple sites."""
        observations = multi_site_backend.scan_observations()

        # Should find both files in both North and South sites (2 files × 2 sites = 4 observations)
        assert len(observations) == 4

        sites = [obs.site for obs in observations]
        assert "North" in sites
        assert "South" in sites

        # Should have both obsids (232 and 239) from the two test files
        obsids = [obs.obsid for obs in observations]
        assert 232 in obsids
        assert 239 in obsids

        # All observations should have same tel_id and date
        for obs in observations:
            assert obs.tel_id == 1
            assert obs.date == "2025-10-22"

    def test_ob_date_map_multi_site(self, multi_site_backend):
        """Test observation date mapping with multiple sites."""
        ob_map = multi_site_backend.get_ob_date_map()

        assert "2025-10-22" in ob_map
        # Should list both unique obsids, sorted
        expected_obsids = sorted([232, 239])
        assert ob_map["2025-10-22"] == expected_obsids

    def test_scan_observations_both_files(self, backend_with_both_files):
        """Test scanning observations with both test files in one site."""
        backend, _ = backend_with_both_files
        observations = backend.scan_observations()

        # Should find both files in North site
        assert len(observations) == 2

        # All should be from North site
        for obs in observations:
            assert obs.site == "North"
            assert obs.date == "2025-10-22"
            assert obs.tel_id == 1

        # Should have both obsids
        obsids = [obs.obsid for obs in observations]
        assert 232 in obsids
        assert 239 in obsids


class TestFileBackendErrorHandling:
    """Test error handling in file backend."""

    def test_nonexistent_data_dir(self):
        """Test backend with non-existent data directory."""
        with pytest.raises(
            FileNotFoundError, match="Data prefix directory does not exist"
        ):
            FileBackend(data_dir="/completely/nonexistent/path")

    def test_invalid_site_name(self, backend_with_data):
        """Test fetch_data with invalid site name."""
        backend, _ = backend_with_data

        with pytest.raises(FileNotFoundError, match="No HDF5 file found"):
            backend.fetch_data(obsid=232, tel_id=1, site="Invalid", date="2025-10-22")

    def test_invalid_date(self, backend_with_data):
        """Test fetch_data with invalid date."""
        backend, _ = backend_with_data

        with pytest.raises(FileNotFoundError, match="No HDF5 file found"):
            backend.fetch_data(obsid=232, tel_id=1, site="North", date="1999-01-01")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
