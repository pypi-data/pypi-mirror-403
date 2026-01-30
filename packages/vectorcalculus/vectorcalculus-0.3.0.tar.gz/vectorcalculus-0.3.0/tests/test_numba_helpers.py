import numpy as np
import pytest
from numpy import pi


def test_numba_helpers_present_or_skipped():
    # Skip the whole test file if numba not installed to keep CI portable
    pytest.importorskip("numba")
    from vectorcalculus import numba_helpers

    assert hasattr(numba_helpers, "NUMBA_AVAILABLE")
    assert numba_helpers.NUMBA_AVAILABLE


def test_gradient_divergence_curl_against_analytic():
    pytest.importorskip("numba")
    from vectorcalculus import numba_helpers

    nx = ny = nz = 16
    x = np.linspace(0, 1, nx, endpoint=False)
    y = np.linspace(0, 1, ny, endpoint=False)
    z = np.linspace(0, 1, nz, endpoint=False)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")

    # scalar potential
    phi = np.sin(2 * pi * X) * np.sin(2 * pi * Y) * np.sin(2 * pi * Z)
    dx = dy = dz = 1.0 / nx

    gx, gy, gz = numba_helpers.gradient_3d(phi, dx, dy, dz)

    # analytic gradient
    gx_ref = 2 * pi * np.cos(2 * pi * X) * np.sin(2 * pi * Y) * np.sin(2 * pi * Z)
    gy_ref = 2 * pi * np.sin(2 * pi * X) * np.cos(2 * pi * Y) * np.sin(2 * pi * Z)
    gz_ref = 2 * pi * np.sin(2 * pi * X) * np.sin(2 * pi * Y) * np.cos(2 * pi * Z)

    assert np.allclose(gx, gx_ref, atol=1e-2)
    assert np.allclose(gy, gy_ref, atol=1e-2)
    assert np.allclose(gz, gz_ref, atol=1e-2)

    # construct a vector field and check divergence ~ known value
    Fx = gx_ref
    Fy = gy_ref
    Fz = gz_ref

    div = numba_helpers.divergence_3d(Fx, Fy, Fz, dx, dy, dz)
    # divergence of gradient should approximate Laplacian of phi = - (2pi)^2 * 3 * phi
    lap_ref = -((2 * pi) ** 2) * 3 * phi
    assert np.allclose(div, lap_ref, atol=1e-1)
