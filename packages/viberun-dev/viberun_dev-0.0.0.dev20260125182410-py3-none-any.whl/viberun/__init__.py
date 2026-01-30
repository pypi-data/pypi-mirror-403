from importlib.metadata import PackageNotFoundError, version

DIST_NAME = "viberun-dev"

try:
    __version__ = version(DIST_NAME)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
