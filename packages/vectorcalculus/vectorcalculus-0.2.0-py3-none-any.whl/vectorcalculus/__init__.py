"""Vector Calculus — simple Python module.

Expose `Vector` and numerical vector-calculus operators.
"""
from .vector import Vector
from .operations import (
	gradient,
	divergence,
	curl,
	laplacian,
	gradient_np,
	divergence_np,
	curl_np,
	laplacian_np,
    directional_derivative,
    jacobian,
    hessian,
    vector_laplacian,
    jacobian_np,
    hessian_np,
    vector_laplacian_np,
)
from .grid import mesh, points_array, gradient_on_grid, divergence_on_grid, curl_on_grid
from .integrals import line_integral, surface_integral
from .integrals import stokes_verifier, divergence_verifier_box
from .symbolic import sympy_gradient, sympy_divergence, sympy_curl, sympy_scalar_potential, sympy_vector_potential
from .visualization import plot_vector_field_2d, plot_streamlines_2d, plot_surface_parametric

__all__ = [
	"Vector",
	"gradient",
	"divergence",
	"curl",
	"laplacian",
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
]
