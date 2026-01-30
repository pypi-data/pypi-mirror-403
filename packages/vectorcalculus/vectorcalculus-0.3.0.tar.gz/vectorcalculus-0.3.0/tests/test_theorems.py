import math

from vectorcalculus import divergence_verifier_box, stokes_verifier


def test_stokes_unit_disk():
    # F = (-y, x, 0), curl = (0,0,2)
    def F(p):
        x, y, z = p
        return (-y, x, 0)

    # boundary: unit circle in xy-plane
    def boundary(t):
        return (math.cos(t), math.sin(t), 0.0)

    # surface param: polar coords (r,theta) -> (r*cos, r*sin, 0)
    def surf(u, v):
        return (u * math.cos(v), u * math.sin(v), 0.0)

    res = stokes_verifier(
        F,
        boundary,
        0.0,
        2 * math.pi,
        surf,
        0.0,
        1.0,
        0.0,
        2 * math.pi,
        line_num=2000,
        mu=200,
        mv=200,
    )
    assert abs(res["difference"]) < 1e-2
    assert abs(res["circulation"] - 2 * math.pi) < 1e-2
    assert abs(res["surface_integral"] - 2 * math.pi) < 1e-2


def test_divergence_box_unit_cube():
    # F = (x, y, z), div = 3
    def F(p):
        x, y, z = p
        return (x, y, z)

    res = divergence_verifier_box(F, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, nx=40, ny=40, nz=40)
    assert abs(res["difference"]) < 1e-2
    assert abs(res["volume_integral"] - 3.0) < 1e-2
    assert abs(res["flux"] - 3.0) < 1e-2
