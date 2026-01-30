try:
    from . import extension

    __version__ = extension.__version__
except Exception as e:
    extension = None
    __version__ = None
    print(e)

from .subpixel import SubpixelSimulation
from .mode import SubpixelModeSolver, SubpixelModeSimulation

__all__ = ["SubpixelModeSimulation", "SubpixelModeSolver", "SubpixelSimulation", "__version__"]
