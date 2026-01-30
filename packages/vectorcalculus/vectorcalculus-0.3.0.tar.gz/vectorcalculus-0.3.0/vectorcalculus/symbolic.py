"""Symbolic vector-calculus helpers using SymPy.

This module provides small convenience wrappers to compute symbolic
gradient, divergence, curl, and attempt to find potentials.
SymPy is optional at runtime; these helpers will raise RuntimeError
if `sympy` is not installed.
"""

from typing import Optional, Sequence

try:
    import sympy as _sp
    from sympy import Matrix
except Exception:  # pragma: no cover - runtime import guard
    _sp = None  # type: ignore


def _require_sympy() -> None:
    if _sp is None:
        raise RuntimeError("SymPy is required for symbolic helpers; install sympy")


def sympy_gradient(expr, vars: Sequence) -> "Matrix":
    """Return the symbolic gradient (column Matrix) of *expr* with respect to *vars*.

    Example:
        x,y = sp.symbols('x y')
        sympy_gradient(x*y**2, [x,y]) -> Matrix([[y**2],[2*x*y]])
    """
    _require_sympy()
    return Matrix([_sp.diff(expr, v) for v in vars])


def sympy_divergence(vec: Sequence, vars: Sequence) -> _sp.Expr:
    """Return the symbolic divergence of a vector expression sequence.

    `vec` is a sequence of sympy expressions matching the order of `vars`.
    """
    _require_sympy()
    return _sp.simplify(sum(_sp.diff(c, v) for c, v in zip(vec, vars)))


def sympy_curl(vec3: Sequence, vars3: Sequence) -> "Matrix":
    """Return the symbolic curl of a 3D vector field as a 3x1 Matrix.

    Raises TypeError if inputs are not 3D.
    """
    _require_sympy()
    if len(vec3) != 3 or len(vars3) != 3:
        raise TypeError("sympy_curl requires 3-component vector and 3 variables")
    P, Q, R = vec3
    x, y, z = vars3
    cx = _sp.diff(R, y) - _sp.diff(Q, z)
    cy = _sp.diff(P, z) - _sp.diff(R, x)
    cz = _sp.diff(Q, x) - _sp.diff(P, y)
    return Matrix([cx, cy, cz])


def sympy_scalar_potential(vec: Sequence, vars: Sequence) -> Optional[_sp.Expr]:
    """Attempt to find a scalar potential phi such that grad(phi) == vec.

    Returns a SymPy expression for phi when successful, or ``None`` if
    the field is not conservative (inconsistent mixed partials).

    The method integrates components sequentially and checks consistency.
    Works for arbitrary dimension when an exact potential exists.
    """
    _require_sympy()
    n = len(vars)
    if len(vec) != n:
        raise TypeError("vector length must match variables length")

    # Start with integral of first component
    phi = _sp.integrate(vec[0], (vars[0],))
    # Add functions of remaining variables by integrating residuals
    for i in range(1, n):
        # residual = Fi - d/dxi(phi)
        residual = _sp.simplify(vec[i] - _sp.diff(phi, vars[i]))
        if residual == 0:
            continue
        # integrate residual w.r.t vars[i]
        add = _sp.integrate(residual, (vars[i],))
        phi = _sp.simplify(phi + add)

    # Verify
    grad_phi = Matrix([_sp.diff(phi, v) for v in vars])
    if all(_sp.simplify(g - v) == 0 for g, v in zip(grad_phi, vec)):
        return _sp.simplify(phi)
    return None


def sympy_vector_potential(vec3: Sequence, vars3: Sequence) -> Optional["Matrix"]:
    """Attempt to find a vector potential A such that curl(A) == vec3.

    This uses a simple constructive approach (choosing a convenient gauge)
    and works for many common closed fields. Returns a 3x1 Matrix or None
    if no simple potential is found.
    """
    _require_sympy()
    if len(vec3) != 3 or len(vars3) != 3:
        raise TypeError(
            "sympy_vector_potential requires 3-component vector and 3 variables"
        )
    P, Q, R = vec3
    x, y, z = vars3

    # Quick check: field must be divergence-free to have a global vector potential
    if _sp.simplify(_sp.diff(P, x) + _sp.diff(Q, y) + _sp.diff(R, z)) != 0:
        return None

    # Choose gauge A = (0, A_y(x,y,z), A_z(x,y,z)) and solve
    # From curl(A) = (dAz/dy - dAy/dz, dAx/dz - dAz/dx, dAy/dx - dAx/dy)
    # With Ax = 0 we get:
    # P = dAz/dy - dAy/dz
    # Q = - dAz/dx
    # R = dAy/dx
    Az = -_sp.integrate(Q, x)
    Ay = _sp.integrate(R, x)

    # There may be functions of (y,z) remaining in Az and Ay; add them by
    # integrating the P equation's residual.
    residual = _sp.simplify(P - (_sp.diff(Az, y) - _sp.diff(Ay, z)))
    if residual != 0:
        # try to absorb residual by adding a function h(y,z) to Az and g(y,z) to Ay
        # we add H(y,z) to Az: dH/dy contributes to dAz/dy
        H = _sp.integrate(residual, (y,))
        Az = _sp.simplify(Az + H)
        residual2 = _sp.simplify(P - (_sp.diff(Az, y) - _sp.diff(Ay, z)))
        if residual2 != 0:
            return None

    A = Matrix([0, _sp.simplify(Ay), _sp.simplify(Az)])
    # final verification
    curlA = Matrix(
        [
            _sp.diff(A[2], y) - _sp.diff(A[1], z),
            _sp.diff(A[0], z) - _sp.diff(A[2], x),
            _sp.diff(A[1], x) - _sp.diff(A[0], y),
        ]
    )
    if all(_sp.simplify(c - f) == 0 for c, f in zip(curlA, vec3)):
        return A
    return None
