"""Helmholtz / Hodge-style decompositions using FFT-based Poisson solves.

Current implementation assumes periodic boundary conditions and works for
2D vector fields on a regular grid. The functions return the irrotational
(curl-free) and solenoidal (divergence-free) components.
"""

from typing import Tuple

import numpy as _np


def _fft_wave_numbers(n: int, d: float):
    # angular wave numbers
    k = 2 * _np.pi * _np.fft.fftfreq(n, d)
    return k


def helmholtz_decompose_2d(
    F: _np.ndarray, dx: float = 1.0, dy: float = 1.0
) -> Tuple[_np.ndarray, _np.ndarray]:
    """Decompose a 2D vector field F(x,y) into grad(phi) (irrotational)
    and a divergence-free component via FFT Poisson solves.

    Parameters
    - F: array of shape (ny, nx, 2) representing (Fx, Fy) on a regular grid
    - dx, dy: grid spacings

    Returns (Fi, Fs) where Fi is curl-free (grad phi) and Fs is divergence-free.
    """
    if _np is None:
        raise RuntimeError("NumPy is required for helmholtz_decompose_2d")

    if F.ndim != 3 or F.shape[2] != 2:
        raise ValueError("F must be an array of shape (ny, nx, 2)")

    ny, nx, _ = F.shape
    Fx = F[:, :, 0]
    Fy = F[:, :, 1]

    # compute divergence and curl (z-component) in real space
    # periodic finite differences via FFT are simplest in spectral domain
    # compute Fourier transforms
    Fx_hat = _np.fft.fft2(Fx)
    Fy_hat = _np.fft.fft2(Fy)

    kx = _fft_wave_numbers(nx, dx)
    ky = _fft_wave_numbers(ny, dy)
    KX, KY = _np.meshgrid(kx, ky)
    K2 = KX**2 + KY**2

    # divergence in Fourier space: i*(kx*Fx_hat + ky*Fy_hat)
    div_hat = 1j * (KX * Fx_hat + KY * Fy_hat)

    # avoid division by zero at k=0
    phi_hat = _np.zeros_like(div_hat)
    mask = K2 != 0
    phi_hat[mask] = -div_hat[mask] / K2[mask]

    # irrotational component = grad(phi) in Fourier space: i*k * phi_hat
    Fi_x_hat = 1j * KX * phi_hat
    Fi_y_hat = 1j * KY * phi_hat

    Fi_x = _np.fft.ifft2(Fi_x_hat).real
    Fi_y = _np.fft.ifft2(Fi_y_hat).real

    Fi = _np.stack((Fi_x, Fi_y), axis=-1)
    Fs = F - Fi
    return Fi, Fs


def helmholtz_decompose_3d(
    F: _np.ndarray, dx: float = 1.0, dy: float = 1.0, dz: float = 1.0
) -> Tuple[_np.ndarray, _np.ndarray, _np.ndarray]:
    """Decompose a 3D vector field F(x,y,z) into grad(phi) (irrotational)
    and a divergence-free component via FFT Poisson solves (periodic BCs).

    Parameters
    - F: array of shape (nz, ny, nx, 3) representing (Fx, Fy, Fz) on a regular grid
    - dx, dy, dz: grid spacings

    Returns (Fi, Fs, phi) where Fi is curl-free (grad phi), Fs is divergence-free,
    and phi is the scalar potential on the grid.
    """
    if _np is None:
        raise RuntimeError("NumPy is required for helmholtz_decompose_3d")

    if F.ndim != 4 or F.shape[3] != 3:
        raise ValueError("F must be an array of shape (nz, ny, nx, 3)")

    nz, ny, nx, _ = F.shape
    Fx = F[..., 0]
    Fy = F[..., 1]
    Fz = F[..., 2]

    # Fourier transforms
    Fx_hat = _np.fft.fftn(Fx)
    Fy_hat = _np.fft.fftn(Fy)
    Fz_hat = _np.fft.fftn(Fz)

    kx = _fft_wave_numbers(nx, dx)
    ky = _fft_wave_numbers(ny, dy)
    kz = _fft_wave_numbers(nz, dz)

    # build spectral grids with axis order (z, y, x)
    KZ, KY, KX = _np.meshgrid(kz, ky, kx, indexing="ij")
    K2 = KX**2 + KY**2 + KZ**2

    # divergence in Fourier space: i*(kx*Fx_hat + ky*Fy_hat + kz*Fz_hat)
    div_hat = 1j * (KX * Fx_hat + KY * Fy_hat + KZ * Fz_hat)

    # solve Poisson: laplacian(phi) = div(F)  ->  phi_hat = -div_hat / k^2
    phi_hat = _np.zeros_like(div_hat)
    mask = K2 != 0
    phi_hat[mask] = -div_hat[mask] / K2[mask]

    # irrotational component = grad(phi) in spectral space: i*k * phi_hat
    Fi_x_hat = 1j * KX * phi_hat
    Fi_y_hat = 1j * KY * phi_hat
    Fi_z_hat = 1j * KZ * phi_hat

    Fi_x = _np.fft.ifftn(Fi_x_hat).real
    Fi_y = _np.fft.ifftn(Fi_y_hat).real
    Fi_z = _np.fft.ifftn(Fi_z_hat).real

    Fi = _np.stack((Fi_x, Fi_y, Fi_z), axis=-1)
    Fs = F - Fi
    phi = _np.fft.ifftn(phi_hat).real

    return Fi, Fs, phi


__all__ = ["helmholtz_decompose_2d", "helmholtz_decompose_3d"]
