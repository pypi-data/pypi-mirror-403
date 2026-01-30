"""Sets the configuration for solver execution."""

import os
from typing import Optional

import numpy as np
import pydantic.v1 as pd

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(BASE_PATH, "config.json")


class ExtrasTidy3dConfig(pd.BaseModel):
    """configuration of backend tidy3d"""

    class Config:
        """Because of the way things are run as subprocesses in various places, the config is not
        dynamic. It can only be changed by modifying values in the config file."""

        frozen = True

    tmp_path: Optional[str] = None

    @property
    def precision(self):
        """Floating-point precision in use."""
        if os.environ.get("TIDY3D_DOUBLE_PRECISION") != "1":
            return "single"
        return "double"

    @property
    def fp_type(self):
        """Floating point numpy type depending on precision."""
        if os.environ.get("TIDY3D_DOUBLE_PRECISION") != "1":
            return np.float32
        return np.float64

    @property
    def cfp_type(self):
        """Complex floating point numpy type depending on precision."""
        if os.environ.get("TIDY3D_DOUBLE_PRECISION") != "1":
            return np.complex64
        return np.complex128


config = ExtrasTidy3dConfig.parse_file(CONFIG_FILE)
