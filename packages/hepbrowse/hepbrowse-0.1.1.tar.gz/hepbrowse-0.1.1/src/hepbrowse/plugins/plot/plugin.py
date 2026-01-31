# src/hepbrowse/plugins/plot/plugin.py

from hepbrowse.plugins.api import HEPBrowsePlugin
from hepbrowse.widgets.plot_tab import PlotTab

class PlotPlugin(HEPBrowsePlugin):
    name = "Plot"
    version = "0.1"

    def register_tabs(self, app):
        # Use a factory so widget is instantiated during compose, not now.
        app.add_tab("Plot", "plotting", lambda: PlotTab(loader=app.loader, theme=getattr(app, "theme", None)))
