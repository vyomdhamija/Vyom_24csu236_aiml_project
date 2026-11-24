"""
components.py — Reusable, styled widgets built on top of CustomTkinter.
"""

import customtkinter as ctk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

from theme import COLORS, FONTS, RADIUS


class Card(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=RADIUS, border_width=1, border_color=COLORS["border"], **kwargs)


class SectionLabel(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=text.upper(), font=FONTS["small"], text_color=COLORS["text_muted"], anchor="w", **kwargs)


class LabeledDropdown(ctk.CTkFrame):
    def __init__(self, master, label, values, default=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label = ctk.CTkLabel(self, text=label, font=FONTS["body"], text_color=COLORS["text_secondary"], anchor="w")
        self.label.pack(fill="x", pady=(0, 4))
        self.var = ctk.StringVar(value=default if default else (values[0] if values else ""))
        self.menu = ctk.CTkOptionMenu(
            self, values=values, variable=self.var, fg_color=COLORS["bg_input"], button_color=COLORS["bg_input"],
            button_hover_color=COLORS["bg_card_hover"], dropdown_fg_color=COLORS["bg_card_hover"], font=FONTS["body"], corner_radius=8, height=40,
        )
        self.menu.pack(fill="x")

    def get(self):
        return self.var.get()


class LabeledEntry(ctk.CTkFrame):
    def __init__(self, master, label, default="", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label = ctk.CTkLabel(self, text=label, font=FONTS["body"], text_color=COLORS["text_secondary"], anchor="w")
        self.label.pack(fill="x", pady=(0, 4))
        self.entry = ctk.CTkEntry(self, fg_color=COLORS["bg_input"], border_color=COLORS["border"], font=FONTS["body"], corner_radius=8, height=40)
        self.entry.insert(0, str(default))
        self.entry.pack(fill="x")

    def get(self):
        return self.entry.get()


class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(
            master, text=text, command=command, fg_color=COLORS["chart_bar_alt"], hover_color="#16a34a",
            text_color="#ffffff", font=FONTS["h2"], corner_radius=10, height=48, **kwargs,
        )


class SecondaryButton(ctk.CTkButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(
            master, text=text, command=command, fg_color="transparent", hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"], border_width=1, border_color=COLORS["border"], font=FONTS["body_bold"], corner_radius=10, height=40, **kwargs,
        )


class StatChip(Card):
    def __init__(self, master, title, value, value_color=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title.upper(), font=FONTS["small"], text_color=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(self, text=value, font=FONTS["h1"], text_color=value_color or COLORS["text_primary"]).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))


class AnimatedToxicityLabel(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(master, text="0.0%", font=FONTS["price"], text_color=COLORS["success"], **kwargs)
        self._job = None

    def animate_to(self, target_value, duration_ms=700, steps=24):
        if self._job is not None:
            self.after_cancel(self._job)

        target_value = max(0.0, min(100.0, target_value))
        step_delay = max(1, duration_ms // steps)

        def _tick(i):
            progress = i / steps
            eased = 1 - (1 - progress) ** 3
            current = target_value * eased
            
            # Dynamic toxicity coloration: Green -> Yellow -> Toxic Magenta
            color = COLORS["success"] if current < 40 else (COLORS["warning"] if current < 60 else COLORS["accent"])
                
            self.configure(text=f"{current:.1f}%", text_color=color)
            if i < steps:
                self._job = self.after(step_delay, lambda: _tick(i + 1))
            else:
                self.configure(text=f"{target_value:.1f}%")

        _tick(0)


class ChartCard(Card):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        ctk.CTkLabel(self, text=title, font=FONTS["h2"], text_color=COLORS["text_primary"], anchor="w").pack(fill="x", padx=20, pady=(18, 4))

        self.figure = plt.Figure(figsize=(4.6, 2.8), dpi=100)
        self.figure.patch.set_facecolor(COLORS["bg_card"])
        self.ax = self.figure.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().configure(bg=COLORS["bg_card"], highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0, 18))

    def _style_axes(self):
        self.ax.set_facecolor(COLORS["bg_card"])
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        self.ax.spines["bottom"].set_color(COLORS["border"])
        self.ax.spines["bottom"].set_linewidth(1.5)
        self.ax.tick_params(colors=COLORS["text_secondary"], labelsize=9, length=0)
        self.ax.set_axisbelow(True)

    def draw_horizontal_bars(self, labels, values):
        self.ax.clear()
        self._style_axes()
        self.ax.grid(color=COLORS["chart_grid"], linewidth=1, axis="x", linestyle="--")
        
        bars = self.ax.barh(labels, values, color=COLORS["chart_bar"], height=0.35)
        self.ax.invert_yaxis()
        max_val = max(values) if values else 1
        self.ax.set_xlim(0, max_val * 1.25)
        
        for bar in bars:
            width = bar.get_width()
            self.ax.text(
                width + max_val * 0.03, bar.get_y() + bar.get_height() / 2, f"{width:.0%}" if width < 1 else f"{width:,.0f}",
                va="center", fontsize=9, color=COLORS["text_primary"], weight="bold"
            )
            
        self.figure.subplots_adjust(left=0.28, right=0.95, top=0.95, bottom=0.12)
        self.canvas.draw()

    def draw_comparison_bars(self, labels, values, highlight_index=None, format_as_pct=False):
        self.ax.clear()
        self._style_axes()
        self.ax.grid(color=COLORS["chart_grid"], linewidth=1, axis="y", linestyle="--")
        self.ax.grid(False, axis="x")
        
        colors = [COLORS["chart_bar_alt"]] * len(values)
        if highlight_index is not None and 0 <= highlight_index < len(colors):
            colors[highlight_index] = COLORS["warning"]
            
        self.ax.bar(labels, values, color=colors, width=0.45)
        self.ax.set_xticks(range(len(labels)))
        self.ax.set_xticklabels(labels, rotation=30, ha="right")
        
        def fmt(x, pos):
            return f"{int(x)}%" if format_as_pct else f"{int(x)}"
        self.ax.yaxis.set_major_formatter(FuncFormatter(fmt))

        self.figure.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.25)
        self.canvas.draw()


class LineChartCard(Card):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        ctk.CTkLabel(self, text=title, font=FONTS["h2"], text_color=COLORS["text_primary"], anchor="w").pack(fill="x", padx=20, pady=(18, 0))

        self.figure = plt.Figure(figsize=(4.6, 2.8), dpi=100)
        self.figure.patch.set_facecolor(COLORS["bg_card"])
        self.ax = self.figure.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().configure(bg=COLORS["bg_card"], highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0, 18))

    def _style_axes(self):
        self.ax.set_facecolor(COLORS["bg_card"])
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        self.ax.spines["bottom"].set_color(COLORS["border"])
        self.ax.spines["bottom"].set_linewidth(1.5)
        self.ax.tick_params(colors=COLORS["text_secondary"], labelsize=9, length=0, pad=6)
        self.ax.set_axisbelow(True)

    def draw_line_chart(self, x_labels, y_values, highlight_index=None, format_as_pct=False):
        self.ax.clear()
        self._style_axes()
        self.ax.grid(color=COLORS["chart_grid"], linewidth=1, axis="y", linestyle="--")
        self.ax.grid(False, axis="x")
        
        self.ax.plot(x_labels, y_values, color=COLORS["chart_bar"], marker="o", linewidth=2.5, markersize=6)
        
        if highlight_index is not None and 0 <= highlight_index < len(x_labels):
            self.ax.plot(x_labels[highlight_index], y_values[highlight_index], marker="o", color=COLORS["warning"], markersize=10, zorder=5)
            
        def fmt(x, pos):
            return f"{int(x)}%" if format_as_pct else f"{int(x)}"
        self.ax.yaxis.set_major_formatter(FuncFormatter(fmt))
        
        self.figure.subplots_adjust(left=0.15, right=0.95, top=0.90, bottom=0.2)
        self.canvas.draw()