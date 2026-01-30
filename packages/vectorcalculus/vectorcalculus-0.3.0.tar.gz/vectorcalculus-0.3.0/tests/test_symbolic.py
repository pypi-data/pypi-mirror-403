import pytest

try:
    import sympy as sp
except Exception:
    sp = None

from vectorcalculus import (
    sympy_gradient,
    sympy_divergence,
    sympy_curl,
    sympy_scalar_potential,
    sympy_vector_potential,
)


@pytest.mark.skipif(sp is None, reason="sympy not installed")
def test_symbolic_gradient_and_divergence():
    x, y, z = sp.symbols("x y z")
    f = x * y ** 2
    g = sympy_gradient(f, [x, y, z])
    assert list(g)[:2] == [y ** 2, 2 * x * y]

    vec = [x, y, z]
    div = sympy_divergence(vec, [x, y, z])
    assert sp.simplify(div - 3) == 0


@pytest.mark.skipif(sp is None, reason="sympy not installed")
def test_symbolic_curl_and_potentials():
    x, y, z = sp.symbols("x y z")
    # field that is curl of A = (0,0,x*y)
    A = sp.Matrix([0, 0, x * y])
    F = sp.Matrix([sp.diff(A[2], y) - sp.diff(A[1], z),
                   sp.diff(A[0], z) - sp.diff(A[2], x),
                   sp.diff(A[1], x) - sp.diff(A[0], y)])
    # verify curl helper
    curlF = sympy_curl(F, [x, y, z])
    assert all(sp.simplify(cf) == sp.simplify(fr) for cf, fr in zip(curlF, sp.Matrix([0,0,0])))

    # scalar potential for grad(phi) = [2*x, 2*y]
    phi = 2 * x * y
    grad_phi = [sp.diff(phi, v) for v in (x, y, z)]
    phi_found = sympy_scalar_potential(grad_phi, (x, y, z))
    assert phi_found is not None
    # gradient of returned potential should match (up to constant)
    g = [sp.diff(phi_found, v) for v in (x, y, z)]
    assert all(sp.simplify(a - b) == 0 for a, b in zip(g, grad_phi))

    # vector potential: try on F which is divergence-free
    # create a known curl field: curl( [0,0,x*y] ) above gave F
    A_found = sympy_vector_potential(F, (x, y, z))
    assert A_found is not None
    # verify curl(A_found) == F
    curlA = sp.Matrix([sp.diff(A_found[2], y) - sp.diff(A_found[1], z),
                       sp.diff(A_found[0], z) - sp.diff(A_found[2], x),
                       sp.diff(A_found[1], x) - sp.diff(A_found[0], y)])
    assert all(sp.simplify(c - f) == 0 for c, f in zip(curlA, F))
