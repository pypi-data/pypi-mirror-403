"""Interactive Plotly-based visualization helpers.

These helpers produce standalone HTML outputs or return `plotly` figures
for interactive exploration in notebooks or browsers.
"""

from typing import Optional

try:
    import plotly.graph_objects as go
except Exception:
    go = None  # type: ignore

import numpy as _np


def _ensure_plotly():
    if go is None:
        raise RuntimeError("plotly is required for interactive visualizations")


def quiver_plotly(
    X,
    Y,
    U,
    V,
    scale: float = 1.0,
    title: Optional[str] = None,
    save: Optional[str] = None,
):
    """Create a plotly quiver (arrows) figure. X,Y,U,V may be NumPy arrays or lists."""
    _ensure_plotly()
    X = _np.asarray(X)
    Y = _np.asarray(Y)
    U = _np.asarray(U)
    V = _np.asarray(V)

    # create arrows as line segments with coneheads using scatter
    fig = go.Figure()
    # flatten
    xs = X.ravel()
    ys = Y.ravel()
    us = U.ravel() * scale
    vs = V.ravel() * scale

    for x, y, u, v in zip(xs, ys, us, vs):
        fig.add_trace(
            go.Scatter(
                x=[x, x + u],
                y=[y, y + v],
                mode="lines",
                line=dict(width=2),
                showlegend=False,
            )
        )
        # small marker for arrow head
        fig.add_trace(
            go.Scatter(
                x=[x + u],
                y=[y + v],
                mode="markers",
                marker=dict(size=4),
                showlegend=False,
            )
        )

    fig.update_layout(
        title=title or "Quiver plot",
        xaxis=dict(constrain="domain"),
        yaxis=dict(scaleanchor="x"),
    )
    if save:
        fig.write_html(save)
    return fig


def surface_plotly(X, Y, Z, title: Optional[str] = None, save: Optional[str] = None):
    _ensure_plotly()
    fig = go.Figure(
        data=[go.Surface(z=_np.asarray(Z), x=_np.asarray(X), y=_np.asarray(Y))]
    )
    fig.update_layout(title=title or "Parametric surface")
    if save:
        fig.write_html(save)
    return fig


__all__ = ["quiver_plotly", "surface_plotly"]
