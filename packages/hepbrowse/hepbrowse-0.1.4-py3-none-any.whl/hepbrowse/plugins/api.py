from abc import ABC, abstractmethod
from typing import Any


class HEPBrowsePlugin(ABC):
    """
    Base class for all plugins (builtin and external).
    Plugins should subclass this and implement `register`.
    """

    name: str = "Unnamed"
    version: str = "0.0.0"

    def __init__(self) -> None:
        # Optional place for plugin init state
        self.app = None

    def register(self, app: Any) -> None:
        """
        Called once at startup with the App instance.
        Plugins should use `app` to register tabs, settings providers,
        loaders, services, etc.
        """
        self.app = app

    # convenience extension points (optional to implement)
    def register_tabs(self, app: Any) -> None:
        """Register TabPanes via app.add_tab(label, id, factory)."""
        return

    def register_settings(self, settings_manager: Any) -> None:
        """Register settings providers if any."""
        return
