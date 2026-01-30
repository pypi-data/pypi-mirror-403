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
)
from .grid import mesh, points_array, gradient_on_grid, divergence_on_grid, curl_on_grid

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
]
