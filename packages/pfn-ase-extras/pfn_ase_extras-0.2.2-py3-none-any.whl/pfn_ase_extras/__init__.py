from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("pfn_ase_extras")
except PackageNotFoundError:
    # package is not installed
    pass
