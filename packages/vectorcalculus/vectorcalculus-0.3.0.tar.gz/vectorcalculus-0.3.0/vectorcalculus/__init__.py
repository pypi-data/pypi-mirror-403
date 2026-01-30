"""Vector Calculus — simple Python module.

Expose `Vector` and numerical vector-calculus operators.
"""

from .decompositions import helmholtz_decompose_2d, helmholtz_decompose_3d
from .grid import (curl_on_grid, divergence_on_grid, gradient_on_grid, mesh,
                   points_array)
from .integrals import (divergence_verifier_box, line_integral,
                        stokes_verifier, surface_integral)
from .interactive import quiver_plotly, surface_plotly
from .operations import curl_np  # grid dispatch helpers
from .operations import (curl, curl_grid, directional_derivative, divergence,
                         divergence_grid, divergence_np, gradient,
                         gradient_grid, gradient_np, hessian, hessian_np,
                         jacobian, jacobian_np, laplacian, laplacian_np,
                         vector_laplacian, vector_laplacian_np)
from .perf import numba_helpers
from .symbolic import (sympy_curl, sympy_divergence, sympy_gradient,
                       sympy_scalar_potential, sympy_vector_potential)
from .vector import Vector
from .visualization import (plot_streamlines_2d, plot_surface_parametric,
                            plot_vector_field_2d)

__all__ = [
    "Vector",
    "gradient",
    "divergence",
    "curl",
    "laplacian",
    "gradient_grid",
    "divergence_grid",
    "curl_grid",
    "gradient_np",
    "divergence_np",
    "curl_np",
    "laplacian_np",
    "mesh",
    "points_array",
    "gradient_on_grid",
    "divergence_on_grid",
    "curl_on_grid",
    "line_integral",
    "surface_integral",
    "stokes_verifier",
    "divergence_verifier_box",
    "sympy_gradient",
    "sympy_divergence",
    "sympy_curl",
    "sympy_scalar_potential",
    "sympy_vector_potential",
    "plot_vector_field_2d",
    "plot_streamlines_2d",
    "plot_surface_parametric",
    "quiver_plotly",
    "surface_plotly",
    "helmholtz_decompose_2d",
    "helmholtz_decompose_3d",
    "numba_helpers",
]
