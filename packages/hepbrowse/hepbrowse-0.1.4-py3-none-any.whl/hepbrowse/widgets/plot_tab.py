from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Input, Select, Button, Static, Markdown, RadioButton
from textual_plotext import PlotextPlot
from textual.worker import Worker
from hepbrowse.plotting.histogram_engine import HistogramEngine

MD_INSTRUCTIONS = """
# Plotting Instructions
Panels on the left can be used to control the plot produced:
- Dataset selection (type to search)
- Number of bins
- Plot limits
- Normalization

Leaving blank fields will result in HEPBrowse automatically defining defaults.

Pressing the **Genenerate Plot** button will load and process the necessary data

Pressing the **Reset Plot** button will erase the displayed plot and show this instructions page again.
"""

class PlotTab(Static):
    """PlotTab Widget"""

    def __init__(self, loader, theme, **kwargs):
        super().__init__(**kwargs)
        self.loader = loader
        self.datasets = self.loader.get_flat_dataset_paths()
        self.theme = theme
        self.display_info = True
        self.plot_area: PlotextPlot | None = None
        self.current_worker: Worker | None = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="plot-controls"):

                yield Label("Dataset / Variable")
                yield Select.from_values(
                    self.datasets,
                    prompt="Select Dataset",
                    id="dataset-select",
                    allow_blank=True
                )

                yield Label("Bins")
                self.bins_input = Input(placeholder="50", id="bins-input", type="integer")
                yield self.bins_input

                yield Label("X Min")
                self.xmin_input = Input(placeholder="auto", id="xmin-input", type="number")
                yield self.xmin_input

                yield Label("X Max")
                self.xmax_input = Input(placeholder="auto", id="xmax-input", type="number")
                yield self.xmax_input

                with Horizontal(id="plot-checkboxes"):
                    yield RadioButton("Normalize", id="plot-normalize")

                yield Button("Generate Plot", id="plot-button", variant="success")
                yield Button("Reset Plot", id="reset-button", variant="error")

            with Vertical(id="plot-display"):
                yield Markdown(MD_INSTRUCTIONS, id="plot-md-info")

    async def set_loading(self, loading: bool = True) -> None:
        self.plot_area.loading = loading

    async def set_plot(self, edges, counts, dataset_path) -> None:
        if hasattr(self.plot_area, 'plt'):
            plt = self.plot_area.plt
            plt.bar(edges[:], counts, width=(edges[1] - edges[0]))
            plt.title(f"Histogram for {dataset_path}")
            plt.xlabel("Value")
            plt.ylabel("Count")
            self.plot_area.loading = False

    async def _generate_plot(self):
        if self.plot_area:
            selector = self.query_one("#dataset-select")
            norm_check = self.query_one("#plot-normalize")
            dataset_path = selector.value
            norm = norm_check.value

            try:
                bins = int(self.bins_input.value or 50)
            except ValueError:
                bins = 50

            limits_set = self.xmin_input.value and self.xmax_input.value

            try:
                if limits_set:
                    xmin = float(self.xmin_input.value)
                    xmax = float(self.xmax_input.value)
                    counts, bin_edges = HistogramEngine.make_histogram(dataset_path, bins=bins, range=(xmin, xmax), norm=norm)
                else:
                    counts, bin_edges = HistogramEngine.make_histogram(dataset_path, bins=bins, norm=norm)
            except Exception as e:
                self.app.call_from_thread(
                    self.app.logger.write,
                    f"Histogram generation failed: {e}"
                )
                self.app.call_from_thread(
                    self.notify,
                    f"Error generating histogram: {e}", severity="error"
                )
                self.app.call_from_thread(
                    self.set_loading,
                    False,
                )
                return

            self.app.call_from_thread(
                self.set_plot,
                bin_edges,
                counts,
                dataset_path
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "plot-button":

            selector = self.query_one("#dataset-select")

            if selector.value == Select.BLANK:
                self.notify("No variable was selected for plotting", severity="warning")
                return

            display = self.query_one("#plot-display")

            for child in list(display.children):
                child.remove()

            self.plot_area = PlotextPlot()
            self.plot_area.loading = True
            display.mount(self.plot_area)

            self.current_worker = self.run_worker(self._generate_plot(), group="plotting", exclusive=True, thread=True)
        elif event.button.id == "reset-button":
            display = self.query_one("#plot-display")

            for child in list(display.children):
                child.remove()
            self.plot_area = Markdown(MD_INSTRUCTIONS)
            self.plot_area.loading = False
            display.mount(self.plot_area)