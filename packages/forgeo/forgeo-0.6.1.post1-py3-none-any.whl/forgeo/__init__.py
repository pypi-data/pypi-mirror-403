try:
    from .__version__ import __version__, __version_tuple__, version, version_tuple
except ImportError:
    __version__ = version = None
    __version_tuple__ = version_tuple = ()
