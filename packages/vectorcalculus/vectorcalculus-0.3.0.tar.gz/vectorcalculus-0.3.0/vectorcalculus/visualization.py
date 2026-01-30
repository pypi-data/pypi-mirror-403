from __future__ import annotations

from typing import Callable, Optional, Sequence, Tuple, Any

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
except Exception:
    plt = None  # type: ignore

try:
    import numpy as _np
except Exception:
    _np = None  # type: ignore


def _ensure_pyplot():
    if plt is None:
        raise RuntimeError("matplotlib is required for visualization")


def plot_vector_field_2d(
    field: Callable[[Sequence[float]], Sequence[float]],
    xlim: Tuple[float, float],
    ylim: Tuple[float, float],
    nx: int = 20,
    ny: int = 20,
    scale: Optional[float] = None,
    ax=None,
    save: Optional[str] = None,
    show: bool = True,
 ) -> Any:
    """Plot a 2D vector field using `quiver`.

    - `field` should accept a point `(x,y,...)` and return a sequence `(Fx,Fy,...)`.
    - If `ax` is None a new figure/axes are created.
    - If `save` is provided, the figure is written to that path.
    """
    _ensure_pyplot()
    if _np is None:
        xs = [xlim[0] + (xlim[1] - xlim[0]) * i / (nx - 1) for i in range(nx)]
        ys = [ylim[0] + (ylim[1] - ylim[0]) * j / (ny - 1) for j in range(ny)]
        X = [[x for x in xs] for _ in ys]
        Y = [[y for _ in xs] for y in ys]
        U = [[field((x, y))[0] for x in xs] for y in ys]
        V = [[field((x, y))[1] for x in xs] for y in ys]
    else:
        xs = _np.linspace(xlim[0], xlim[1], nx)
        ys = _np.linspace(ylim[0], ylim[1], ny)
        X, Y = _np.meshgrid(xs, ys)
        U = _np.empty_like(X)
        V = _np.empty_like(Y)
        for i in range(ny):
            for j in range(nx):
                fx, fy = field((float(X[i, j]), float(Y[i, j])))[:2]
                U[i, j] = fx
                V[i, j] = fy

    fig_owned = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 5))
        fig_owned = True
    else:
        fig = ax.figure

    ax.quiver(X, Y, U, V, scale=scale)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    if save and fig_owned:
        fig.savefig(save, bbox_inches="tight")
    if show and fig_owned:
        plt.show()
    return fig


def plot_streamlines_2d(
    field: Callable[[Sequence[float]], Sequence[float]],
    xlim: Tuple[float, float],
    ylim: Tuple[float, float],
    density: float = 1.0,
    nx: int = 200,
    ny: int = 200,
    ax=None,
    save: Optional[str] = None,
    show: bool = True,
 ) -> Any:
    """Plot streamlines of a 2D vector field using `streamplot`."""
    _ensure_pyplot()
    if _np is None:
        raise RuntimeError("NumPy is required for streamlines")

    xs = _np.linspace(xlim[0], xlim[1], nx)
    ys = _np.linspace(ylim[0], ylim[1], ny)
    X, Y = _np.meshgrid(xs, ys)
    U = _np.empty_like(X)
    V = _np.empty_like(Y)
    for i in range(ny):
        for j in range(nx):
            fx, fy = field((float(X[i, j]), float(Y[i, j])))[:2]
            U[i, j] = fx
            V[i, j] = fy

    fig_owned = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 5))
        fig_owned = True
    else:
        fig = ax.figure

    ax.streamplot(X, Y, U, V, density=density)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")

    if save and fig_owned:
        fig.savefig(save, bbox_inches="tight")
    if show and fig_owned:
        plt.show()
    return fig


def plot_surface_parametric(
    param: Callable[[float, float], Sequence[float]],
    u_range: Tuple[float, float],
    v_range: Tuple[float, float],
    mu: int = 50,
    mv: int = 50,
    ax=None,
    save: Optional[str] = None,
    show: bool = True,
 ) -> Any:
    """Plot a parametric surface r(u,v). Requires 3D projection (mpl_toolkits)."""
    _ensure_pyplot()
    if _np is None:
        raise RuntimeError("NumPy is required for surface plotting")

    us = _np.linspace(u_range[0], u_range[1], mu)
    vs = _np.linspace(v_range[0], v_range[1], mv)
    U, V = _np.meshgrid(us, vs)
    X = _np.empty_like(U)
    Y = _np.empty_like(U)
    Z = _np.empty_like(U)
    for i in range(mv):
        for j in range(mu):
            px, py, pz = param(float(U[i, j]), float(V[i, j]))
            X[i, j] = px
            Y[i, j] = py
            Z[i, j] = pz

    fig_owned = False
    if ax is None:
        fig = plt.figure(figsize=(7, 5))
        ax = fig.add_subplot(111, projection="3d")
        fig_owned = True
    else:
        fig = ax.figure

    ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap="viridis", edgecolor="none")
    if save and fig_owned:
        fig.savefig(save, bbox_inches="tight")
    if show and fig_owned:
        plt.show()
    return fig
