import math


from vectorcalculus import line_integral, surface_integral


def test_line_integral_circle_scalar():
    # Circle of radius 1: r(t) = (cos t, sin t), t in [0,2pi]
    r = lambda t: (math.cos(t), math.sin(t))
    f = lambda p: 1.0
    I = line_integral(f, r, 0.0, 2 * math.pi, num=2000, vector_field=False)
    assert abs(I - 2 * math.pi) < 1e-3


def test_line_integral_circle_vector():
    # Vector field F = (-y, x), along unit circle: integral should be 2pi
    r = lambda t: (math.cos(t), math.sin(t))
    F = lambda p: (-p[1], p[0])
    I = line_integral(F, r, 0.0, 2 * math.pi, num=2000, vector_field=True)
    assert abs(I - 2 * math.pi) < 1e-3


def test_surface_integral_plane_square():
    # Parametrize square in z=0 plane: r(u,v) = (u,v,0), u,v in [-1,1]
    param = lambda u, v: (u, v, 0.0)
    f = lambda p: 1.0
    area = surface_integral(
        param, f, -1.0, 1.0, -1.0, 1.0, mu=80, mv=80, vector_field=False
    )
    assert abs(area - 4.0) < 1e-3
