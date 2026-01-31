# Flux-RX Themes Module: Visual styling configuration
from __future__ import annotations

from typing import Any

# Single professional dark theme
THEME: dict[str, Any] = {
    "name": "Flux",
    "colors": {
        "background": "#0d1117",
        "paper": "#161b22",
        "surface": "#21262d",
        "primary": "#58a6ff",
        "secondary": "#7ee787",
        "accent": "#ff7b72",
        "warning": "#d29922",
        "text": "#c9d1d9",
        "text_muted": "#8b949e",
        "grid": "#30363d",
        "border": "#30363d",
        "positive": "#3fb950",
        "negative": "#f85149",
    },
    "palette": [
        "#58a6ff",
        "#7ee787",
        "#ff7b72",
        "#d2a8ff",
        "#79c0ff",
        "#ffa657",
        "#a5d6ff",
        "#f778ba",
    ],
    "font": {
        "family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        "size": 12,
        "color": "#c9d1d9",
    },
    "title_font": {
        "family": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
        "size": 18,
        "color": "#ffffff",
    },
}

DEFAULT_THEME = "flux"


def get_theme(name: str = DEFAULT_THEME) -> dict[str, Any]:
    """Get the theme configuration."""
    return THEME


def create_layout(
    theme: dict[str, Any],
    title: str = "",
    height: int = 500,
    show_legend: bool = True,
    x_title: str = "",
    y_title: str = "",
) -> dict[str, Any]:
    """Create a Plotly layout from theme configuration."""
    colors = theme["colors"]
    font = theme["font"]
    title_font = theme["title_font"]
    
    return {
        "template": "plotly_dark",
        "paper_bgcolor": colors["paper"],
        "plot_bgcolor": colors["background"],
        "height": height,
        "margin": {"l": 60, "r": 30, "t": 60 if title else 30, "b": 50},
        "title": {
            "text": title,
            "font": title_font,
            "x": 0.02,
            "xanchor": "left",
        } if title else None,
        "font": font,
        "showlegend": show_legend,
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "font": {"color": colors["text"], "size": 11},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        "xaxis": {
            "title": {"text": x_title, "font": {"color": colors["text_muted"]}},
            "gridcolor": colors["grid"],
            "gridwidth": 1,
            "linecolor": colors["border"],
            "tickfont": {"color": colors["text_muted"], "size": 10},
            "zeroline": False,
            "showspikes": True,
            "spikecolor": colors["primary"],
            "spikethickness": 1,
            "spikedash": "dot",
            "spikemode": "across",
        },
        "yaxis": {
            "title": {"text": y_title, "font": {"color": colors["text_muted"]}},
            "gridcolor": colors["grid"],
            "gridwidth": 1,
            "linecolor": colors["border"],
            "tickfont": {"color": colors["text_muted"], "size": 10},
            "zeroline": False,
            "side": "right",
        },
        "hovermode": "x unified",
        "hoverlabel": {
            "bgcolor": colors["surface"],
            "bordercolor": colors["border"],
            "font": {"color": colors["text"], "size": 12},
        },
    }


def apply_theme(fig: Any) -> Any:
    """Apply the theme to a Plotly figure."""
    layout = create_layout(THEME)
    fig.update_layout(**layout)
    return fig


def get_colorscale(diverging: bool = False) -> list:
    """Get a colorscale for heatmaps."""
    colors = THEME["colors"]
    
    if diverging:
        return [
            [0.0, colors["negative"]],
            [0.5, colors["background"]],
            [1.0, colors["positive"]],
        ]
    
    return [
        [0.0, colors["background"]],
        [0.5, colors["primary"]],
        [1.0, colors["secondary"]],
    ]


def get_heatmap_colorscale() -> list:
    """Get the colorscale for monthly returns heatmap."""
    colors = THEME["colors"]
    
    return [
        [0.0, colors["negative"]],
        [0.35, "#3d1f1f"],
        [0.5, colors["surface"]],
        [0.65, "#1f3d1f"],
        [1.0, colors["positive"]],
    ]
