"""
Utilities for pre and post-processing.
"""

import os
import shutil
import tempfile
from typing import Union

import h5py
import numpy as np
from tidy3d import Grid, Simulation, log
from tidy3d.components.types import Numpy
from tidy3d.exceptions import ValidationError
from tidy3d.components.data.data_array import ScalarFieldDataArray
from tidy3d.components.data.monitor_data import PermittivityData, MediumData
from tidy3d.components.monitor import PermittivityMonitor, MediumMonitor

from .core.config import config
from .core.custom_medium import write_chunk_custom_medium
from .core.simulation import BackendSimulation

try:
    from .extension import _gencoeffs
except Exception as exc:
    log.error(exc)
    _gencoeffs = None


def load_medium_monitor_data(
    eps_values,
    mu_values,
    comp_grid,
    mnt_grid,
    inds_mnt,
    symmetry,
    center,
    monitor: Union[PermittivityMonitor, MediumMonitor],
) -> Union[PermittivityData, MediumData]:
    """Load monitor data from eps and mu arrays."""
    fields = ("Ex", "Ey", "Ez", "Hx", "Hy", "Hz")
    field_components = {}
    coords = {}
    coords["f"] = np.array(monitor.freqs)
    for field_name in fields:
        component_index = ["x", "y", "z"].index(field_name[1])
        yee_locs = comp_grid.grid[field_name].to_list
        coords.update({dim: vals[inds] for dim, vals, inds in zip("xyz", yee_locs, inds_mnt)})

        # epsilon
        if field_name[0] == "E":
            eps_vals = eps_values[component_index]
            eps_name = f"eps_{field_name[1]}{field_name[1]}"
            field_components[eps_name] = ScalarFieldDataArray(eps_vals, coords=coords)
        # mu
        elif field_name[0] == "H" and isinstance(monitor, MediumMonitor):
            mu_vals = mu_values[component_index]
            mu_name = f"mu_{field_name[1]}{field_name[1]}"
            field_components[mu_name] = ScalarFieldDataArray(mu_vals, coords=coords)

    symmetry_kwargs = {
        "symmetry": symmetry,
        "symmetry_center": center,
        "grid_expanded": mnt_grid.grid,
    }

    if isinstance(monitor, PermittivityMonitor):
        return PermittivityData(monitor=monitor, **field_components, **symmetry_kwargs)
    return MediumData(monitor=monitor, **field_components, **symmetry_kwargs)


def write_material_yee_frequency_independent_files(
    sim: Simulation,
    span_inds: Numpy,
    input_file_name_prefix: str,
    grid: Grid = None,
):
    """Generate old json file and hdf5 file for gencoeffs. The two files are frequency-independent.
    The generated files are `file_name_prefix.json` and `file_name_prefix.hdf5`. `file_name_prefix`
    should contain the directory already.
    """

    if grid is None:
        grid = sim.grid

    # Store simulation to file
    file_path = os.path.dirname(input_file_name_prefix)
    os.makedirs(file_path, exist_ok=True)
    old_sim_json = input_file_name_prefix + ".json"
    BackendSimulation.backend_sim_to_json(sim, old_sim_json)

    # Make input temporary files and write all inputs
    file_in = input_file_name_prefix + ".hdf5"
    dset_name = "subdomain"
    with h5py.File(file_in, "w") as mfile:
        if "subdomains" not in mfile.keys():
            grp = mfile.create_group("subdomains")
        if "grid" not in mfile.keys():
            grp = mfile.create_group("grid")
            for dim in ("x", "y", "z"):
                grp.create_dataset(dim, data=grid.boundaries.to_dict[dim].astype(config.fp_type))
        grp = mfile.create_group("subdomains/" + dset_name)
        grp.create_dataset("span_inds", data=span_inds)

        # custom medium
        write_chunk_custom_medium(sim, grid, mfile, 0, span_inds)


def get_material_yee_cpp(
    freqs: Numpy,
    input_file_name_prefix: str,
    tmp_path: str = config.tmp_path,
    subpixel_scheme: int = 0,
    diagonal: bool = True,
):
    """Get the permittivity/mu/split using a call to the C++ preprocessing. C++ read files generated
    by `write_material_yee_frequency_independent_files`, which describes simulation object, and a subdomain defined
    by the ``span_inds`` over a ``grid`` (use ``sim.grid if grid is None``).
    """

    hdf5_file = input_file_name_prefix + ".hdf5"
    json_file = input_file_name_prefix + ".json"

    # write frequency-dependent data, e.g. frequencies
    os.makedirs(tmp_path, exist_ok=True)
    frequency_file = os.path.join(tmp_path, "eps_sub_in.hdf5")
    mfile = h5py.File(frequency_file, "w")
    grp = mfile.create_group("frequency")
    grp.create_dataset("freqs", data=freqs)
    mfile.close()

    # Make output temporary file
    file_out = os.path.join(tmp_path, "eps_sub_out.hdf5")

    # Call the epsilon generator
    if _gencoeffs is None:
        raise ValidationError(
            "Trying to get material properties using local subpixel, "
            "but the 'tidy3d-extras' package did not initialize correctly, "
            "likely due to an invalid API key."
        )
    _gencoeffs(
        json_file=json_file,
        hdf5_file=hdf5_file,
        frequency_file=frequency_file,
        file_out=file_out,
        subpixel_scheme=subpixel_scheme,
    )

    dset_name = "subdomain"
    # Read and return the results
    with h5py.File(file_out, "r") as mfile:
        group = mfile[dset_name]
        eps_sub = np.array(group["eps"])
        mu = group.get("mu")
        split_curl = group.get("splitCurlScaling")
        if mu is not None:
            mu = np.array(mu)
        if split_curl is not None:
            split_curl = np.array(split_curl)

    # eps_sub contains all 9 components
    if diagonal:
        eps_sub = eps_sub[:, :, :, :, [0, 4, 8]]
        if mu is not None:
            mu = mu[:, :, :, :, [0, 4, 8]]
    return eps_sub, mu, split_curl


class TempDir:
    def __enter__(self):
        if config.tmp_path is None:
            self.tmp_path = tempfile.mkdtemp()
        else:
            self.tmp_path = config.tmp_path
        return self.tmp_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        # clean up temp files, unless tmp_path is set explicitly
        if config.tmp_path is None:
            # import psutil
            # p = psutil.Process()
            # print(p.open_files())
            try:
                shutil.rmtree(self.tmp_path)
            except PermissionError as exc:
                log.warning("Unable to clean up local subpixel temp files.")
                log.warning(exc)
