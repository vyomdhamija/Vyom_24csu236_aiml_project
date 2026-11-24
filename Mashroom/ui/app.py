"""
app.py — FungiSafe Pro prediction engine.
"""

import os
import sys
import datetime

import customtkinter as ctk

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))

from theme import COLORS, FONTS, apply_base_theme
from components import (
    Card, SectionLabel, LabeledDropdown, LabeledEntry,
    PrimaryButton, SecondaryButton, 
    StatChip, AnimatedToxicityLabel, ChartCard, LineChartCard,
)
import predictor

# -------------------------------------------------------------
# Translation Dictionary: Raw Data -> Human Readable
# -------------------------------------------------------------
FEATURE_LABELS = {
    "cap-shape": {"b": "Bell", "c": "Conical", "x": "Convex", "f": "Flat", "s": "Sunken", "p": "Spherical", "o": "Others"},
    "cap-surface": {"i": "Fibrous", "g": "Grooves", "y": "Scaly", "s": "Smooth", "h": "Shiny", "l": "Leathery", "k": "Silky", "t": "Sticky", "w": "Wrinkled", "e": "Fleshy"},
    "cap-color": {"n": "Brown", "b": "Buff", "g": "Gray", "r": "Green", "p": "Pink", "u": "Purple", "e": "Red", "w": "White", "y": "Yellow", "l": "Blue", "o": "Orange", "k": "Black"},
    "does-bruise-or-bleed": {"t": "Bruises/Bleeds", "f": "No"},
    "gill-attachment": {"a": "Adnate", "x": "Adnexed", "d": "Decurrent", "e": "Free", "s": "Sinuate", "p": "Pores", "f": "None", "?": "Unknown", "unknown": "Unknown"},
    "gill-spacing": {"c": "Close", "d": "Distant", "f": "None"},
    "gill-color": {"n": "Brown", "b": "Buff", "g": "Gray", "r": "Green", "p": "Pink", "u": "Purple", "e": "Red", "w": "White", "y": "Yellow", "l": "Blue", "o": "Orange", "k": "Black", "f": "None"},
    "habitat": {"g": "Grasses", "l": "Leaves", "m": "Meadows", "p": "Paths", "u": "Urban", "w": "Waste", "d": "Woods"},
    "season": {"s": "Spring", "u": "Summer", "a": "Autumn", "w": "Winter"}
}

def format_opts(feature, codes):
    """Takes a list of codes like ['b', 'c'] and returns ['Bell (b)', 'Conical (c)']"""
    mapping = FEATURE_LABELS.get(feature, {})
    return [f"{mapping.get(c, c.title())} ({c})" for c in codes]

def parse_opt(val):
    """Extracts the code 'b' back out from 'Bell (b)' for the backend"""
    if "(" in val and ")" in val:
        return val.split("(")[-1].strip(")")
    return val


class FungiSafeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FungiSafe Pro — Bioluminescent Foraging Predictor")
        self.geometry("1300x940")
        self.minsize(1150, 800)
        self.configure(fg_color=COLORS["bg_main"])

        self.current_mushroom = None
        self.current_toxicity = None

        try:
            self.categories = predictor.get_categories()
            self.toxicity_stats = predictor.get_toxicity_stats()
            self.feature_importance = predictor.get_feature_importance()
            self.load_error = None
        except FileNotFoundError as e:
            self.categories = None
            self.load_error = str(e)

        self._build_layout()

        if self.load_error:
            self._show_error_state()
        else:
            self._build_form()
            self._build_results_panel()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=520) 
        self.grid_columnconfigure(1, weight=1)              
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=32, pady=(28, 16))
        header.grid_columnconfigure(1, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_box, text="Mushroom Edibility Scanner", font=FONTS["display"], text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Machine Learning driven foraging analysis", font=FONTS["body"], text_color=COLORS["text_secondary"]).pack(anchor="w")

        if getattr(self, "toxicity_stats", None):
            stats_box = ctk.CTkFrame(header, fg_color="transparent")
            stats_box.grid(row=0, column=2, sticky="e")
            
            acc_chip = StatChip(stats_box, "AI Accuracy", f"{self.toxicity_stats['accuracy']*100:.1f}%", value_color=COLORS["chart_bar_alt"])
            acc_chip.pack(side="left", padx=(0, 12))
            
            avg_chip = StatChip(stats_box, "Overall Toxic Ratio", f"{self.toxicity_stats['overall_risk']*100:.1f}%", value_color=COLORS["chart_bar"])
            avg_chip.pack(side="left")

        self.form_col = ctk.CTkFrame(self, fg_color="transparent")
        self.form_col.grid(row=1, column=0, sticky="nsew", padx=(32, 16), pady=(0, 28))

        self.results_col = ctk.CTkFrame(self, fg_color="transparent")
        self.results_col.grid(row=1, column=1, sticky="nsew", padx=(16, 32), pady=(0, 28))
        self.results_col.grid_rowconfigure(1, weight=1)
        self.results_col.grid_columnconfigure(0, weight=1)

    def _show_error_state(self):
        card = Card(self)
        card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=32, pady=(0, 28))
        ctk.CTkLabel(card, text="Model Configuration Missing", font=FONTS["h1"], text_color=COLORS["warning"]).pack(pady=(40, 8))
        ctk.CTkLabel(card, text="Run train.py first to generate the classifier and metadata files.", font=FONTS["body"], text_color=COLORS["text_secondary"]).pack()

    def _build_form(self):
        card = Card(self.form_col)
        card.pack(fill="both", expand=True)

        inner = ctk.CTkScrollableFrame(card, fg_color="transparent", scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["text_muted"])
        inner.pack(fill="both", expand=True, padx=18, pady=18)
        
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)

        SectionLabel(inner, "Mushroom Morphology").grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        cats = self.categories
        
        self.f_cap_dia = LabeledEntry(inner, f"Cap Diameter ({cats['cap_range'][0]}-{cats['cap_range'][1]} cm)", default=6.5)
        self.f_cap_dia.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=8)
        
        self.f_stem_ht = LabeledEntry(inner, f"Stem Height ({cats['stem_range'][0]}-{cats['stem_range'][1]} cm)", default=5.2)
        self.f_stem_ht.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=8)

        # Uses format_opts to convert 'x' to 'Convex (x)'
        self.f_cap_shape = LabeledDropdown(inner, "Cap Shape", format_opts("cap-shape", cats["cap-shape"]))
        self.f_cap_shape.grid(row=2, column=0, sticky="ew", padx=(0, 4), pady=8)

        self.f_cap_surf = LabeledDropdown(inner, "Cap Surface", format_opts("cap-surface", cats["cap-surface"]))
        self.f_cap_surf.grid(row=2, column=1, sticky="ew", padx=(4, 0), pady=8)

        self.f_cap_col = LabeledDropdown(inner, "Cap Color", format_opts("cap-color", cats["cap-color"]))
        self.f_cap_col.grid(row=3, column=0, sticky="ew", padx=(0, 4), pady=8)

        self.f_bruise = LabeledDropdown(inner, "Does Bruise/Bleed?", format_opts("does-bruise-or-bleed", cats["does-bruise-or-bleed"]))
        self.f_bruise.grid(row=3, column=1, sticky="ew", padx=(4, 0), pady=8)

        self.f_gill_att = LabeledDropdown(inner, "Gill Attachment", format_opts("gill-attachment", cats["gill-attachment"]))
        self.f_gill_att.grid(row=4, column=0, sticky="ew", padx=(0, 4), pady=8)

        self.f_gill_spc = LabeledDropdown(inner, "Gill Spacing", format_opts("gill-spacing", cats["gill-spacing"]))
        self.f_gill_spc.grid(row=4, column=1, sticky="ew", padx=(4, 0), pady=8)

        self.f_gill_col = LabeledDropdown(inner, "Gill Color", format_opts("gill-color", cats["gill-color"]))
        self.f_gill_col.grid(row=5, column=0, columnspan=2, sticky="ew", padx=0, pady=8)
        
        SectionLabel(inner, "Environment").grid(row=6, column=0, columnspan=2, sticky="ew", pady=(16, 10))

        self.f_habitat = LabeledDropdown(inner, "Habitat", format_opts("habitat", cats["habitat"]))
        self.f_habitat.grid(row=7, column=0, sticky="ew", padx=(0, 4), pady=8)

        self.f_season = LabeledDropdown(inner, "Season", format_opts("season", cats["season"]))
        self.f_season.grid(row=7, column=1, sticky="ew", padx=(4, 0), pady=8)

        self.error_label = ctk.CTkLabel(inner, text="", font=FONTS["small"], text_color=COLORS["warning"])
        self.error_label.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        btn = PrimaryButton(inner, "Analyze Toxicity", command=self._on_predict)
        btn.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(18, 0))

    def _build_results_panel(self):
        price_card = Card(self.results_col)
        price_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        ctk.CTkLabel(price_card, text="Toxicity Probability", font=FONTS["h2"], text_color=COLORS["text_secondary"]).pack(anchor="w", padx=24, pady=(22, 0))

        self.risk_label = AnimatedToxicityLabel(price_card)
        self.risk_label.pack(anchor="w", padx=24, pady=(0, 4))

        actions_frame = ctk.CTkFrame(price_card, fg_color="transparent")
        actions_frame.pack(anchor="w", padx=24, pady=(0, 24), fill="x")

        self.compare_label = ctk.CTkLabel(
            actions_frame, text="Enter morphology traits to determine edibility.",
            font=FONTS["body"], text_color=COLORS["text_secondary"], anchor="w",
        )
        self.compare_label.pack(side="left")

        SecondaryButton(actions_frame, "Export Log", command=self._on_export).pack(side="right")

        charts_row = ctk.CTkScrollableFrame(self.results_col, fg_color="transparent", scrollbar_button_color=COLORS["border"], scrollbar_button_hover_color=COLORS["text_muted"])
        charts_row.grid(row=1, column=0, sticky="nsew")
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)

        self.importance_chart = ChartCard(charts_row, "Traits Signaling Poison")
        self.importance_chart.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))
        self._draw_importance_chart()

        self.hab_chart = ChartCard(charts_row, "Toxicity by Habitat")
        self.hab_chart.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))
        self._draw_hab_chart()
        
        self.sea_chart = LineChartCard(charts_row, "Seasonal Toxicity Trends")
        self.sea_chart.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 8))
        self._draw_sea_chart()

    def _draw_importance_chart(self):
        items = list(self.feature_importance.items())[:6]
        items.reverse()
        labels = [k.replace("_", " ").title() for k, _ in items]
        values = [v for _, v in items]
        self.importance_chart.draw_horizontal_bars(labels, values)

    def _draw_hab_chart(self, highlight_hab=None):
        by_hab = self.toxicity_stats["by_habitat"]
        mapping = FEATURE_LABELS.get("habitat", {})
        
        # Convert chart labels to human readable words
        labels = [mapping.get(k, k).title() for k in by_hab.keys()]
        values = [v * 100 for v in by_hab.values()]
        
        highlight_idx = None
        if highlight_hab:
            readable_hab = mapping.get(highlight_hab, highlight_hab.title()).title()
            if readable_hab in labels:
                highlight_idx = labels.index(readable_hab)
                
        self.hab_chart.draw_comparison_bars(labels, values, highlight_index=highlight_idx, format_as_pct=True)
        
    def _draw_sea_chart(self, highlight_sea=None):
        by_sea = self.toxicity_stats["by_season"]
        mapping = FEATURE_LABELS.get("season", {})
        
        # Convert chart labels to human readable words
        labels = [mapping.get(str(k), str(k)).title() for k in by_sea.keys()]
        risks = [v * 100 for v in by_sea.values()]
        
        highlight_idx = None
        if highlight_sea:
            readable_sea = mapping.get(str(highlight_sea), str(highlight_sea).title()).title()
            if readable_sea in labels:
                highlight_idx = labels.index(readable_sea)
                    
        self.sea_chart.draw_line_chart(labels, risks, highlight_index=highlight_idx, format_as_pct=True)

    def _on_predict(self):
        self.error_label.configure(text="")

        try:
            # parse_opt strips out the backend code exactly
            mushroom = {
                "cap-diameter": float(self.f_cap_dia.get()),
                "stem-height": float(self.f_stem_ht.get()),
                "cap-shape": parse_opt(self.f_cap_shape.get()),
                "cap-surface": parse_opt(self.f_cap_surf.get()),
                "cap-color": parse_opt(self.f_cap_col.get()),
                "does-bruise-or-bleed": parse_opt(self.f_bruise.get()),
                "gill-attachment": parse_opt(self.f_gill_att.get()),
                "gill-spacing": parse_opt(self.f_gill_spc.get()),
                "gill-color": parse_opt(self.f_gill_col.get()),
                "habitat": parse_opt(self.f_habitat.get()),
                "season": parse_opt(self.f_season.get()),
            }
        except ValueError:
            self.error_label.configure(text="Ensure cap diameter and stem height are numbers.")
            return

        try:
            result = predictor.predict_toxicity(mushroom)
        except Exception as e:
            self.error_label.configure(text=f"Prediction failed: {e}")
            return

        self.current_mushroom = mushroom
        self.current_toxicity = result["toxicity_probability"]

        self.risk_label.animate_to(self.current_toxicity)

        if self.current_toxicity < 50:
            msg = "Likely Edible. Safe foraging probability is high."
        else:
            msg = "WARNING: Highly likely to be Poisonous. Do not consume."

        self.compare_label.configure(text=msg)
        
        self._draw_hab_chart(highlight_hab=mushroom["habitat"])
        self._draw_sea_chart(highlight_sea=mushroom["season"])

    def _on_export(self):
        if not self.current_mushroom or not self.current_toxicity:
            self.error_label.configure(text="Please run an analysis before exporting.")
            return

        filename = ctk.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All Files", "*.*")],
            title="Save Foraging Report",
            initialfile=f"FungiSafe_Report.txt"
        )

        if not filename:
            return  

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=========================================\n")
                f.write("       FUNGISAFE PRO FORAGING LOG        \n")
                f.write("=========================================\n\n")
                f.write(f"Generated: {now}\n\n")

                f.write("MUSHROOM MORPHOLOGY\n")
                f.write("-----------------------------------------\n")
                
                # Make the export file beautifully formatted with the translation map
                for key, val in self.current_mushroom.items():
                    label = key.replace("-", " ").title()
                    if isinstance(val, str):
                        mapping = FEATURE_LABELS.get(key, {})
                        readable = mapping.get(val, val.title())
                        display_val = f"{readable} ({val})"
                    else:
                        display_val = str(val)
                    f.write(f"{label.ljust(22)}: {display_val}\n")

                f.write("\nTOXICITY ASSESSMENT\n")
                f.write("-----------------------------------------\n")
                f.write(f"Poison Probability    : {self.current_toxicity}%\n")

                if self.current_toxicity >= 50:
                    f.write("Status                : POISONOUS (DO NOT CONSUME)\n")
                else:
                    f.write("Status                : LIKELY EDIBLE\n")

                f.write("\nDisclaimer: Never eat a wild mushroom based purely on an AI prediction.\n")
                f.write("Always verify with a local expert mycologist.\n")
                
        except Exception as e:
            self.error_label.configure(text=f"Export failed: {e}")

def main():
    apply_base_theme()
    app = FungiSafeApp()
    app.mainloop()

if __name__ == "__main__":
    main()