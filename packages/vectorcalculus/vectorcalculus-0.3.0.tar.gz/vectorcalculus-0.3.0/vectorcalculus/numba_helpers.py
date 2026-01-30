"""Optional Numba-accelerated finite-difference helpers for array-backed fields.

These functions operate on NumPy arrays and provide central-difference
derivatives with periodic boundary handling. They are JIT-compiled when
Numba is available; otherwise the module exposes a flag `NUMBA_AVAILABLE`.
"""


import numpy as np

try:
    from numba import njit, prange

    NUMBA_AVAILABLE = True
except Exception:
    NUMBA_AVAILABLE = False


if NUMBA_AVAILABLE:

    @njit(parallel=True)
    def gradient_3d(field: np.ndarray, dx: float, dy: float, dz: float):
        nz, ny, nx = field.shape
        gx = np.zeros_like(field)
        gy = np.zeros_like(field)
        gz = np.zeros_like(field)
        for k in prange(nz):
            kf = (k + 1) % nz
            kb = (k - 1) % nz
            for j in range(ny):
                jf = (j + 1) % ny
                jb = (j - 1) % ny
                for i in range(nx):
                    if_ = (i + 1) % nx
                    ib = (i - 1) % nx
                    gx[k, j, i] = (field[k, j, if_] - field[k, j, ib]) / (2.0 * dx)
                    gy[k, j, i] = (field[k, jf, i] - field[k, jb, i]) / (2.0 * dy)
                    gz[k, j, i] = (field[kf, j, i] - field[kb, j, i]) / (2.0 * dz)
        return gx, gy, gz

    @njit(parallel=True)
    def divergence_3d(
        Fx: np.ndarray, Fy: np.ndarray, Fz: np.ndarray, dx: float, dy: float, dz: float
    ):
        nz, ny, nx = Fx.shape
        out = np.zeros_like(Fx)
        for k in prange(nz):
            kf = (k + 1) % nz
            kb = (k - 1) % nz
            for j in range(ny):
                jf = (j + 1) % ny
                jb = (j - 1) % ny
                for i in range(nx):
                    if_ = (i + 1) % nx
                    ib = (i - 1) % nx
                    dFx = (Fx[k, j, if_] - Fx[k, j, ib]) / (2.0 * dx)
                    dFy = (Fy[k, jf, i] - Fy[k, jb, i]) / (2.0 * dy)
                    dFz = (Fz[kf, j, i] - Fz[kb, j, i]) / (2.0 * dz)
                    out[k, j, i] = dFx + dFy + dFz
        return out

    @njit(parallel=True)
    def curl_3d(
        Fx: np.ndarray, Fy: np.ndarray, Fz: np.ndarray, dx: float, dy: float, dz: float
    ):
        nz, ny, nx = Fx.shape
        cx = np.zeros_like(Fx)
        cy = np.zeros_like(Fx)
        cz = np.zeros_like(Fx)
        for k in prange(nz):
            kf = (k + 1) % nz
            kb = (k - 1) % nz
            for j in range(ny):
                jf = (j + 1) % ny
                jb = (j - 1) % ny
                for i in range(nx):
                    if_ = (i + 1) % nx
                    ib = (i - 1) % nx
                    dFz_dy = (Fz[k, jf, i] - Fz[k, jb, i]) / (2.0 * dy)
                    dFy_dz = (Fy[kf, j, i] - Fy[kb, j, i]) / (2.0 * dz)
                    dFx_dz = (Fx[kf, j, i] - Fx[kb, j, i]) / (2.0 * dz)
                    dFz_dx = (Fz[k, j, if_] - Fz[k, j, ib]) / (2.0 * dx)
                    dFy_dx = (Fy[k, j, if_] - Fy[k, j, ib]) / (2.0 * dx)
                    dFx_dy = (Fx[k, jf, i] - Fx[k, jb, i]) / (2.0 * dy)
                    cx[k, j, i] = dFz_dy - dFy_dz
                    cy[k, j, i] = dFx_dz - dFz_dx
                    cz[k, j, i] = dFy_dx - dFx_dy
        return cx, cy, cz

else:

    def gradient_3d(*args, **kwargs):
        raise RuntimeError("Numba is not available")

    def divergence_3d(*args, **kwargs):
        raise RuntimeError("Numba is not available")

    def curl_3d(*args, **kwargs):
        raise RuntimeError("Numba is not available")


__all__ = ["NUMBA_AVAILABLE", "gradient_3d", "divergence_3d", "curl_3d"]
