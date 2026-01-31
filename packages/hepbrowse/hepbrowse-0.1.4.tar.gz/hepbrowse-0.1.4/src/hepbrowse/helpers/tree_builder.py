# src/hepbrowse/helpers/tree_builder.py
from textual.widgets import Tree
from hepbrowse.helpers import loader_factory

class TreeBuilder:
    """Helper class that takes loader output and populates a Textual Tree."""

    @staticmethod
    def populate_from_structure(tree: Tree, structure: dict):
        """Recursively populate a Textual Tree from a nested structure dict."""
        def add_nodes(parent, substruct):
            for key, value in substruct.items():
                if isinstance(value, dict):
                    child = parent.add(key)
                    add_nodes(child, value)
                elif isinstance(value, (list, tuple)):
                    list_node = parent.add(key)
                    for i, item in enumerate(value):
                        list_node.add_leaf(f"[{i}]  {item}")
                else:
                    parent.add_leaf(f"{key}  {value}")
        add_nodes(tree.root, structure)
        tree.root.expand()

    @staticmethod
    def populate_from_file(tree: Tree, file_path: str):
        """Open a data file, build its structure, and fill the tree."""
        loader = loader_factory.get_loader(file_path)
        structure = loader.get_structure()
        TreeBuilder.populate_from_structure(tree, structure)
