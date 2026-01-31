from importlib.metadata import version as get_version

__version__ = get_version(__package__)  # type: ignore
__all__ = ["__version__"]
