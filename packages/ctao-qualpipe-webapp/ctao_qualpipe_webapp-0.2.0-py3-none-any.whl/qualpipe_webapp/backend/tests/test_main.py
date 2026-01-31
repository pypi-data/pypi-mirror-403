from unittest.mock import create_autospec, patch

import pytest
from fastapi.testclient import TestClient

from qualpipe_webapp.backend.backends.base import BackendAPI
from qualpipe_webapp.backend.main import app


@pytest.fixture()
def mock_backend():
    """Create a mock backend for testing."""
    # Use an autospecced mock so method signatures are enforced.
    # This prevents route handlers from calling backend methods with wrong args.
    mock_backend = create_autospec(BackendAPI, instance=True)
    mock_backend.get_ob_date_map.return_value = {"2024-01-01": [1, 2, 3]}
    mock_backend.fetch_data.return_value = {"test": "data"}
    mock_backend.scan_observations.return_value = []
    return mock_backend


@pytest.fixture()
def client_with_backend(mock_backend):
    """Create a test client with mocked backend using the real app."""
    # Override the backend creation in the lifespan
    with patch(
        "qualpipe_webapp.backend.main.create_backend", return_value=mock_backend
    ):
        with TestClient(app) as client:
            yield client


def test_health_check(client_with_backend):
    """Test the health check endpoint."""
    response = client_with_backend.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "backend"}


@pytest.mark.verifies_usecase("UC-140-2.1")
def test_get_ob_date_map_endpoint(client_with_backend):
    """Test the ob_date_map endpoint returns data from backend."""
    response = client_with_backend.get("/v1/ob_date_map")
    assert response.status_code == 200
    assert response.json() == {"2024-01-01": [1, 2, 3]}


@pytest.mark.verifies_usecase("UC-140-2.1")
def test_get_data_invalid_telescope_type(client_with_backend):
    """Test that invalid telescope type returns 400 error."""
    response = client_with_backend.get(
        "/v1/data",
        params={
            "site": "North",
            "date": "2024-01-01",
            "ob": 1,
            "telescope_type": "INVALID",
            "telescope_id": 1,
        },
    )
    assert response.status_code == 400
    assert "Invalid telescope type" in response.json()["detail"]


@pytest.mark.verifies_usecase("UC-140-2.1")
def test_get_data_file_not_found(client_with_backend):
    """Test that missing data returns 404 error."""
    # Configure mock backend to raise FileNotFoundError
    client_with_backend.app.state.backend.fetch_data.side_effect = FileNotFoundError(
        "No data found"
    )

    response = client_with_backend.get(
        "/v1/data",
        params={
            "site": "North",
            "date": "2024-01-01",
            "ob": 1,
            "telescope_type": "LST",
            "telescope_id": 999,
        },
    )
    assert response.status_code == 404
    assert "No data found" in response.json()["detail"]


@pytest.mark.verifies_usecase("UC-140-2.1")
def test_get_data_success_calls_backend_with_expected_args(client_with_backend):
    response = client_with_backend.get(
        "/v1/data",
        params={
            "site": "North",
            "date": "2024-01-01",
            "ob": 1,
            "telescope_type": "LST",
            "telescope_id": 1,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"test": "data"}
    client_with_backend.app.state.backend.fetch_data.assert_called_once_with(
        1, 1, "North", "2024-01-01", None
    )
