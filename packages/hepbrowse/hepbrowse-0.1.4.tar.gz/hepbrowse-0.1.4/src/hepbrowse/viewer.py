from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, TabbedContent, TabPane, Markdown, RichLog
from hepbrowse.data.data_manager import DataManager
from hepbrowse.settings import SettingsTab
from hepbrowse.helpers.tree_builder import TreeBuilder
from hepbrowse.widgets.plot_tab import PlotTab
from hepbrowse.helpers import loader_factory
from hepbrowse.plugins.loader import register_plugins_with_app

import click

WELCOME_FILE = Path(__file__).parent / "docs" / "welcome.md"

class HEPBrowseApp(App):
    """HEPBrowse main Textual application."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)   

        self.tab_definitions = []   

        self.plugins = []   

        self.services = {}  

        self.plugins = register_plugins_with_app(self)  

    CSS_PATH = [
        Path(__file__).parent / "css" / "hepbrowse.tcss",
        Path(__file__).parent / "css" / "plot_tab.tcss",
        Path(__file__).parent / "css" / "settings_screen.tcss",
        ]
    TITLE = "HEPBrowse"

    BINDINGS = [
        ("ctrl+right", "cycle_tab(1)", "Next Tab"),
        ("ctrl+left", "cycle_tab(-1)", "Previous Tab"),
        ("ctrl+s", "toggle_sidebar", "Toggle Sidebar")
        ]
    
    def set_file(self, path: Path):
        self.file = path
        self.loader = loader_factory.get_loader(path)
        DataManager(self.loader)

    def add_tab(self, label: str, tab_id: str, factory):
        existing = [tid for (_, tid, _) in self.tab_definitions]
        if tab_id in existing:
            return
        self.tab_definitions.append((label, tab_id, factory))

    def _make_welcome_tab(self):
        if WELCOME_FILE.exists():
            return Markdown(WELCOME_FILE.read_text(encoding="utf-8"), id="welcome-text")
        else:
            return Markdown("# Welcome\n\nFile not found.", id="welcome-text")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield from self.make_sidebar()
        with TabbedContent(initial="welcome"):
            with TabPane("Welcome", id="welcome"):
                if WELCOME_FILE.exists():
                    with WELCOME_FILE.open("r", encoding="utf-8") as f:
                        md_content = f.read()
                else:
                    md_content = "# Welcome\n\nFile not found."
                yield Markdown(md_content, id="welcome-text")
            with TabPane("Plot", id="plotting"):
                yield PlotTab(loader=self.loader, theme=self.theme)
            with TabPane("Settings", id="settings"):
                yield SettingsTab()
            with TabPane("Log", id="log"):
                self.logger = RichLog(highlight=True, markup=True)
                yield self.logger
        yield Footer()
        
    def make_sidebar(self):
        """Generator version of sidebar creation."""
        self.sidebar = Tree(self.file.name, id="sidebar")

        TreeBuilder.populate_from_file(
            self.sidebar,
            str(self.file.resolve())
        )

        yield self.sidebar

    def action_toggle_sidebar(self):
        self.sidebar.toggle_class("--visible")

    def action_cycle_tab(self, direction: int):
        """Move to the next/previous tab with wrapping."""
        tabbed_content = self.query_one(TabbedContent)
        tabs = [tab.id for tab in self.query("TabPane")]
        current_index = tabs.index(tabbed_content.active)
        new_index = (current_index + direction) % len(tabs)
        tabbed_content.active = tabs[new_index]
    
    def on_mount(self) -> None:
        self.logger.write("App starting...")
        self.logger.write("Loading theme...")
        self.theme = "dracula"
        self.logger.write("Loaded file: " + str(self.file.resolve()))
        self.logger.write("App started successfully")

@click.command()
@click.argument('filename', nargs=1)
def HEPBrowse(filename: str):
    """
        Open FILENAME in HEPBrowse 
    """
    app = HEPBrowseApp()
    app.set_file(Path(filename))
    app.run()

if __name__ == "__main__":
    HEPBrowse()