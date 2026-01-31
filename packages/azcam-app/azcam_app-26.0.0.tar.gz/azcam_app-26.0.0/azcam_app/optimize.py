"""
Optimize azcam built-ins for azcam-app.
Everything here is imported to the azcam-app CLI.
"""

import azcam

# set imports
pars = azcam.db.parameters
api = azcam.db.api

__all__ = ["azcam", "pars", "api"]

for obj in azcam.db.tools:
    locals()[obj] = azcam.db.tools[obj]
    __all__.append(obj)
