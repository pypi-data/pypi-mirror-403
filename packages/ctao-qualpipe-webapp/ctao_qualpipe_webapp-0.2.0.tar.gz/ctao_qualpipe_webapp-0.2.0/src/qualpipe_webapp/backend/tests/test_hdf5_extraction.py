import h5py
import numpy as np

from qualpipe_webapp.backend.backends.file_backend import FileBackend


def _ensure_group(h5file: h5py.File, path: str) -> h5py.Group:
    group = h5file
    for part in path.strip("/").split("/"):
        group = group.require_group(part)
    return group


def test_extract_dataset_value_from_compound_dataset(temp_data_dir):
    # Create a minimal backend; it only needs an existing data dir.
    backend = FileBackend(data_dir=str(temp_data_dir))

    h5_path = temp_data_dir / "test.h5"
    dataset_path = "dl1/monitoring/telescope/quality/pedestal_charge_mean/tel_001"

    dtype = np.dtype([("mean", "f4"), ("std", "f4")])
    data = np.zeros((3,), dtype=dtype)
    data["mean"] = np.array([1.0, 2.0, 3.0], dtype="f4")

    with h5py.File(h5_path, "w") as h5file:
        parent = _ensure_group(
            h5file, "dl1/monitoring/telescope/quality/pedestal_charge_mean"
        )
        parent.create_dataset("tel_001", data=data)

    with h5py.File(h5_path, "r") as h5file:
        extracted = backend._extract_dataset_value(h5file, dataset_path, "mean")

    assert extracted is not None
    assert extracted.tolist() == [1.0, 2.0, 3.0]


def test_extract_dataset_value_from_group_member_dataset(temp_data_dir):
    backend = FileBackend(data_dir=str(temp_data_dir))

    h5_path = temp_data_dir / "test_group.h5"
    dataset_path = "dl1/monitoring/telescope/quality/pedestal_charge_mean/tel_001"

    with h5py.File(h5_path, "w") as h5file:
        tel_group = _ensure_group(h5file, dataset_path)
        tel_group.create_dataset("mean", data=np.array([1.0, 2.0, 3.0], dtype="f4"))

    with h5py.File(h5_path, "r") as h5file:
        extracted = backend._extract_dataset_value(h5file, dataset_path, "mean")

    assert extracted is not None
    assert extracted.tolist() == [1.0, 2.0, 3.0]
