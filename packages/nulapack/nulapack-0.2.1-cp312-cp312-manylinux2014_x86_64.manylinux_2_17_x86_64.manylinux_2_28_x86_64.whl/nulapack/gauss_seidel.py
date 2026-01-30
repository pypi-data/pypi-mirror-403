import _nulapack
import numpy as np


def gauss_seidel(a, b, max_iter=1000, tol=1e-8, omega=1.0):
    """
    Solve the linear system ax = b using the Gauss-Seidel method.

    Parameters
    ----------
    a : ndarray
        Coefficient matrix (n x n)
    b : ndarray
        Right-hand side vector (n,)
    max_iter : int, optional
        Maximum number of iterations
    tol : float, optional
        Convergence tolerance
    omega : float, optional
        Relaxation factor

    Returns
    -------
    x : ndarray
        Solution vector
    status : int
        0 if converged, non-zero otherwise
    """
    a = np.ascontiguousarray(a)
    b = np.asfortranarray(b)
    n = a.shape[0]

    x = np.zeros_like(b)

    a_flat = a.ravel()

    if np.issubdtype(a.dtype, np.floating):
        if a.dtype == np.float32:
            status = _nulapack.sgegssv(a_flat, b, x, max_iter, tol, omega, 0, n)
        else:  # float64
            status = _nulapack.dgegssv(a_flat, b, x, max_iter, tol, omega, 0, n)
    elif np.issubdtype(a.dtype, np.complexfloating):
        if a.dtype == np.complex64:
            status = _nulapack.cgegssv(a_flat, b, x, max_iter, tol, omega, 0, n)
        else:  # complex128
            status = _nulapack.zgegssv(a_flat, b, x, max_iter, tol, omega, 0, n)
    else:
        raise TypeError(f"Unsupported array dtype: {a.dtype}")

    return x, int(status) if status is not None else 0
