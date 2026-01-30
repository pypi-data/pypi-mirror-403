import math
from vectorcalculus import Vector, gradient, divergence, curl


def test_vector_basic():
    v = Vector(1, 2, 2)
    assert v.norm() == math.sqrt(1 + 4 + 4)
    u = Vector(2, 0, 0)
    assert v.dot(u) == 2
    assert Vector(1, 0, 0).cross(Vector(0, 1, 0)).to_list() == [0.0, 0.0, 1.0]


def test_gradient():
    def f(p):
        x, y, z = p
        return x * y + z * z

    g = gradient(f, (1.3, -2.2, 0.5))
    # analytical grad = [y, x, 2z]
    assert abs(g.to_list()[0] - (-2.2)) < 1e-3
    assert abs(g.to_list()[1] - 1.3) < 1e-3
    assert abs(g.to_list()[2] - 1.0) < 1e-3


def test_divergence_and_curl():
    def F(p):
        x, y, z = p
        return [x * x, y * y, z * z]

    d = divergence(F, (0.5, -0.2, 1.3))
    # div = 2x + 2y + 2z
    assert abs(d - (2 * 0.5 + 2 * -0.2 + 2 * 1.3)) < 1e-3

    def G(p):
        x, y, z = p
        return [-y, x, 0]

    c = curl(G, (0.1, 0.2, 0.3))
    # curl of [-y, x, 0] is [0, 0, 2]
    assert abs(c.to_list()[0]) < 1e-3
    assert abs(c.to_list()[1]) < 1e-3
    assert abs(c.to_list()[2] - 2.0) < 1e-2
