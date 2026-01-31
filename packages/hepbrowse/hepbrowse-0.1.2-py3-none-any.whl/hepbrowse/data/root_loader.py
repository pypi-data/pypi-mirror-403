from pathlib import Path
from typing import Any
import numpy as np
import uproot
import awkward as ak

from hepbrowse.data.loader_base import DataLoader


class RootLoader(DataLoader):
    """ROOT file loader using uproot (thread-safe, stateless)."""

    def get_structure(self) -> dict:
        """
        Return nested dict of ROOT content:
          - Nested TDirectory structures
          - TTree / TChain names → dict of branch name → interpretation
        """
        import uproot

        structure: dict = {}

        with uproot.open(self.path) as file:
            # uproot <=4 compatibility: no `encoded=` argument
            class_map = file.classnames(recursive=True)

            for fullpath, classname in class_map.items():
                path = fullpath.strip("/")

                if classname == "TDirectory":
                    parts = path.split("/")
                    d = structure
                    for part in parts:
                        d = d.setdefault(part, {})

                elif classname in ("TTree", "TChain"):
                    parts = path.split("/")
                    tree_name = parts[-1]

                    parent = structure
                    for part in parts[:-1]:
                        parent = parent.setdefault(part, {})

                    tree = file[path]

                    branches = {
                        name: str(branch.interpretation)
                        for name, branch in tree.items()
                    }

                    parent[tree_name] = branches

                # TODO: other ROOT object types

        return structure





    # ------------------------------
    # Dataset shape
    # ------------------------------
    def get_dataset_shape(self, dataset_path: str) -> tuple[int, ...]:
        """
        Return shape of a dataset without loading full data.
        Dataset path must be /dir/tree/branch or /tree/branch.
        """
        tree_path, branch = self._split_path(dataset_path)

        with uproot.open(self.path) as file:
            tree = file[tree_path]
            branch_obj = tree[branch]
            return (branch_obj.num_entries,)

    # ------------------------------
    # Dataset loading
    # ------------------------------
    def load_dataset(self, dataset_path: str, *, flatten: bool = True) -> np.ndarray:
        tree_path, branch = self._split_path(dataset_path)
    
        with uproot.open(self.path) as file:
            tree = file[tree_path]
            arr = tree[branch].array(library="ak")
    
            if flatten and "var *" in str(ak.type(arr)):
                return ak.to_numpy(ak.flatten(arr))
            else:
                return ak.to_numpy(arr)


    # ------------------------------
    # Flat dataset listing
    # ------------------------------
    def get_flat_dataset_paths(self) -> list[str]:
        """
        Return a flat list of dataset paths:
          /tree/branch
          /dir/tree/branch
        """
        import uproot

        paths: list[str] = []

        with uproot.open(self.path) as file:
            class_map = file.classnames(recursive=True)

            for fullpath, classname in class_map.items():
                path = fullpath.strip("/")

                if classname in ("TTree", "TChain"):
                    tree = file[path]
                    for branch_name in tree.keys():
                        paths.append(f"/{path}/{branch_name}")

        return paths


    # ------------------------------
    # Helpers
    # ------------------------------
    @staticmethod
    def _split_path(dataset_path: str) -> tuple[str, str]:
        """
        Split /dir/tree/branch → ("dir/tree", "branch")
        """
        parts = dataset_path.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid ROOT dataset path: {dataset_path}")

        tree_path = "/".join(parts[:-1])
        branch = parts[-1]
        return tree_path, branch
