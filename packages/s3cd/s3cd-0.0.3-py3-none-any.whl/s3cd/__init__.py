from importlib import metadata as _metadata

from s3cd.cli import cli  # noqa: F401

try:
    __version__ = _metadata.version('s3cd')
except _metadata.PackageNotFoundError:
    __version__ = '0.0.0'

__all__ = ['cli', '__version__']
