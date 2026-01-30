import numpy as np
from numpy import pi

from vectorcalculus.decompositions import helmholtz_decompose_3d


def test_helmholtz_decompose_3d_reconstruction_and_properties():
    # small periodic grid
    nx = ny = nz = 16
    x = np.linspace(0, 1, nx, endpoint=False)
    y = np.linspace(0, 1, ny, endpoint=False)
    z = np.linspace(0, 1, nz, endpoint=False)
    Z, Y, X = np.meshgrid(z, y, x, indexing="ij")  # shape (nz, ny, nx)

    # scalar potential phi with known gradient
    phi = np.sin(2 * pi * X) * np.sin(2 * pi * Y) * np.sin(2 * pi * Z)
    # analytic gradient
    grad_phi_x = 2 * pi * np.cos(2 * pi * X) * np.sin(2 * pi * Y) * np.sin(2 * pi * Z)
    grad_phi_y = 2 * pi * np.sin(2 * pi * X) * np.cos(2 * pi * Y) * np.sin(2 * pi * Z)
    grad_phi_z = 2 * pi * np.sin(2 * pi * X) * np.sin(2 * pi * Y) * np.cos(2 * pi * Z)

    # construct a divergence-free field (simple periodic functions)
    sol_x = np.sin(2 * pi * Y)
    sol_y = np.sin(2 * pi * Z)
    sol_z = np.sin(2 * pi * X)

    F = np.stack((grad_phi_x + sol_x, grad_phi_y + sol_y, grad_phi_z + sol_z), axis=-1)

    Fi, Fs, phi_out = helmholtz_decompose_3d(F, dx=1 / nx, dy=1 / ny, dz=1 / nz)

    # reconstruction
    F_rec = Fi + Fs
    assert np.allclose(F_rec, F, atol=1e-8)

    # solenoidal part should be (numerically) divergence-free
    Fx_hat = np.fft.fftn(Fs[..., 0])
    Fy_hat = np.fft.fftn(Fs[..., 1])
    Fz_hat = np.fft.fftn(Fs[..., 2])

    kx = 2 * pi * np.fft.fftfreq(nx, 1 / nx)
    ky = 2 * pi * np.fft.fftfreq(ny, 1 / ny)
    kz = 2 * pi * np.fft.fftfreq(nz, 1 / nz)
    KZ, KY, KX = np.meshgrid(kz, ky, kx, indexing="ij")
    div_hat = 1j * (KX * Fx_hat + KY * Fy_hat + KZ * Fz_hat)
    div = np.fft.ifftn(div_hat).real
    assert np.allclose(div, 0, atol=1e-8)

    # irrotational component should have (numerically) near-zero curl
    # compute curl in spectral space: curl = ifft(i k x F_hat)
    Fi_x_hat = np.fft.fftn(Fi[..., 0])
    Fi_y_hat = np.fft.fftn(Fi[..., 1])
    Fi_z_hat = np.fft.fftn(Fi[..., 2])

    curl_x_hat = 1j * (KY * Fi_z_hat - KZ * Fi_y_hat)
    curl_y_hat = 1j * (KZ * Fi_x_hat - KX * Fi_z_hat)
    curl_z_hat = 1j * (KX * Fi_y_hat - KY * Fi_x_hat)

    curl_x = np.fft.ifftn(curl_x_hat).real
    curl_y = np.fft.ifftn(curl_y_hat).real
    curl_z = np.fft.ifftn(curl_z_hat).real

    max_curl = np.max(np.abs(np.stack((curl_x, curl_y, curl_z))))
    assert max_curl < 1e-8
