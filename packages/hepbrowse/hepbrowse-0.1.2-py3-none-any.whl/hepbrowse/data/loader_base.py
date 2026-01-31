from abc import ABC, abstractmethod
from pathlib import Path
import numpy as np

class DataLoader(ABC):
    """Abstract base class for all data loaders (HDF5, ROOT, etc.)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")

    @abstractmethod
    def get_structure(self) -> dict:
        """Return the hierarchical structure of the file.
        Should return nested dicts: {group: {dataset: shape, ...}, ...}
        """

    @abstractmethod
    def get_dataset_shape(self, dataset_path: str) -> tuple[int, ...]:
        """Return the shape of a given dataset without loading its contents."""

    @abstractmethod
    def load_dataset(self, dataset_path: str) -> np.ndarray:
        """Lazily load a dataset as a NumPy array."""

    @abstractmethod
    def get_flat_dataset_paths(self) -> list[str]:
        """Return a flat list of dataset paths suitable for UI dropdowns."""
        pass
