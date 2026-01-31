import sys
import warnings

import pkg_resources

from platon.main import (
    Web3  # noqa: E402,
)

if (3, 5) <= sys.version_info < (3, 6):
    warnings.warn(
        "Support for Python 3.5 will be removed in web3.py v5",
        category=DeprecationWarning,
        stacklevel=2)

if sys.version_info < (3, 5):
    raise EnvironmentError(
        "Python 3.5 or above is required. "
        "Note that support for Python 3.5 will be removed in web3.py v5")


__version__ = pkg_resources.get_distribution("platon_py").version

__all__ = [
    "__version__",
    "Web3"
]
