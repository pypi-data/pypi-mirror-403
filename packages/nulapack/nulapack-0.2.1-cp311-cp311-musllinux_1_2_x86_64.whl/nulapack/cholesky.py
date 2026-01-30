import _nulapack
import numpy as np


def cholesky(a: np.ndarray):
    """
    Compute the Cholesky factorization of a symmetric/Hermitian
    positive-definite matrix A using NULAPACK.

    Parameters
    ----------
    a : ndarray
        Coefficient matrix (n x n) stored as a full matrix. Real matrices
        should be symmetric, complex matrices should be Hermitian and
        positive-definite.

    Returns
    -------
    L : ndarray
        Lower-triangular matrix from the factorization (A = L * L^T or
        A = L * L^H).
    info : int
        0 if success, >0 if the matrix is not positive-definite.
    """
    a = np.ascontiguousarray(a)
    n = a.shape[0]
    lda = n

    a_flat = a.ravel(order="C")
    l_flat = np.zeros_like(a_flat)
    info = np.zeros(1, dtype=np.int32)

    if np.issubdtype(a.dtype, np.floating):
        if a.dtype == np.float32:
            _nulapack.spoctrf(n, a_flat, l_flat, lda, info)
        else:  # float64
            _nulapack.dpoctrf(n, a_flat, l_flat, lda, info)
    elif np.issubdtype(a.dtype, np.complexfloating):
        if a.dtype == np.complex64:
            _nulapack.cpoctrf(n, a_flat, l_flat, lda, info)
        else:  # complex128
            _nulapack.zpoctrf(n, a_flat, l_flat, lda, info)
    else:
        raise TypeError(f"Unsupported array dtype: {a.dtype}")

    return np.tril(l_flat.reshape(n, n, order="C")), int(info[0])
