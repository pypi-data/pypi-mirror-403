try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:  # pragma: no cover
    from importlib_metadata import version, PackageNotFoundError  # type: ignore

try:
    __version__ = version("pypac4http2")
except PackageNotFoundError:  # pragma: no cover
    # package is not installed
    __version__ = "unknown"

from pypac4http2.http_pac import HttpPac

__all__ = ["HttpPac", "__version__"]
