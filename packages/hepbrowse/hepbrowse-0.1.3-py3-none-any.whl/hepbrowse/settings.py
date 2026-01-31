from textual.app import ComposeResult
from textual.widgets import Button, Static, Select
from textual.containers import Vertical

class SettingsTab(Vertical):
    """Widget representing the Settings tab."""

    THEMES_MAP = {
        "Textual Dark": "textual-dark",
        "Textual Light": "textual-light",
        "Nord": "nord",
        "Gruvbox": "gruvbox",
        "Catppuccin Mocha": "catppuccin-mocha",
        "Dracula": "dracula",
        "Tokyo Night": "tokyo-night",
        "Monokai": "monokai",
        "Flexoki": "flexoki",
        "Catppuccin Latte": "catppuccin-latte",
        "Solarized Light": "solarized-light",
    }

    def compose(self) -> ComposeResult:
        yield Static("HEPBrowse Settings", id="settings-title")
        yield Select.from_values(list(self.THEMES_MAP.keys()), prompt="Select Theme", id="theme-select", value="Dracula", allow_blank=False)
        with Vertical(id="save-container"):
            yield Button("Save", id="save-settings", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-settings":
            self.notify("Saved settings")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Switch theme using the map."""
        if event.select.id == "theme-select":
            display_name = event.value
            theme_id = self.THEMES_MAP.get(display_name)
            if theme_id:
                self.app.theme = theme_id
                self.notify(f"Switched to {display_name} theme", severity="information")
                self.app.logger.write(f"Set theme to {display_name}")
