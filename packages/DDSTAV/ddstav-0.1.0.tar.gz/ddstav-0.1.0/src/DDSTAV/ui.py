import tkinter as tk
import seaborn as sns
import numpy as np
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.colors import to_hex

PASTEL_PALETTE = (sns.color_palette("pastel"))


class MongoApp(tk.Tk):
    """
    Main application class for the Mongo Structure Viewer.
    Encapsulates all UI, state, and logic.
    """
    COLLECTION_COLORS = {}
    PASTEL_HEX_PALETTE = [to_hex(c) for c in PASTEL_PALETTE]

    def __init__(self, structures):
        """Initializes the main application window and components."""
        super().__init__()
        self.structures = structures
        self.title("Mongo Structure Viewer")
        self.geometry("1000x800")
        self.tile_cards = []
        self.current_collection = None
        self.graph_figure = None
        self._init_style()
        self._create_widgets()
        if self.structures:
            self.collection_combo.current(0)
            self.show_selected_collection()
            # self.after(1000, self.export_tiles_to_image)

    def _init_style(self):
        """Initializes Tkinter styles for themed widgets."""
        style = ttk.Style(self)
        style.configure("Header.TFrame", background="#F0F0F0")
        style.configure("InnerFrame.TFrame", background="#F0F0F0")

    def _create_widgets(self):
        """Creates and packs all main UI components."""
        self._create_header()
        self._create_graph_area()
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self._create_scrollable_area(main_frame)

    def _create_header(self):
        """Creates the collection selection combobox header."""
        self.header_frame = ttk.Frame(self, style="Header.TFrame")
        self. header_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        inner_pad = tk.Frame(self.header_frame)
        inner_pad.pack(fill=tk.X, padx=10, pady=10)
        self.collection_combo = ttk.Combobox(inner_pad, state="readonly", font=("Arial", 12))
        self.collection_combo["values"] = list(self.structures.keys())
        self.collection_combo.pack(fill=tk.X, expand=True)
        self.collection_combo.bind("<<ComboboxSelected>>", self.show_selected_collection)

    def _create_scrollable_area(self, parent):
        """Creates the scrollable canvas and inner frame for tiles."""
        self.canvas = tk.Canvas(parent, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.tiles_inner = ttk.Frame(self.canvas, style="InnerFrame.TFrame")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.tiles_inner, anchor="n")
        self.tiles_inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_scroll_recursively(self.canvas)

    def _on_mouse_wheel(self, event):
        """Handles mouse wheel scrolling for the canvas."""
        if event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        elif event.delta:  # Windows/macOS
            self.canvas.yview_scroll(int(-1 * (event.delta / 120) * 3), "units")

    def _bind_scroll_recursively(self, widget):
        """Recursive scroll binding."""
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        widget.bind("<Button-4>", self._on_mouse_wheel)
        widget.bind("<Button-5>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self._bind_scroll_recursively(child)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.reflow_tiles()

    def _create_graph_area(self):
        """Creates the Matplotlib graph placeholder area and a visual separator."""
        self.bottom_container = tk.Frame(self, bg="#ffffff")
        self.bottom_container.pack(side=tk.BOTTOM, fill=tk.X)
        separator_line = tk.Frame(self.bottom_container, bg="#B0B0B0", height=2)
        separator_line.pack(side=tk.TOP, fill=tk.X)
        shadow_line = tk.Frame(self.bottom_container, bg="#F0F0F0", height=2)
        shadow_line.pack(side=tk.TOP, fill=tk.X)
        self.graph_figure = Figure(figsize=(10, 3), dpi=100)
        self.graph_figure.patch.set_facecolor('#FAFAFA')
        self.graph_canvas = FigureCanvasTkAgg(self.graph_figure, master=self.bottom_container)
        self.graph_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.X)

    def _draw_bar_chart(self, labels, counts, color, collection_name):
        self.graph_figure.clf()
        ax = self.graph_figure.add_subplot(111)
        ax.set_facecolor('#FAFAFA')
        if not labels:
            ax.set_title(f"Schema Count for '{collection_name}' (No data)", fontsize=10)
            ax.text(0.5, 0.5, "No document structures found.",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, color='black')
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            x_pos = np.arange(len(labels))
            bars = ax.bar(x_pos, counts, align='center', color=color, alpha=0.8, edgecolor="#888888", linewidth=0.5)
            ax.set_ylabel('Frequency', fontsize=9)
            ax.margins(y=0.15)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=8)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{height}',
                        ha='center', va='bottom', fontsize=8)

        self.graph_figure.tight_layout(pad=1.5)
        self.graph_canvas.draw()

    def reflow_tiles(self, event=None):
        """Dynamically arranges structure tiles in a centered grid."""
        if not self.tile_cards:
            return

        width = self.canvas.winfo_width()
        if width < 50:
            return

        CARD_WIDTH = 320
        num_cols = max(1, width // CARD_WIDTH)
        if num_cols > 5:
            num_cols = 5

        for w in self.tiles_inner.grid_slaves():
            w.grid_forget()

        self.tiles_inner.grid_columnconfigure(0, weight=1)
        for c in range(1, num_cols + 1):
            self.tiles_inner.grid_columnconfigure(c, weight=0, minsize=CARD_WIDTH)

        self.tiles_inner.grid_columnconfigure(num_cols + 1, weight=1)
        for i, widget in enumerate(self.tile_cards):
            row = (i // num_cols)
            col = (i % num_cols) + 1
            widget.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

        for r in range((len(self.tile_cards) // num_cols) + 1):
            self.tiles_inner.grid_rowconfigure(r, weight=0)

        self.tiles_inner.update_idletasks()
        self._on_frame_configure(None)

    def _get_collection_color(self, collection_name):
        if collection_name not in self.COLLECTION_COLORS:
            color_index = len(self.COLLECTION_COLORS) % len(self.PASTEL_HEX_PALETTE)
            self.COLLECTION_COLORS[collection_name] = self.PASTEL_HEX_PALETTE[color_index]
        return self.COLLECTION_COLORS[collection_name]

    def _create_collection_tile(self, struct, parent, bg_color):
        bg_holder = tk.Frame(parent, bg=bg_color)
        tile = tk.Frame(bg_holder, bg="#ffffff", bd=1, relief="solid", highlightthickness=0)
        tile.configure(highlightbackground="#C0C0C0", highlightthickness=1)
        tile.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)  # Malý padding pre efekt okraja
        label_name = next((k for k in struct.keys() if k != "count"), "Document")
        title_text = f"{label_name} (Count: {struct['count']})"
        title_lbl = tk.Label(tile,
                             text=title_text,
                             bg="#ffffff", fg="#333333",
                             font=("Segoe UI", 11, "bold"))
        title_lbl.pack(anchor="w", pady=(10, 5), padx=10)
        ttk.Separator(tile, orient='horizontal').pack(fill='x', padx=10, pady=2)
        fields = struct[label_name]
        body_lines = []
        for field, types in fields.items():
            body_lines.append(f"{field}: {types}")

        body_text = "\n".join(body_lines)
        body_lbl = tk.Label(tile,
                            text=body_text,
                            font=("Consolas", 9),
                            justify=tk.LEFT,
                            anchor="nw",
                            bg="#ffffff", fg="#000000",
                            padx=10, pady=5)
        body_lbl.pack(fill=tk.BOTH, expand=True)
        self._bind_scroll_recursively(bg_holder)

        return bg_holder

    def show_selected_collection(self, event=None):
        selected = self.collection_combo.get()
        if not selected or selected == self.current_collection and not event:
            if self.current_collection is not None:
                return

        self.current_collection = selected

        for w in self.tiles_inner.winfo_children():
            w.destroy()
        self.tile_cards.clear()
        current_color = self._get_collection_color(selected)
        self.configure(bg=current_color)
        style = ttk.Style(self)
        style.configure("InnerFrame.TFrame", background=current_color)
        self.canvas["bg"] = current_color
        collection_data = self.structures[selected]
        chart_labels = []
        chart_counts = []
        for struct in collection_data:
            tile = self._create_collection_tile(struct, self.tiles_inner, current_color)
            self.tile_cards.append(tile)
            label_name = next((k for k in struct.keys() if k != "count"), "Document")
            chart_labels.append(label_name)
            chart_counts.append(struct['count'])

        self._draw_bar_chart(chart_labels, chart_counts, current_color, selected)
        self.update_idletasks()
        self.reflow_tiles()