"""
theme.py — Centralized design tokens for FungiSafe Pro.
"""

import customtkinter as ctk

# ---------------------------------------------------------------
# Color palette — Dark Earth & Bioluminescence
# ---------------------------------------------------------------
COLORS = {
    "bg_main":        "#0a0f0c",  # Extremely dark forest green/black
    "bg_sidebar":     "#121a14",  
    "bg_card":        "#121a14",  
    "bg_card_hover":  "#1b261e",  
    "bg_input":       "#1b261e",  
    "border":         "#2d3d33",  

    "accent":         "#d946ef",  # Toxic Magenta (Poisonous)
    "accent_hover":   "#c026d3",  
    "accent_soft":    "#d946ef22",

    "success":        "#22c55e",  # Leaf Green (Edible)
    "success_soft":   "#22c55e22",
    "warning":        "#eab308",  # Amber/Yellow

    "text_primary":   "#f8fafc",  
    "text_secondary": "#94a3b8",  
    "text_muted":     "#475569",  

    "chart_bar":      "#d946ef",  # Toxic
    "chart_bar_alt":  "#22c55e",  # Safe
    "chart_grid":     "#2d3d33",  
}

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"

FONTS = {
    "display":   (FONT_FAMILY, 38, "bold"),
    "h1":        (FONT_FAMILY, 24, "bold"),
    "h2":        (FONT_FAMILY, 18, "bold"),
    "body":      (FONT_FAMILY, 14, "normal"),
    "body_bold": (FONT_FAMILY, 14, "bold"),
    "small":     (FONT_FAMILY, 12, "bold"),
    "price":     (FONT_FAMILY, 64, "bold"),
    "mono":      (FONT_FAMILY_MONO, 12, "normal"),
}

RADIUS = 14
PAD = 20

def apply_base_theme():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")