
from vectorcalculus import (directional_derivative, hessian, jacobian,
                            vector_laplacian)


def test_directional_derivative():
    def f(p):
        x, y, z = p
        return x * x + y * y + z * z

    # gradient at (1,0,0) = (2,0,0); directional derivative along x is 2
    val = directional_derivative(f, (1.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    assert abs(val - 2.0) < 1e-6


def test_jacobian_identity():
    def F(p):
        x, y, z = p
        return (x, y, z)

    J = jacobian(F, (0.5, 0.2, -0.1), h=1e-6)
    # should be identity
    assert all(
        abs(J[i][j] - (1.0 if i == j else 0.0)) < 1e-3
        for i in range(3)
        for j in range(3)
    )


def test_hessian_quadratic():
    def f(p):
        x, y, z = p
        return x * x + y * y + z * z

    H = hessian(f, (0.1, -0.2, 0.3), h=1e-4)
    # Hessian is 2*I
    assert all(
        abs(H[i][j] - (2.0 if i == j else 0.0)) < 1e-2
        for i in range(3)
        for j in range(3)
    )


def test_vector_laplacian_zero():
    def F(p):
        x, y, z = p
        return (x, y, z)

    L = vector_laplacian(F, (0.0, 0.0, 0.0), h=1e-4)
    assert all(abs(c) < 1e-6 for c in L)
