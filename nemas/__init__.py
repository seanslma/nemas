from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('nemas')
except PackageNotFoundError:
    __version__ = '0.0.0'  # Fallback for development
