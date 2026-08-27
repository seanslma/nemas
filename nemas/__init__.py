from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('nemas')
except PackageNotFoundError:
    __version__ = '0.0.0'  # Fallback for development


from .data import (
    cache_data,
    get_data,
    get_url,
    read_zip,
)


__all__ = [
    'cache_data',
    'get_data',
    'get_url',
    'read_zip',
]
