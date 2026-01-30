"""Vectorized grid helpers for evaluating fields and computing derivatives.

All helpers below require NumPy and expect vectorized callables that accept
mesh arrays as returned by `numpy.meshgrid` (e.g. `X, Y = meshgrid(x, y)`).
"""

from typing import Any, Callable, Optional, Sequence, Tuple, cast

import numpy as np


def mesh(*axes: Sequence[Any], indexing: str = "xy") -> Tuple[np.ndarray, ...]:
    """Create mesh arrays from 1D axes. Returns the same as `np.meshgrid`.

    Example:
        X, Y = mesh(x, y)
    """
    _mesh_fn: Any = np.meshgrid
    return cast(Tuple[np.ndarray, ...], _mesh_fn(*axes, indexing=indexing))


def points_array(*axes: Sequence[Any], indexing: str = "xy") -> np.ndarray:
    """Return an array of points shaped (*grid_shape, ndim).

    For 2D, shape is (ny, nx, 2) when using `indexing='xy'`.
    """
    grids = mesh(*axes, indexing=indexing)
    return np.stack(grids, axis=-1)


def gradient_on_grid(
    scalar_field: Callable[..., np.ndarray],
    *axes: Sequence[Any],
    indexing: str = "xy",
    spacing: Optional[Sequence[Any]] = None,
    edge_order: int = 2
) -> Tuple[np.ndarray, ...]:
    """Compute the gradient of a scalar field on a grid.

    `scalar_field` must be vectorized and accept mesh arrays: e.g. `f(X, Y)`.
    Returns a tuple of arrays (d/dx0, d/dx1, ...), each same shape as the mesh.
    """
    grids = mesh(*axes, indexing=indexing)
    values = scalar_field(*grids)
    if spacing is None:
        # construct spacing in the order np.gradient expects for the
        # values array. For `indexing='xy'`, the first two axes are swapped.
        if indexing == "ij" or len(axes) < 2:
            spacing_arrs = [np.asarray(a) for a in axes]
        else:
            spacing_arrs = [np.asarray(axes[1]), np.asarray(axes[0])] + [
                np.asarray(a) for a in axes[2:]
            ]
        spacing = spacing_arrs
    # np.gradient typing is picky; treat result as Any then convert
    grads_any: Any = np.gradient(values, *spacing, edge_order=edge_order)  # type: ignore[call-overload,arg-type]
    grads = tuple(grads_any)
    # Map grads (which are ordered by array axes) back to the order of the
    # input axes. For `indexing='xy'` the first two are swapped.
    if indexing == "ij" or len(axes) < 2:
        return grads
    else:
        reordered = [grads[1], grads[0]] + list(grads[2:])
        return tuple(reordered)


def divergence_on_grid(
    vector_field: Callable[..., Sequence[np.ndarray]],
    *axes: Sequence[Any],
    indexing: str = "xy",
    spacing: Optional[Sequence[Any]] = None,
    edge_order: int = 2
) -> np.ndarray:
    """Compute divergence of a vector field on a grid.

    `vector_field` must be vectorized and accept mesh arrays, returning a
    sequence of component arrays (Fx, Fy, ...).
    Returns an array of divergence values with the same shape as the mesh.
    """
    grids = mesh(*axes, indexing=indexing)
    components = vector_field(*grids)
    if spacing is None:
        if indexing == "ij" or len(axes) < 2:
            spacing_arrs = [np.asarray(a) for a in axes]
        else:
            spacing_arrs = [np.asarray(axes[1]), np.asarray(axes[0])] + [
                np.asarray(a) for a in axes[2:]
            ]
        spacing = spacing_arrs
    div = np.zeros_like(components[0], dtype=float)
    # build mapping from original axis index -> array axis index
    if indexing == "ij" or len(axes) < 2:
        axis_map = list(range(len(axes)))
    else:
        axis_map = [1, 0] + list(range(2, len(axes)))

    for i, comp in enumerate(components):
        derivs_any: Any = np.gradient(comp, *spacing, edge_order=edge_order)  # type: ignore[call-overload,arg-type]
        derivs = tuple(derivs_any)
        array_axis = axis_map[i]
        div += derivs[array_axis]
    return div


def curl_on_grid(
    vector_field: Callable[..., Sequence[np.ndarray]],
    *axes: Sequence[Any],
    indexing: str = "xy",
    spacing: Optional[Sequence[Any]] = None,
    edge_order: int = 2
) -> np.ndarray:
    """Compute curl on a 3D grid. `vector_field` must be vectorized.

    Returns an array with the same spatial shape and an extra last axis of size 3
    holding the curl vector at each grid point.
    """
    if len(axes) != 3:
        raise TypeError("curl_on_grid requires 3 axes (3D grid)")
    grids = mesh(*axes, indexing=indexing)
    Fx, Fy, Fz = vector_field(*grids)
    if spacing is None:
        if len(axes) < 2 or indexing == "ij":
            spacing_arrs = [np.asarray(a) for a in axes]
        else:
            spacing_arrs = [np.asarray(axes[1]), np.asarray(axes[0])] + [
                np.asarray(a) for a in axes[2:]
            ]
        spacing = spacing_arrs

    dFx_any: Any = np.gradient(Fx, *spacing, edge_order=edge_order)  # type: ignore[call-overload,arg-type]
    dFy_any: Any = np.gradient(Fy, *spacing, edge_order=edge_order)  # type: ignore[call-overload,arg-type]
    dFz_any: Any = np.gradient(Fz, *spacing, edge_order=edge_order)  # type: ignore[call-overload,arg-type]
    dFx = tuple(dFx_any)
    dFy = tuple(dFy_any)
    dFz = tuple(dFz_any)

    # map original axis indices to array axis indices
    if indexing == "ij" or len(axes) < 2:
        axis_map = list(range(len(axes)))
    else:
        axis_map = [1, 0] + list(range(2, len(axes)))

    # helper to pick derivative of component wrt original axis j
    def deriv(comp_derivs, orig_axis_index):
        return comp_derivs[axis_map[orig_axis_index]]

    # dFz/dy - dFy/dz, dFx/dz - dFz/dx, dFy/dx - dFx/dy
    cx = deriv(dFz, 1) - deriv(dFy, 2)
    cy = deriv(dFx, 2) - deriv(dFz, 0)
    cz = deriv(dFy, 0) - deriv(dFx, 1)

    return np.stack([cx, cy, cz], axis=-1)
