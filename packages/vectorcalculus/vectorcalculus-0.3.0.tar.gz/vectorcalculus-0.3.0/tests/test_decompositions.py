import numpy as np

from vectorcalculus.decompositions import helmholtz_decompose_2d


def test_helmholtz_decompose_trivial_components():
    # build grid
    nx, ny = 64, 64
    x = np.linspace(0, 2 * np.pi, nx, endpoint=False)
    y = np.linspace(0, 2 * np.pi, ny, endpoint=False)
    X, Y = np.meshgrid(x, y)

    # scalar potentials
    phi = np.sin(X) * np.cos(Y)
    psi = np.cos(X) * np.sin(Y)

    # grad(phi)
    dphi_dx = np.cos(X) * np.cos(Y)
    dphi_dy = -np.sin(X) * np.sin(Y)

    # rot(psi) in 2D: (dpsi/dy, -dpsi/dx)
    dpsi_dx = -np.sin(X) * np.sin(Y)
    dpsi_dy = np.cos(X) * np.cos(Y)
    rot_x = dpsi_dy
    rot_y = -dpsi_dx

    Fx = dphi_dx + rot_x
    Fy = dphi_dy + rot_y
    F = np.stack((Fx, Fy), axis=-1)

    Fi, Fs = helmholtz_decompose_2d(F, dx=(x[1] - x[0]), dy=(y[1] - y[0]))

    # Fi should approximate grad(phi)
    err_i = np.max(np.abs(Fi[..., 0] - dphi_dx)) + np.max(np.abs(Fi[..., 1] - dphi_dy))
    err_s = np.max(np.abs(Fs[..., 0] - rot_x)) + np.max(np.abs(Fs[..., 1] - rot_y))
    assert err_i < 1e-6
    assert err_s < 1e-6
