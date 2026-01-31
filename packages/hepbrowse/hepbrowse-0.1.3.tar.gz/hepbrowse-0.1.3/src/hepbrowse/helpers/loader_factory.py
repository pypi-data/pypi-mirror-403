# hepbrowse/data/registry.py
from pathlib import Path
from typing import Type
from hepbrowse.data.loader_base import DataLoader
from hepbrowse.data.h5_loader import H5Loader
from hepbrowse.data.root_loader import RootLoader

_LOADER_REGISTRY: dict[str, Type[DataLoader]] = {
    ".h5": H5Loader,
    ".hdf5": H5Loader,
    ".root": RootLoader
}

@staticmethod
def get_loader(path: str | Path) -> DataLoader:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix not in _LOADER_REGISTRY:
        raise ValueError(f"No loader registered for file type: {suffix}")

    return _LOADER_REGISTRY[suffix](path)
