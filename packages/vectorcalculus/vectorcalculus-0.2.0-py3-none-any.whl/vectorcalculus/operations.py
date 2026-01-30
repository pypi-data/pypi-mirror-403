"""Numerical vector calculus operators using finite differences.

Functions expect points as sequences (x, y) or (x, y, z).
Scalar fields: callable(point) -> float
Vector fields: callable(point) -> sequence of floats
"""
from typing import Sequence, Callable, Tuple, Any
from vectorcalculus.vector import Vector

_np: Any = None
try:
    import numpy as _np
except Exception:
    _np = None


def _ensure_point(p: Sequence[float]) -> Tuple[float, ...]:
    return tuple(float(x) for x in p)


def gradient(scalar_field: Callable[[Sequence[float]], float], point: Sequence[float], h: float = 1e-6) -> Vector:
    """Central-difference gradient returning a `Vector` for Python scalars."""
    p = _ensure_point(point)
    n = len(p)
    grad = []
    for i in range(n):
        forward = list(p)
        backward = list(p)
        forward[i] += h
        backward[i] -= h
        f1 = scalar_field(tuple(forward))
        f2 = scalar_field(tuple(backward))
        grad.append((f1 - f2) / (2 * h))
    return Vector(grad)


def divergence(vector_field: Callable[[Sequence[float]], Sequence[float]], point: Sequence[float], h: float = 1e-6) -> float:
    p = _ensure_point(point)
    n = len(p)
    div = 0.0
    for i in range(n):
        forward = list(p)
        backward = list(p)
        forward[i] += h
        backward[i] -= h
        f1 = vector_field(tuple(forward))[i]
        f2 = vector_field(tuple(backward))[i]
        div += (f1 - f2) / (2 * h)
    return float(div)


def curl(vector_field: Callable[[Sequence[float]], Sequence[float]], point: Sequence[float], h: float = 1e-6) -> Vector:
    p = _ensure_point(point)
    if len(p) != 3:
        raise TypeError("Curl is defined only in 3D for this implementation")
    def partial(component_index, var_index, sign):
        q = list(p)
        q[var_index] += sign * h
        return vector_field(tuple(q))[component_index]

    dFz_dy = (partial(2, 1, 1) - partial(2, 1, -1)) / (2 * h)
    dFy_dz = (partial(1, 2, 1) - partial(1, 2, -1)) / (2 * h)
    dFx_dz = (partial(0, 2, 1) - partial(0, 2, -1)) / (2 * h)
    dFz_dx = (partial(2, 0, 1) - partial(2, 0, -1)) / (2 * h)
    dFy_dx = (partial(1, 0, 1) - partial(1, 0, -1)) / (2 * h)
    dFx_dy = (partial(0, 1, 1) - partial(0, 1, -1)) / (2 * h)

    cx = dFz_dy - dFy_dz
    cy = dFx_dz - dFz_dx
    cz = dFy_dx - dFx_dy

    return Vector(cx, cy, cz)


def laplacian(scalar_field: Callable[[Sequence[float]], float], point: Sequence[float], h: float = 1e-4) -> float:
    p = _ensure_point(point)
    n = len(p)
    lap = 0.0
    base = scalar_field(tuple(p))
    for i in range(n):
        qf = list(p)
        qb = list(p)
        qf[i] += h
        qb[i] -= h
        lap += (scalar_field(tuple(qf)) - 2 * base + scalar_field(tuple(qb))) / (h * h)
    return float(lap)


def directional_derivative(scalar_field: Callable[[Sequence[float]], float],
                           point: Sequence[float],
                           direction: Sequence[float],
                           h: float = 1e-6) -> float:
    """Directional derivative D_u f at point. If `direction` is not unit,
    it will be normalized to compute the unit-directional derivative.
    """
    # compute gradient (returns Vector)
    grad_v = gradient(scalar_field, point, h=h)
    # normalize direction
    dir_vec = Vector(direction)
    dir_unit = dir_vec.normalize()
    return float(grad_v.dot(dir_unit))


def jacobian(vector_field: Callable[[Sequence[float]], Sequence[float]],
             point: Sequence[float], h: float = 1e-6) -> list:
    """Return Jacobian matrix (m x n) for vector_field: R^n -> R^m as list of rows.
    Each row corresponds to partials of one component of the vector field.
    """
    p = _ensure_point(point)
    n = len(p)
    F0 = vector_field(tuple(p))
    m = len(F0)
    J = [[0.0] * n for _ in range(m)]
    for j in range(n):
        forward = list(p)
        backward = list(p)
        forward[j] += h
        backward[j] -= h
        Ff = vector_field(tuple(forward))
        Fb = vector_field(tuple(backward))
        for i in range(m):
            J[i][j] = (Ff[i] - Fb[i]) / (2 * h)
    return J


def hessian(scalar_field: Callable[[Sequence[float]], float], point: Sequence[float], h: float = 1e-4) -> list:
    """Return Hessian matrix (n x n) of second partial derivatives for scalar_field at point."""
    p = _ensure_point(point)
    n = len(p)
    H = [[0.0] * n for _ in range(n)]
    base = scalar_field(tuple(p))
    for i in range(n):
        for j in range(n):
            if i == j:
                qf = list(p)
                qb = list(p)
                qf[i] += h
                qb[i] -= h
                H[i][i] = (scalar_field(tuple(qf)) - 2 * base + scalar_field(tuple(qb))) / (h * h)
            else:
                # mixed partial: f(xi+h, xj+h) - f(xi+h, xj-h) - f(xi-h, xj+h) + f(xi-h, xj-h) / (4 h^2)
                a = list(p)
                b = list(p)
                c = list(p)
                d = list(p)
                a[i] += h; a[j] += h
                b[i] += h; b[j] -= h
                c[i] -= h; c[j] += h
                d[i] -= h; d[j] -= h
                H[i][j] = (scalar_field(tuple(a)) - scalar_field(tuple(b)) - scalar_field(tuple(c)) + scalar_field(tuple(d))) / (4 * h * h)
    return H


def vector_laplacian(vector_field: Callable[[Sequence[float]], Sequence[float]], point: Sequence[float], h: float = 1e-4) -> Vector:
    """Apply scalar Laplacian to each component of a vector field and return a `Vector` of results."""
    p = _ensure_point(point)
    F0 = vector_field(tuple(p))
    m = len(F0)
    comps = []
    for i in range(m):
        def comp_func(q):
            return vector_field(q)[i]
        comps.append(laplacian(comp_func, p, h=h))
    return Vector(comps)


# --- NumPy-accelerated versions (optional) ---
def gradient_np(scalar_field: Callable[..., Any], point: Sequence[float], h: float = 1e-6) -> Any:
    """Vectorized gradient using NumPy. Returns a NumPy array.

    The `scalar_field` must accept and return NumPy arrays when given NumPy inputs.
    """
    if _np is None:
        raise RuntimeError("NumPy is required for gradient_np")
    p = _np.asarray(point, dtype=float)
    n = p.size
    out = _np.empty(n, dtype=float)
    for i in range(n):
        e = _np.zeros_like(p)
        e[i] = h
        f1 = scalar_field(p + e)
        f2 = scalar_field(p - e)
        out[i] = (f1 - f2) / (2 * h)
    return out


def divergence_np(vector_field: Callable[..., Any], point: Sequence[float], h: float = 1e-6) -> float:
    if _np is None:
        raise RuntimeError("NumPy is required for divergence_np")
    p = _np.asarray(point, dtype=float)
    n = p.size
    div = 0.0
    for i in range(n):
        e = _np.zeros_like(p)
        e[i] = h
        f1 = vector_field(p + e)[i]
        f2 = vector_field(p - e)[i]
        div += (f1 - f2) / (2 * h)
    return float(div)


def curl_np(vector_field: Callable[..., Any], point: Sequence[float], h: float = 1e-6) -> Any:
    if _np is None:
        raise RuntimeError("NumPy is required for curl_np")
    p = _np.asarray(point, dtype=float)
    if p.size != 3:
        raise TypeError("curl_np requires 3D points")
    def partial(component_index: int, var_index: int, sign: int):
        e = _np.zeros_like(p)
        e[var_index] = sign * h
        return vector_field(p + e)[component_index]

    dFz_dy = (partial(2, 1, 1) - partial(2, 1, -1)) / (2 * h)
    dFy_dz = (partial(1, 2, 1) - partial(1, 2, -1)) / (2 * h)
    dFx_dz = (partial(0, 2, 1) - partial(0, 2, -1)) / (2 * h)
    dFz_dx = (partial(2, 0, 1) - partial(2, 0, -1)) / (2 * h)
    dFy_dx = (partial(1, 0, 1) - partial(1, 0, -1)) / (2 * h)
    dFx_dy = (partial(0, 1, 1) - partial(0, 1, -1)) / (2 * h)

    cx = dFz_dy - dFy_dz
    cy = dFx_dz - dFz_dx
    cz = dFy_dx - dFx_dy
    return _np.array([cx, cy, cz], dtype=float)


def laplacian_np(scalar_field: Callable[..., Any], point: Sequence[float], h: float = 1e-4) -> float:
    if _np is None:
        raise RuntimeError("NumPy is required for laplacian_np")
    p = _np.asarray(point, dtype=float)
    n = p.size
    base = scalar_field(p)
    lap = 0.0
    for i in range(n):
        e = _np.zeros_like(p)
        e[i] = h
        lap += (scalar_field(p + e) - 2 * base + scalar_field(p - e)) / (h * h)
    return float(lap)


def jacobian_np(vector_field: Callable[..., Any], point: Sequence[float], h: float = 1e-6) -> Any:
    if _np is None:
        raise RuntimeError("NumPy is required for jacobian_np")
    p = _np.asarray(point, dtype=float)
    n = p.size
    F0 = vector_field(p)
    m = len(F0)
    J = _np.empty((m, n), dtype=float)
    for j in range(n):
        e = _np.zeros_like(p)
        e[j] = h
        Ff = vector_field(p + e)
        Fb = vector_field(p - e)
        for i in range(m):
            J[i, j] = (Ff[i] - Fb[i]) / (2 * h)
    return J


def hessian_np(scalar_field: Callable[..., Any], point: Sequence[float], h: float = 1e-4) -> Any:
    if _np is None:
        raise RuntimeError("NumPy is required for hessian_np")
    p = _np.asarray(point, dtype=float)
    n = p.size
    H = _np.empty((n, n), dtype=float)
    base = scalar_field(p)
    for i in range(n):
        for j in range(n):
            if i == j:
                e = _np.zeros_like(p); e[i] = h
                H[i, i] = (scalar_field(p + e) - 2 * base + scalar_field(p - e)) / (h * h)
            else:
                a = p.copy(); b = p.copy(); c = p.copy(); d = p.copy()
                a[i] += h; a[j] += h
                b[i] += h; b[j] -= h
                c[i] -= h; c[j] += h
                d[i] -= h; d[j] -= h
                H[i, j] = (scalar_field(a) - scalar_field(b) - scalar_field(c) + scalar_field(d)) / (4 * h * h)
    return H


def vector_laplacian_np(vector_field: Callable[..., Any], point: Sequence[float], h: float = 1e-4) -> Any:
    if _np is None:
        raise RuntimeError("NumPy is required for vector_laplacian_np")
    p = _np.asarray(point, dtype=float)
    F0 = vector_field(p)
    m = len(F0)
    out = _np.empty(m, dtype=float)
    for i in range(m):
        def comp(q):
            return vector_field(q)[i]
        out[i] = laplacian_np(comp, p, h=h)
    return out
