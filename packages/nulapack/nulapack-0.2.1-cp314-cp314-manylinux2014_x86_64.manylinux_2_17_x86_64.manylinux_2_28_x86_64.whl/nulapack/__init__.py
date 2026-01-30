from importlib.metadata import PackageNotFoundError, version

from .cholesky import cholesky
from .crout import crout
from .doolittle import doolittle
from .gauss_seidel import gauss_seidel
from .jacobi import jacobi
from .thomas import thomas


try:
    __version__ = version("nulapack")
except PackageNotFoundError:
    # package is not installed
    pass

__all__ = ["__version__", "cholesky", "crout", "doolittle", "gauss_seidel", "jacobi", "thomas"]
