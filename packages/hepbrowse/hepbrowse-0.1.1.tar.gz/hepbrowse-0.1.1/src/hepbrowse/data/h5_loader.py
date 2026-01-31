# src/hepbrowse/data/h5_loader.py
from pathlib import Path
import h5py
import numpy as np

from hepbrowse.data.loader_base import DataLoader


class H5Loader(DataLoader):
    """Thread-safe HDF5 loader."""

    def get_structure(self) -> dict:
        def explore(obj):
            struct = {}
            for name, item in obj.items():
                if isinstance(item, h5py.Group):
                    struct[name] = explore(item)
                elif isinstance(item, h5py.Dataset):
                    if item.dtype.names:
                        struct[name] = {
                            field: item.dtype[field].str
                            for field in item.dtype.names
                        }
                    else:
                        struct[name] = tuple(item.shape)
            return struct

        with h5py.File(self.path, "r") as f:
            return explore(f)

    def get_dataset_shape(self, dataset_path: str) -> tuple[int, ...]:
        with h5py.File(self.path, "r") as f:
            obj = self._resolve_path(f, dataset_path)
            return obj.shape

    def load_dataset(self, dataset_path: str) -> np.ndarray:
        with h5py.File(self.path, "r") as f:
            obj = self._resolve_path(f, dataset_path)
            return np.asarray(obj)

    def get_flat_dataset_paths(self) -> list[str]:
        paths = []

        def walk(obj, prefix=""):
            for name, item in obj.items():
                path = f"{prefix}/{name}" if prefix else f"/{name}"
                if isinstance(item, h5py.Group):
                    walk(item, path)
                elif isinstance(item, h5py.Dataset):
                    if item.dtype.names:
                        for field in item.dtype.names:
                            paths.append(f"{path}/{field}")
                    else:
                        paths.append(path)

        with h5py.File(self.path, "r") as f:
            walk(f)

        return paths

    @staticmethod
    def _resolve_path(file, dataset_path: str):
        obj = file
        for part in dataset_path.strip("/").split("/"):
            obj = obj[part]
        return obj
