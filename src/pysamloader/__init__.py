
try:
    from ._version import __version__
except ImportError:
    from pkg_resources import get_distribution
    __version__ = get_distribution('pysamloader').version
