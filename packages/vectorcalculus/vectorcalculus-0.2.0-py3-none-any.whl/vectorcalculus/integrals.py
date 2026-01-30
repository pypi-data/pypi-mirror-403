from typing import Callable, Sequence, Optional, Tuple, Any

try:
    import numpy as _np
except Exception:
    _np = None  # type: ignore


from . import operations as _ops


def _as_array(x):
    return _np.asarray(x) if _np is not None else x


def line_integral(field: Callable[[Sequence[float]], Any],
                  r: Callable[[float], Sequence[float]],
                  t0: float, t1: float,
                  num: int = 2000,
                  vector_field: bool = False) -> float:
    """Numerically compute a line integral along parametric curve r(t).

    If `vector_field` is False, `field` should be a scalar field f(point)
    and the integral computed is ∫ f(r(t)) |r'(t)| dt (scalar line integral).

    If `vector_field` is True, `field` should be a vector field F(point)
    and the integral computed is ∫ F(r(t)) · r'(t) dt (work integral).
    """
    if _np is None:
        # pure-Python trapezoid
        ts = [t0 + (t1 - t0) * i / (num - 1) for i in range(num)]
        pts = [tuple(r(t)) for t in ts]
        # compute dr segments
        total = 0.0
        for i in range(num - 1):
            p0 = pts[i]
            p1 = pts[i + 1]
            seg = tuple(b - a for a, b in zip(p0, p1))
            seg_len = sum(s * s for s in seg) ** 0.5
            if vector_field:
                F0 = field(p0)
                F1 = field(p1)
                # average F on segment
                Fav = tuple((a + b) / 2.0 for a, b in zip(F0, F1))
                total += sum(f * ds for f, ds in zip(Fav, seg))
            else:
                f0 = float(field(p0))
                f1 = float(field(p1))
                total += 0.5 * (f0 + f1) * seg_len
        return float(total)

    # NumPy path
    t = _np.linspace(t0, t1, num=num)
    pts = _np.asarray([_np.asarray(r(tt), dtype=float) for tt in t])
    dr = pts[1:] - pts[:-1]
    if vector_field:
        F0 = _np.asarray([_np.asarray(field(tuple(p)), dtype=float) for p in pts[:-1]])
        F1 = _np.asarray([_np.asarray(field(tuple(p)), dtype=float) for p in pts[1:]])
        Fav = 0.5 * (F0 + F1)
        # dot Fav with dr and sum
        return float(_np.sum(_np.einsum('ij,ij->i', Fav, dr)))
    else:
        f0 = _np.asarray([float(field(tuple(p))) for p in pts[:-1]])
        f1 = _np.asarray([float(field(tuple(p))) for p in pts[1:]])
        seg_len = _np.linalg.norm(dr, axis=1)
        return float(_np.sum(0.5 * (f0 + f1) * seg_len))


def surface_integral(param: Callable[[float, float], Sequence[float]],
                     field: Callable[[Sequence[float]], Any],
                     u0: float, u1: float,
                     v0: float, v1: float,
                     mu: int = 200, mv: int = 200,
                     vector_field: bool = False) -> float:
    """Numerically compute a surface integral over parametric surface r(u,v).

    If `vector_field` is False, `field` should be scalar and the integral is
    ∫ f(r(u,v)) |r_u × r_v| du dv.

    If `vector_field` is True, `field` should be a vector field and the flux
    is ∫ F(r(u,v)) · (r_u × r_v) du dv.
    """
    if _np is None:
        # basic double loop
        us = [u0 + (u1 - u0) * i / (mu - 1) for i in range(mu)]
        vs = [v0 + (v1 - v0) * j / (mv - 1) for j in range(mv)]
        du = (u1 - u0) / (mu - 1)
        dv = (v1 - v0) / (mv - 1)
        total = 0.0
        for i, u in enumerate(us):
            for j, v in enumerate(vs):
                # finite differences for ru, rv
                up = min(mu - 1, i + 1)
                um = max(0, i - 1)
                vp = min(mv - 1, j + 1)
                vm = max(0, j - 1)
                ru = tuple((param(us[up], v)[k] - param(us[um], v)[k]) / (us[up] - us[um]) for k in range(len(param(u, v))))
                rv = tuple((param(u, vs[vp])[k] - param(u, vs[vm])[k]) / (vs[vp] - vs[vm]) for k in range(len(param(u, v))))
                # cross product
                nx = ru[1] * rv[2] - ru[2] * rv[1]
                ny = ru[2] * rv[0] - ru[0] * rv[2]
                nz = ru[0] * rv[1] - ru[1] * rv[0]
                weight = 1.0
                if i == 0 or i == mu - 1:
                    weight *= 0.5
                if j == 0 or j == mv - 1:
                    weight *= 0.5
                if vector_field:
                    F = field(param(u, v))
                    total += (F[0] * nx + F[1] * ny + F[2] * nz) * du * dv * weight
                else:
                    fval = float(field(param(u, v)))
                    total += fval * (nx * nx + ny * ny + nz * nz) ** 0.5 * du * dv * weight
        return float(total)

    # NumPy path
    us = _np.linspace(u0, u1, mu)
    vs = _np.linspace(v0, v1, mv)
    du = us[1] - us[0]
    dv = vs[1] - vs[0]
    U, V = _np.meshgrid(us, vs, indexing='xy')
    # Evaluate surface points
    pts = _np.empty((mv, mu, 3), dtype=float)
    for i in range(mv):
        for j in range(mu):
            pts[i, j, :] = _np.asarray(param(U[i, j], V[i, j]), dtype=float)

    # compute partials ru (axis=1 corresponds to u), rv (axis=0 corresponds to v)
    ru = (_np.roll(pts, -1, axis=1) - _np.roll(pts, 1, axis=1)) / (2 * du)
    rv = (_np.roll(pts, -1, axis=0) - _np.roll(pts, 1, axis=0)) / (2 * dv)
    # one-sided differences on boundaries
    ru[:, 0, :] = (pts[:, 1, :] - pts[:, 0, :]) / du
    ru[:, -1, :] = (pts[:, -1, :] - pts[:, -2, :]) / du
    rv[0, :, :] = (pts[1, :, :] - pts[0, :, :]) / dv
    rv[-1, :, :] = (pts[-1, :, :] - pts[-2, :, :]) / dv

    normal = _np.cross(ru, rv)
    if vector_field:
        # evaluate vector field at each point
        F = _np.empty_like(normal)
        for i in range(mv):
            for j in range(mu):
                F[i, j, :] = _np.asarray(field(tuple(pts[i, j, :])), dtype=float)
        integrand = _np.einsum('ijk,ijk->ij', F, normal)
    else:
        fvals = _np.empty((mv, mu), dtype=float)
        for i in range(mv):
            for j in range(mu):
                fvals[i, j] = float(field(tuple(pts[i, j, :])))
        integrand = fvals * _np.linalg.norm(normal, axis=2)

    # apply trapezoidal weights for better accuracy on uniform grid
    w = _np.ones_like(integrand)
    w[0, :] *= 0.5
    w[-1, :] *= 0.5
    w[:, 0] *= 0.5
    w[:, -1] *= 0.5

    return float(_np.sum(integrand * w) * du * dv)


def stokes_verifier(vector_field: Callable[[Sequence[float]], Sequence[float]],
                    boundary_r: Callable[[float], Sequence[float]],
                    boundary_t0: float,
                    boundary_t1: float,
                    surface_param: Callable[[float, float], Sequence[float]],
                    u0: float,
                    u1: float,
                    v0: float,
                    v1: float,
                    line_num: int = 2000,
                    mu: int = 200, mv: int = 200) -> dict:
    """Numerically verify Stokes' theorem for a surface with boundary.

    Returns a dict with `circulation`, `surface_integral`, and `difference`.
    """
    circ = line_integral(vector_field, boundary_r, boundary_t0, boundary_t1, num=line_num, vector_field=True)

    def curl_at_point(p: Sequence[float]) -> Sequence[float]:
        c = _ops.curl(vector_field, p)
        # ensure a plain sequence of floats (Vector -> list)
        try:
            return tuple(c.to_list())
        except Exception:
            return tuple(c)

    surf = surface_integral(surface_param, curl_at_point, u0, u1, v0, v1, mu=mu, mv=mv, vector_field=True)

    return {"circulation": float(circ), "surface_integral": float(surf), "difference": float(circ - surf)}


def divergence_verifier_box(vector_field: Callable[[Sequence[float]], Sequence[float]],
                           x0: float, x1: float,
                           y0: float, y1: float,
                           z0: float, z1: float,
                           nx: int = 20, ny: int = 20, nz: int = 20) -> dict:
    """Numerically verify the divergence theorem on an axis-aligned box.

    Returns dict with `flux`, `volume_integral`, and `difference`.
    """
    # Each face needs sampling resolution matching its parameter ranges.
    # Build faces with explicit parameter ranges and sampling sizes
    faces = [
        # x = x1 (out +x): u in [y0,y1], v in [z0,z1]
        (lambda u, v, x=x1: (x, u, v), (y0, y1), (z0, z1), ny, nz),
        # x = x0 (out -x): param(u,v)=(x0, v, u) with u in [z0,z1], v in [y0,y1]
        (lambda u, v, x=x0: (x, v, u), (z0, z1), (y0, y1), nz, ny),
        # y = y1 (out +y): param(u,v)=(v, y1, u) with u in [z0,z1], v in [x0,x1]
        (lambda u, v, y=y1: (v, y, u), (z0, z1), (x0, x1), nz, nx),
        # y = y0 (out -y): param(u,v)=(u, y0, v) with u in [x0,x1], v in [z0,z1]
        (lambda u, v, y=y0: (u, y, v), (x0, x1), (z0, z1), nx, nz),
        # z = z1 (out +z): param(u,v)=(u, v, z1) with u in [x0,x1], v in [y0,y1]
        (lambda u, v, z=z1: (u, v, z), (x0, x1), (y0, y1), nx, ny),
        # z = z0 (out -z): param(u,v)=(v, u, z0) with u in [y0,y1], v in [x0,x1]
        (lambda u, v, z=z0: (v, u, z), (y0, y1), (x0, x1), ny, nx),
    ]

    flux = 0.0
    for param_func, (ua, ub), (va, vb), mu_face, mv_face in faces:
        flux += surface_integral(param_func, vector_field, ua, ub, va, vb, mu=mu_face, mv=mv_face, vector_field=True)

    xs = [x0 + (x1 - x0) * (i + 0.5) / nx for i in range(nx)]
    ys = [y0 + (y1 - y0) * (j + 0.5) / ny for j in range(ny)]
    zs = [z0 + (z1 - z0) * (k + 0.5) / nz for k in range(nz)]
    vol = 0.0
    dv = (x1 - x0) / nx * (y1 - y0) / ny * (z1 - z0) / nz
    for xi in xs:
        for yj in ys:
            for zk in zs:
                p = (xi, yj, zk)
                div_val = _ops.divergence(vector_field, p)
                vol += float(div_val) * dv

    return {"flux": float(flux), "volume_integral": float(vol), "difference": float(flux - vol)}
