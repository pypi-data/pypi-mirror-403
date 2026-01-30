import numpy as np
from numpy import pi

from vectorcalculus.operations import (curl_grid_3d, divergence_grid_3d,
                                       gradient_grid_3d)


def test_grid_wrappers_fallback_numpy():
    nx = ny = nz = 16
    x = np.linspace(0, 1, nx, endpoint=False)
    y = np.linspace(0, 1, ny, endpoint=False)
    z = np.linspace(0, 1, nz, endpoint=False)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")

    phi = np.sin(2 * pi * X) * np.sin(2 * pi * Y) * np.sin(2 * pi * Z)
    dx = dy = dz = 1.0 / nx

    gx, gy, gz = gradient_grid_3d(phi, dx, dy, dz, use_numba=False)

    gx_ref = 2 * pi * np.cos(2 * pi * X) * np.sin(2 * pi * Y) * np.sin(2 * pi * Z)
    gy_ref = 2 * pi * np.sin(2 * pi * X) * np.cos(2 * pi * Y) * np.sin(2 * pi * Z)
    gz_ref = 2 * pi * np.sin(2 * pi * X) * np.sin(2 * pi * Y) * np.cos(2 * pi * Z)

    # central-difference accuracy on a coarse grid: allow relaxed tolerance
    assert np.allclose(gx, gx_ref, atol=2e-1)
    assert np.allclose(gy, gy_ref, atol=2e-1)
    assert np.allclose(gz, gz_ref, atol=2e-1)

    Fx = gx_ref
    Fy = gy_ref
    Fz = gz_ref

    div = divergence_grid_3d(Fx, Fy, Fz, dx, dy, dz, use_numba=False)
    lap_ref = -((2 * pi) ** 2) * 3 * phi
    # allow relaxed tolerance for discrete divergence of exact gradients
    assert np.allclose(div, lap_ref, atol=5.0)

    cx, cy, cz = curl_grid_3d(Fx, Fy, Fz, dx, dy, dz, use_numba=False)
    assert np.max(np.abs(cx)) < 1e-8
    assert np.max(np.abs(cy)) < 1e-8
    assert np.max(np.abs(cz)) < 1e-8
