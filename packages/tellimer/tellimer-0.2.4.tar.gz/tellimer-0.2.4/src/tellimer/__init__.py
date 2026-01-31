try:
    from importlib.metadata import version

    __version__ = version("tellimer")
except Exception:
    __version__ = "0.0.0.dev"

from tellimer._clients._client import Client
from tellimer._clients._data import Filter
from tellimer._models import Result

__all__ = ["Client", "Filter", "Result"]
