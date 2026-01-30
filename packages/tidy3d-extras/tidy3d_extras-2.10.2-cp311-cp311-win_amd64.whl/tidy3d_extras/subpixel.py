from __future__ import annotations

import os
import uuid

import numpy as np
import xarray as xr
from tidy3d import Box, Coords, Grid, Monitor, PermittivityMonitor, ScalarFieldDataArray, Simulation
from tidy3d.components.base import cached_property
from tidy3d.components.medium import FREQ_EVAL_INF
from tidy3d.config import config

from .core.subgrid import monitor_grid_inds
from .utils import TempDir, get_material_yee_cpp, write_material_yee_frequency_independent_files


class SubpixelSimulation(Simulation):
    """Simulation with subpixel averaging."""

    subpixel_scheme: int = 0

    @cached_property
    def _uuid4(self):
        return uuid.uuid4().hex

    def _input_file_name_prefix(self, tmp_path: str):
        """File name for old simulation json. The json is created for each mode solver."""
        filename = "mode_eps_sub_sim_" + self._uuid4
        return os.path.join(tmp_path, filename)

    def _write_epsilon_frequency_independent_files(
        self, monitor: Monitor, input_file_name_prefix: str
    ):
        """Write files containing frequency-independent data so that they don't
        need to be computed again for each frequency.
        """
        (comp_grid, mnt_grid, inds_mnt) = monitor_grid_inds(self, monitor)
        grid = comp_grid.grid
        span_inds = [[np.min(inds), np.max(inds) + 1] for inds in inds_mnt]
        write_material_yee_frequency_independent_files(
            sim=self,
            span_inds=span_inds,
            input_file_name_prefix=input_file_name_prefix,
            grid=grid,
        )

    @staticmethod
    def _reshape_from_gencoeffs(mat_data):
        """
        gencoeffs returns shape (Nf, Nx, Ny, Nz, dim), so just need to swap first and last dim,
        and take a single frequency so squeeze frequency dim
        """
        if mat_data is None:
            return None

        # swap first and last dim
        mat_data = np.swapaxes(mat_data, 0, -1)

        # for now mode solver takes a single frequency so squeeze frequency dim
        return np.squeeze(mat_data, -1)

    @classmethod
    def _get_epsilon(cls, freq, subpixel_scheme, input_file_name_prefix, tmp_path):
        """
        Compute the diagonal components of the epsilon tensor in the plane using subpixel.

        Note: `_write_epsilon_frequency_independent_files` must be called before calling
        this method.
        """

        # Files for input-output to the C++ subpixel permittivity getter will go in this folder
        eps_sub, mu, split_curl = get_material_yee_cpp(
            freqs=np.array([freq]),
            input_file_name_prefix=input_file_name_prefix,
            tmp_path=os.path.join(tmp_path, uuid.uuid4().hex),
            subpixel_scheme=subpixel_scheme,
            diagonal=False,
        )
        return (cls._reshape_from_gencoeffs(f) for f in [eps_sub, mu, split_curl])

    def epsilon_on_grid(
        self, grid: Grid, coord_key: str = "centers", freq: float = None
    ) -> xr.DataArray:
        """Get array of permittivity at a given freq on a given grid.

        Parameters
        ----------
        grid : :class:`.Grid`
            Grid specifying where to measure the permittivity.
        coord_key : str = 'centers'
            Specifies at what part of the grid to return the permittivity at.
            Accepted values are ``{'centers', 'boundaries', 'Ex', 'Ey', 'Ez', 'Exy', 'Exz', 'Eyx',
            'Eyz', 'Ezx', Ezy'}``. The field values (eg. ``'Ex'``) correspond to the corresponding field
            locations on the yee lattice. If field values are selected, the corresponding diagonal
            (eg. ``eps_xx`` in case of ``'Ex'``) or off-diagonal (eg. ``eps_xy`` in case of ``'Exy'``) epsilon
            component from the epsilon tensor is returned. Otherwise, the average of the main
            values is returned.
        freq : float = None
            The frequency to evaluate the mediums at.
            If not specified, evaluates at infinite frequency.
        subpixel : bool = False
            Whether to use subpixel averaging.
            Requires installing the ``tidy3d-extras`` package.
            NOTE: This feature is not yet supported.

        Returns
        -------
        xarray.DataArray
            Datastructure containing the relative permittivity values and location coordinates.
            For details on xarray DataArray objects,
            refer to `xarray's Documentation <https://tinyurl.com/2zrzsp7b>`_.
        """
        if config.simulation.use_local_subpixel is False:
            return super().epsilon_on_grid(grid=grid, coord_key=coord_key, freq=freq)

        if freq is None:
            freq = FREQ_EVAL_INF

        with TempDir() as tmp_path:
            input_file_name_prefix = self._input_file_name_prefix(tmp_path=tmp_path)

            def get_eps():
                """Select the correct epsilon component if field locations are requested."""
                eps_sub, _, _ = self._get_epsilon(
                    freq=freq,
                    subpixel_scheme=self.subpixel_scheme,
                    input_file_name_prefix=input_file_name_prefix,
                    tmp_path=tmp_path,
                )
                if coord_key[0] != "E":
                    eps_diag = [eps_sub[4 * i] for i in range(3)]
                    return np.mean(eps_diag, axis=0)
                else:
                    row = ["x", "y", "z"].index(coord_key[1])
                    if len(coord_key) == 2:  # diagonal component in case of Ex, Ey, and Ez
                        col = row
                    else:  # off-diagonal component in case of Exy, Exz, Eyx, etc
                        col = ["x", "y", "z"].index(coord_key[2])
                    return eps_sub[3 * row + col]

            def make_eps_data(coords: Coords):
                """returns epsilon data on grid of points defined by coords"""
                arrays = (np.array(coords.x), np.array(coords.y), np.array(coords.z))

                rmin = (np.min(coords.x), np.min(coords.y), np.min(coords.z))
                rmax = (np.max(coords.x), np.max(coords.y), np.max(coords.z))
                geometry = Box.from_bounds(rmin=rmin, rmax=rmax)
                monitor = PermittivityMonitor(
                    size=geometry.size,
                    center=geometry.center,
                    name="<<<PERMITTIVITY_MONITOR>>>",
                    freqs=[freq],
                )
                (comp_grid, mnt_grid, inds_mnt) = monitor_grid_inds(self, monitor)

                self._write_epsilon_frequency_independent_files(
                    monitor=monitor, input_file_name_prefix=input_file_name_prefix
                )

                eps_array_raw = get_eps()

                if coord_key[0] == "E":
                    yee_locs = comp_grid.grid[coord_key[0:2]].to_list
                else:
                    yee_locs = comp_grid.grid[coord_key].to_list
                coords_raw = {dim: vals[inds] for dim, vals, inds in zip("xyz", yee_locs, inds_mnt)}
                scalar_data = ScalarFieldDataArray(
                    eps_array_raw, coords=coords_raw, dims=("x", "y", "z")
                )

                # now we symmetry expand
                for sym_dim, (sym_val, sym_loc) in enumerate(zip(self.symmetry, self.center)):
                    dim_name = "xyz"[sym_dim]

                    # Get coordinates for this field component on the expanded grid
                    coords = arrays[sym_dim]
                    coords = monitor.downsample(coords, axis=sym_dim)

                    coords_interp = np.copy(coords)

                    if sym_val != 0:
                        # Get indexes of coords that lie on the left of the symmetry center
                        flip_inds = np.where(coords < sym_loc)[0]

                        # Get the symmetric coordinates on the right
                        coords_interp[flip_inds] = 2 * sym_loc - coords[flip_inds]

                    # Interpolate. There generally shouldn't be values out of bounds except potentially
                    # when handling modes, in which case they should be at the boundary and close to 0.
                    scalar_data = scalar_data.sel(**{dim_name: coords_interp}, method="nearest")
                    scalar_data = scalar_data.assign_coords({dim_name: coords})
                return scalar_data

            # combine all data into dictionary
            if coord_key[0] == "E":
                # off-diagonal components are sampled at respective locations (eg. `eps_xy` at `Ex`)
                coords = grid[coord_key[0:2]]
            else:
                coords = grid[coord_key]
            return make_eps_data(coords)

    @classmethod
    def from_simulation(cls, sim: Simulation) -> SubpixelSimulation:
        """Convert a Simulation to a SubpixelSimulation."""
        sim_dict = dict(sim)
        sim_dict.pop("type")
        return cls.parse_obj(sim_dict)
