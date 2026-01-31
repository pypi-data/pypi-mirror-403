import importlib
import pkgutil
import sys
import traceback
from typing import List, Type

from hepbrowse.plugins.api import HEPBrowsePlugin


def _iter_plugin_modules(package_name: str):
    """
    Yield imported Python modules under a given package.
    Supports both module-based and package-based plugins.
    """
    try:
        package = importlib.import_module(package_name)
    except Exception:
        return

    package_path = getattr(package, "__path__", None)
    if not package_path:
        return

    for modinfo in pkgutil.iter_modules(package_path, package_name + "."):
        try:
            module = importlib.import_module(modinfo.name)
            yield module
        except Exception:
            print(
                f"[hepbrowse] Failed importing plugin module {modinfo.name}",
                file=sys.stderr,
            )
            traceback.print_exc()


def _find_plugin_classes(module) -> List[Type[HEPBrowsePlugin]]:
    """
    Return all concrete subclasses of HEPBrowsePlugin in a module.
    """
    plugins: List[Type[HEPBrowsePlugin]] = []

    for obj in module.__dict__.values():
        try:
            if (
                isinstance(obj, type)
                and issubclass(obj, HEPBrowsePlugin)
                and obj is not HEPBrowsePlugin
            ):
                plugins.append(obj)
        except Exception:
            continue

    return plugins


def discover_builtin_plugins(
    package: str = "hepbrowse.plugins",
) -> List[HEPBrowsePlugin]:
    """
    Discover and instantiate builtin plugins.
    """
    instances: List[HEPBrowsePlugin] = []

    for module in _iter_plugin_modules(package):
        for plugin_cls in _find_plugin_classes(module):
            try:
                instances.append(plugin_cls())
            except Exception:
                print(
                    f"[hepbrowse] Failed instantiating plugin {plugin_cls.__name__}",
                    file=sys.stderr,
                )
                traceback.print_exc()

    return instances


def register_plugins_with_app(app, package: str = "hepbrowse.plugins"):
    """
    Discover plugins and register them with the app.
    """
    plugins = discover_builtin_plugins(package)

    for plugin in plugins:
        try:
            plugin.register(app)

            if hasattr(plugin, "register_tabs"):
                plugin.register_tabs(app)

            if hasattr(plugin, "register_settings") and hasattr(app, "settings_manager"):
                plugin.register_settings(app.settings_manager)

        except Exception:
            print(
                f"[hepbrowse] Error registering plugin {plugin}",
                file=sys.stderr,
            )
            traceback.print_exc()

    return plugins
