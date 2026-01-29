# gymDSM/__init__.py - gymDSM package initializer
###############################################################################################################
# Author: Daniel Saromo-Mori.
# Code adapted from OpenAI Gym's classic MountainCar (MIT licensed).
#
# Description:
#   This file exposes the public API of the gymDSM package.
#   It re-exports the main objects from the internal module `gymDSM.py` so users can do:
#
#       import gymDSM
#       env = gymDSM.make("MountainCar-v0")
#
###############################################################################################################

from .gymDSM import (  # noqa: F401
    __version__,
    ColoredActionMountainCarEnv,
    make,
    register_environments,
)

# Register environments on import for convenience.
register_environments()

__all__ = [
    "__version__",
    "ColoredActionMountainCarEnv",
    "make",
    "register_environments",
]
