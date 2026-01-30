import numpy as np

from vectorcalculus import curl_np, divergence_np, gradient_np, laplacian_np


def test_gradient_np():
    def f(p):
        # vectorized: p is numpy array
        x, y, z = p
        return x * y + z * z

    g = gradient_np(f, np.array([1.3, -2.2, 0.5]))
    assert np.allclose(g, np.array([-2.2, 1.3, 1.0]), atol=1e-6)


def test_divergence_np_and_curl_np():
    def F(p):
        x, y, z = p
        return np.array([x * x, y * y, z * z])

    d = divergence_np(F, np.array([0.5, -0.2, 1.3]))
    assert abs(d - (2 * 0.5 + 2 * -0.2 + 2 * 1.3)) < 1e-6

    def G(p):
        x, y, z = p
        return np.array([-y, x, 0.0])

    c = curl_np(G, np.array([0.1, 0.2, 0.3]))
    assert np.allclose(c, np.array([0.0, 0.0, 2.0]), atol=1e-4)


def test_laplacian_np():
    def f(p):
        x, y = p
        return x * x + y * y

    val = laplacian_np(f, np.array([1.0, 2.0]))
    # Laplacian of x^2 + y^2 is 2 + 2 = 4
    assert abs(val - 4.0) < 1e-3
