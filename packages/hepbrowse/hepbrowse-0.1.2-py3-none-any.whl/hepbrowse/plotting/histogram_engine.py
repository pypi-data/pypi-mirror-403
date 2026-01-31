import numpy as np
import plotext as plt
from hepbrowse.data.data_manager import DataManager


class HistogramEngine:
    """Lightweight, NumPy-based histogram engine using lazy data access."""

    @staticmethod
    def make_histogram(dataset_path: str, bins: int = 50, range: tuple[float, float] | None = None, norm: bool = False):
        """
        Create a histogram for the given dataset path.

        This method reopens the file lazily from disk (to ensure thread safety),
        fetches the dataset, computes the histogram with NumPy, and returns both
        bin centers and counts (ready for plotting).

        Parameters
        ----------
        dataset_path : str
            Path to the dataset (as returned by DataManager.list_datasets()).
        bins : int, optional
            Number of histogram bins.
        range : tuple[float, float], optional
            Value range for the histogram; if None, use data min/max.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Bin centers and counts arrays.
        """
        # Reopen the file from disk in this thread to avoid threading issues
        dm = DataManager.get()
        loader_cls = type(dm.loader)
        loader_path = dm.loader.path

        # Recreate loader fresh for this thread
        loader = loader_cls(loader_path)

        # Load dataset lazily from the file
        data = loader.load_dataset(dataset_path)

        # Ensure numeric data
        if not np.issubdtype(data.dtype, np.number):
            raise TypeError(f"Dataset '{dataset_path}' is not numeric ({data.dtype}) and cannot be histogrammed.")
        
        # Ensure safe data
        data = data[~np.isnan(data)]
        data = data[np.isfinite(data)]

        # Compute histogram with NumPy
        counts, edges = np.histogram(data, bins=bins, range=range)
        centers = (edges[:-1] + edges[1:]) / 2

        return counts/sum(counts) if norm else counts, centers #centers, counts



