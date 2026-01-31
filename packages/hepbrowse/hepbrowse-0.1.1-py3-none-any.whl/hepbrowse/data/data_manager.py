# src/hepbrowse/data/data_manager.py
from typing import Optional
from hepbrowse.data.loader_base import DataLoader
import numpy as np

class DataManager:
    _instance: Optional["DataManager"] = None  # singleton reference

    def __init__(self, loader: DataLoader):
        self.loader = loader
        self._cache: dict[str, np.ndarray] = {}
        DataManager._instance = self  # set global reference

    @classmethod
    def get(cls) -> "DataManager":
        """Return the global DataManager instance."""
        if cls._instance is None:
            raise RuntimeError("DataManager has not been initialized yet!")
        return cls._instance

    # your previous methods...
    def get_data(self, dataset_path: str) -> np.ndarray:
        if dataset_path in self._cache:
            return self._cache[dataset_path]
        data = self.loader.load_dataset(dataset_path)
        self._cache[dataset_path] = data
        return data

    def get_shape(self, dataset_path: str) -> tuple[int, ...]:
        return self.loader.get_dataset_shape(dataset_path)

    def list_datasets(self) -> list[str]:
        return self.loader.get_flat_dataset_paths()

    def clear_cache(self) -> None:
        self._cache.clear()
