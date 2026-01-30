"""Performance helpers subpackage.

Place optional accelerated implementations (Numba/CuPy) here.
"""

from . import numba_helpers

__all__ = ["numba_helpers"]
