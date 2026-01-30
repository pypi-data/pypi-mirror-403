import _nulapack
import numpy as np


def crout(a: np.ndarray):
    """
    Compute the LU Crout decomposition of a general matrix A.

    Parameters
    ----------
    a : ndarray
        Coefficient matrix (n x n) stored as a full matrix.

    Returns
    -------
    L : ndarray
        Lower triangular matrix from the factorization.
    U : ndarray
        Upper triangular matrix from the factorization (with ones on diagonal).
    info : int
        0 if success, <0 if a zero diagonal in L was detected.
    """
    a = np.ascontiguousarray(a)
    n = a.shape[0]

    a_flat = a.ravel(order="C")
    l_flat = np.zeros_like(a_flat)
    u_flat = np.zeros_like(a_flat)
    info = np.zeros(1, dtype=np.int32)

    if np.issubdtype(a.dtype, np.floating):
        if a.dtype == np.float32:
            _nulapack.sgectrf(n, a_flat, l_flat, u_flat, info)
        else:  # float64
            _nulapack.dgectrf(n, a_flat, l_flat, u_flat, info)
    elif np.issubdtype(a.dtype, np.complexfloating):
        if a.dtype == np.complex64:
            _nulapack.cgectrf(n, a_flat, l_flat, u_flat, info)
        else:  # complex128
            _nulapack.zgectrf(n, a_flat, l_flat, u_flat, info)
    else:
        raise TypeError(f"Unsupported array dtype: {a.dtype}")

    return l_flat.reshape(n, n, order="C"), u_flat.reshape(n, n, order="C"), int(info[0])
