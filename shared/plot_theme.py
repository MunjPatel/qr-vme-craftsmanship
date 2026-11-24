"""Consistent visual theme for Plotly / Streamlit charts (slate + teal, not purple-default)."""

from __future__ import annotations

COLORS = {
    "bg": "#0f1419",
    "panel": "#1a2332",
    "text": "#e7ecf3",
    "muted": "#8b9bb4",
    "accent": "#2dd4bf",
    "accent2": "#38bdf8",
    "warn": "#f59e0b",
    "danger": "#f87171",
    "good": "#34d399",
    "grid": "#243044",
}


def apply_plotly_theme(fig):
    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text"], family="IBM Plex Sans, Segoe UI, sans-serif"),
        title_font=dict(size=18, color=COLORS["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["muted"])),
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
        yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    )
    return fig
