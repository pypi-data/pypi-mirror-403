import numpy as np

from vectorcalculus import (curl_on_grid, divergence_on_grid, gradient_on_grid,
                            mesh)


def test_gradient_on_grid_2d():
    x = np.linspace(0, 1, 21)
    y = np.linspace(-1, 1, 31)

    def f(X, Y):
        return X * Y + 2 * (Y**2)

    gx, gy = gradient_on_grid(f, x, y)
    # analytic gradients
    X, Y = mesh(x, y)
    ax = Y
    ay = X + 4 * Y
    assert np.allclose(gx, ax, atol=1e-6)
    assert np.allclose(gy, ay, atol=1e-6)


def test_divergence_on_grid_2d():
    x = np.linspace(-0.5, 0.5, 21)
    y = np.linspace(-1.0, 1.0, 41)

    def F(X, Y):
        return (X**2, Y**2)

    div = divergence_on_grid(F, x, y)
    X, Y = mesh(x, y)
    expected = 2 * X + 2 * Y
    assert np.allclose(div, expected, atol=1e-6)


def test_curl_on_grid_3d():
    x = np.linspace(-0.2, 0.2, 11)
    y = np.linspace(-0.1, 0.1, 9)
    z = np.linspace(0.0, 0.5, 13)

    def G(X, Y, Z):
        return (-Y, X, np.zeros_like(X))

    c = curl_on_grid(G, x, y, z)
    # curl is [0,0,2]
    assert np.allclose(c[..., 0], 0.0, atol=1e-4)
    assert np.allclose(c[..., 1], 0.0, atol=1e-4)
    assert np.allclose(c[..., 2], 2.0, atol=5e-3)
