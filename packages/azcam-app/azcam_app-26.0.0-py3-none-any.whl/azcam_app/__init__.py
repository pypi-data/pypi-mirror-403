"""
azcam-app is an application used to control imaging systems such as those
used for scientific observations."""

from importlib import metadata

from azcam.database import AzcamDatabase

__version__ = metadata.version(__package__)
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())
