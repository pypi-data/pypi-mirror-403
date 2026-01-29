
import plotly.graph_objects as go
from typing import Optional, Dict, Any

# --- ANTIGRAVITY THEME DEFINITIONS ---
# --- ANTIGRAVITY THEME DEFINITIONS ---
THEME_COLORS = {
    "background": "#ffffff",
    "plot_background": "#f8fafc",
    "text": "#1e293b",          # Slate-800
    "secondary_text": "#64748b", # Slate-500
    "grid": "#e2e8f0",          # Slate-200
    "primary_accent": "#4f46e5", # Indigo-600
    "secondary_accent": "#818cf8",
    "tertiary_accent": "#94a3b8",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444"
}

ANTIGRAVITY_FONT = "Outfit, sans-serif"

def apply_antigravity_theme(fig: go.Figure, height: int = 350) -> go.Figure:
    """
    Applies the standardized Decyphr Antigravity aesthetic (Light Mode) to a Plotly figure.
    
    Features:
    - Transparent backgrounds (paper and plot)
    - 'Outfit' font family
    - Minimalist grid lines
    - No surrounding legends/clutter by default (can be overridden)
    """
    fig.update_layout(
        template="simple_white",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(
            family=ANTIGRAVITY_FONT,
            size=12,
            color=THEME_COLORS['text']
        ),
        margin=dict(l=0, r=0, t=30, b=20),
        height=height,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family=ANTIGRAVITY_FONT,
            font_color=THEME_COLORS['text']
        ),
        # Minimalist Axis
        xaxis=dict(
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor=THEME_COLORS['text'], # Darker line for axis
            tickfont=dict(color=THEME_COLORS['secondary_text'])
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=THEME_COLORS['grid'],
            showline=False,
            zeroline=False,
            tickfont=dict(color=THEME_COLORS['secondary_text'])
        ),
        title_font=dict(color=THEME_COLORS['text'])
    )
    return fig

def get_theme_colors() -> Dict[str, str]:
    """Returns the dictionary of theme colors for use in specific plot traces."""
    return THEME_COLORS
