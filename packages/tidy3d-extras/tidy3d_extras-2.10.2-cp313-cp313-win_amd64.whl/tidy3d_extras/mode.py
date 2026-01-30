from __future__ import annotations

import os
import uuid
from typing import Dict, List, Literal, Tuple, Union
import scipy.sparse as sp

import numpy as np

from tidy3d.components.base import Tidy3dBaseModel, cached_property
from tidy3d.components.mode.mode_solver import MODE_PLANE_TYPE, ModeSolver
from tidy3d.components.mode.simulation import MODE_SIM_MODE_SOLVER_SHARED_ATTRS, ModeSimulation
from tidy3d.components.mode.solver import EigSolver as FrontendEigSolver
from tidy3d.components.types.mode_spec import ModeSpecType
from tidy3d.components.types import (
    ArrayComplex4D,
    ArrayFloat1D,
    Axis,
    Direction,
    EpsSpecType,
    Symmetry,
)
from tidy3d.components.data.monitor_data import PermittivityData, MediumData
from tidy3d.components.mode.data.sim_data import ModeSimulationData
from tidy3d.components.monitor import PermittivityMonitor, Monitor, MediumMonitor
from tidy3d.config import config
from tidy3d.constants import ETA_0, fp_eps

from .subpixel import SubpixelSimulation
from .utils import (
    TempDir,
    write_material_yee_frequency_independent_files,
    get_material_yee_cpp,
    load_medium_monitor_data,
)
from .core.subgrid import snap_zero_dim, monitor_grid_inds
from .colocation import create_c_matrices as c_mats

MODE_SIM_MODE_SOLVER_EXTRA_ATTRS = [
    "subpixel_scheme",
]


class EigSolver(FrontendEigSolver):
    """EigSolver with improved fully tensorial handling."""

    @classmethod
    def solver_tensorial(
        cls,
        eps,
        mu,
        der_mats,
        num_modes,
        neff_guess,
        vec_init,
        mat_precision,
        direction,
        dls=None,
        Nxy=None,
        dmin_pmc=None,
    ):
        """EM eigenmode solver assuming ``eps`` or ``mu`` have off-diagonal elements.
        Additionally, enforce PEC/PMC at xmin/ymin by eliminating constrained DOFs
        (tangential E and normal H) from the unknown space to avoid spurious boundary modes.
        """

        mode_solver_type = "tensorial"
        N = eps.shape[-1]
        dxf, dxb, dyf, dyb = der_mats

        if dls:
            col_mats = c_mats(Nxy, dls, dmin_pmc)
        else:
            col_mats = [sp.eye(N)] * 4
        cxf, cxb, cyf, cyb = col_mats

        # Create sparse diagonal matrices for mu tensor components
        mu_xx = sp.spdiags(mu[0, 0, :], [0], N, N)
        mu_xy = sp.spdiags(mu[0, 1, :], [0], N, N)
        mu_xz = sp.spdiags(mu[0, 2, :], [0], N, N)
        mu_yx = sp.spdiags(mu[1, 0, :], [0], N, N)
        mu_yy = sp.spdiags(mu[1, 1, :], [0], N, N)
        mu_yz = sp.spdiags(mu[1, 2, :], [0], N, N)
        mu_zx = sp.spdiags(mu[2, 0, :], [0], N, N)
        mu_zy = sp.spdiags(mu[2, 1, :], [0], N, N)
        # mu_zz = sp.spdiags(mu[2, 2, :], [0], N, N)
        inv_mu_zz = sp.spdiags(1 / mu[2, 2, :], [0], N, N)

        # Create sparse diagonal matrices for eps tensor components
        eps_xx = sp.spdiags(eps[0, 0, :], [0], N, N)
        eps_xy = sp.spdiags(eps[0, 1, :], [0], N, N)
        eps_xz = sp.spdiags(eps[0, 2, :], [0], N, N)
        eps_yx = sp.spdiags(eps[1, 0, :], [0], N, N)
        eps_yy = sp.spdiags(eps[1, 1, :], [0], N, N)
        eps_yz = sp.spdiags(eps[1, 2, :], [0], N, N)
        eps_zx = sp.spdiags(eps[2, 0, :], [0], N, N)
        eps_zy = sp.spdiags(eps[2, 1, :], [0], N, N)
        # eps_zz = sp.spdiags(eps[2, 2, :], [0], N, N)
        inv_eps_zz = sp.spdiags(1 / eps[2, 2, :], [0], N, N)

        # Compute all blocks of the matrix for diagonalization
        axax = -dxf.dot(inv_eps_zz).dot(eps_zx).dot(cxb) - cyb.dot(mu_yz).dot(inv_mu_zz).dot(dyf)
        axay = -dxf.dot(inv_eps_zz).dot(eps_zy).dot(cyb) + cyb.dot(mu_yz).dot(inv_mu_zz).dot(dxf)
        axbx = (
            -dxf.dot(inv_eps_zz).dot(dyb)
            + cyb.dot(mu_yx).dot(inv_mu_zz).dot(cxf)
            - cyb.dot(mu_yz).dot(inv_mu_zz).dot(mu_zx).dot(cxf)
        )
        axby = (
            dxf.dot(inv_eps_zz).dot(dxb) + mu_yy - cyb.dot(mu_yz).dot(inv_mu_zz).dot(mu_zy).dot(cyf)
        )

        ayax = -dyf.dot(inv_eps_zz).dot(eps_zx).dot(cxb) + cxb.dot(mu_xz).dot(inv_mu_zz).dot(dyf)
        ayay = -dyf.dot(inv_eps_zz).dot(eps_zy).dot(cyb) - cxb.dot(mu_xz).dot(inv_mu_zz).dot(dxf)
        aybx = (
            -dyf.dot(inv_eps_zz).dot(dyb)
            - mu_xx
            + cxb.dot(mu_xz).dot(inv_mu_zz).dot(mu_zx).dot(cxf)
        )
        ayby = (
            dyf.dot(inv_eps_zz).dot(dxb)
            + cxb.dot(mu_xz).dot(inv_mu_zz).dot(mu_zy).dot(cyf)
            - cxb.dot(mu_xy).dot(cyf)
        )

        bxbx = -dxb.dot(inv_mu_zz).dot(mu_zx).dot(cxf) - cyf.dot(eps_yz).dot(inv_eps_zz).dot(dyb)
        bxby = -dxb.dot(inv_mu_zz).dot(mu_zy).dot(cyf) + cyf.dot(eps_yz).dot(inv_eps_zz).dot(dxb)
        bxax = (
            -dxb.dot(inv_mu_zz).dot(dyf)
            + cyf.dot(eps_yx).dot(cxb)
            - cyf.dot(eps_yz).dot(inv_eps_zz).dot(eps_zx).dot(cxb)
        )
        bxay = (
            dxb.dot(inv_mu_zz).dot(dxf)
            + eps_yy
            - cyf.dot(eps_yz).dot(inv_eps_zz).dot(eps_zy).dot(cyb)
        )

        bybx = -dyb.dot(inv_mu_zz).dot(mu_zx).dot(cxf) + cxf.dot(eps_xz).dot(inv_eps_zz).dot(dyb)
        byby = -dyb.dot(inv_mu_zz).dot(mu_zy).dot(cyf) - cxf.dot(eps_xz).dot(inv_eps_zz).dot(dxb)
        byax = (
            -dyb.dot(inv_mu_zz).dot(dyf)
            - eps_xx
            + cxf.dot(eps_xz).dot(inv_eps_zz).dot(eps_zx).dot(cxb)
        )
        byay = (
            dyb.dot(inv_mu_zz).dot(dxf)
            - cxf.dot(eps_xy).dot(cyb)
            + cxf.dot(eps_xz).dot(inv_eps_zz).dot(eps_zy).dot(cyb)
        )

        mat = sp.bmat(
            [
                [axax, axay, axbx, axby],
                [ayax, ayay, aybx, ayby],
                [bxax, bxay, bxbx, bxby],
                [byax, byay, bybx, byby],
            ]
        )

        # The eigenvalues for the matrix above are 1j * (neff + 1j * keff)
        # Multiply the matrix by -1j, so that eigenvalues are (neff + 1j * keff)
        mat *= -1j

        # change matrix sign for backward direction
        if direction == "-":
            mat *= -1

        """Build elimination masks for PEC boundaries if grid and boundary info provided.
        We already apply boundary conditions in the derivative and colocation matrices. This seems
        to be enough in most cases, but at least in the case of a mode solver with an angle, when
        both off-diagonal eps and mu are introduced, we've observed cases where unphysical modes
        localized at the PEC boundary appear, due to some coupling introduced by the off-diagonal
        terms. To avoid this, here we eliminate the DOFs associated with the tangential E and
        normal H components at PEC boundaries. No such treatment is applied for PMC as the fields
        live half a step away from the boundary, and they cannot be simply zeroed out - but no
        spurious modes have been observed in PMC cases so far.
        """
        keep = None
        Nx = Ny = None
        if Nxy is not None and dmin_pmc is not None:
            Nx, Ny = Nxy
            Ntot = N
            # base masks per component
            keep_ax = np.ones(Ntot, dtype=bool)
            keep_ay = np.ones(Ntot, dtype=bool)
            keep_bx = np.ones(Ntot, dtype=bool)
            keep_by = np.ones(Ntot, dtype=bool)
            # indices along xmin and ymin assuming C-order flatten with Ny as inner stride
            xmin_idx = np.arange(Ny)
            ymin_idx = np.arange(0, Ntot, Ny)
            # x-min boundary
            if not dmin_pmc[0]:
                # PEC at xmin: remove ay[0,:], bx[0,:]
                keep_ay[xmin_idx] = False
                keep_bx[xmin_idx] = False
            # y-min boundary
            if not dmin_pmc[1]:
                # PEC at ymin: remove ax[:,0], by[:,0]
                keep_ax[ymin_idx] = False
                keep_by[ymin_idx] = False
            # pack into 4N mask
            keep = np.concatenate([keep_ax, keep_ay, keep_bx, keep_by])

        # Cast matrix to target data type
        mat_dtype = cls.matrix_data_type(eps, mu, der_mats, mat_precision, is_tensorial=True)
        mat = cls.type_conversion(mat, mat_dtype)

        # Apply elimination by slicing rows/cols and reduce initial vector
        if keep is not None:
            mat = mat[keep][:, keep]
            vec_init = vec_init[keep]

        # Trim small values in single precision case
        if mat_precision == "single":
            cls.trim_small_values(mat, tol=fp_eps)

        # Casting starting vector to target data type
        vec_init = cls.type_conversion(vec_init, mat_dtype)

        # Starting eigenvalue guess in target data type
        eig_guess = cls.type_conversion(np.array([neff_guess]), mat_dtype)[0]

        # Call the eigensolver.
        vals, vecs = cls.solver_eigs(
            mat,
            num_modes,
            vec_init,
            guess_value=eig_guess,
            mode_solver_type=mode_solver_type,
        )
        neff, keff = cls.eigs_to_effective_index(vals, mode_solver_type)
        # Sort by descending real part
        sort_inds = np.argsort(neff)[::-1]
        neff = neff[sort_inds]
        keff = keff[sort_inds]
        vecs = vecs[:, sort_inds]

        # If we eliminated DOFs, expand eigenvectors back to 4N by inserting zeros
        if keep is not None:
            full_vecs = np.zeros((4 * N, vecs.shape[1]), dtype=vecs.dtype)
            full_vecs[keep, :] = vecs
            vecs = full_vecs

        # Field components from eigenvectors
        Ex = vecs[:N, :]
        Ey = vecs[N : 2 * N, :]
        Hx = vecs[2 * N : 3 * N, :]
        Hy = vecs[3 * N :, :]

        # Get the other field components
        hxy_term = (-mu[2, 0, :] * cxf.dot(Hx).T - mu[2, 1, :] * cyf.dot(Hy).T).T
        Hz = inv_mu_zz.dot(dxf.dot(Ey) - dyf.dot(Ex) + hxy_term)
        exy_term = (-eps[2, 0, :] * cxb.dot(Ex).T - eps[2, 1, :] * cyb.dot(Ey).T).T
        Ez = inv_eps_zz.dot(dxb.dot(Hy) - dyb.dot(Hx) + exy_term)

        # Bundle up
        E = np.stack((Ex, Ey, Ez), axis=0)
        H = np.stack((Hx, Hy, Hz), axis=0)

        # Return to standard H field units (see CEM notes for H normalization used in solver)
        # The minus sign here is suspicious, need to check how modes are used in Mode objects
        H *= -1j / ETA_0

        return E, H, neff, keff


class ModeSubpixelData(Tidy3dBaseModel):
    """A data class to group a set of data common to each frequency solve. This is to make it convenient to
    pass so many variables to staticmethods of single frequency solve. All fields in this class should be light-weighted.
    For heavy data, it's better to write them to files with `_write_epsilon_frequency_independent_files`.
    """

    coords: Tuple[ArrayFloat1D, ArrayFloat1D]
    symmetry: Tuple[Symmetry, Symmetry]
    subpixel_scheme: int
    input_file_name_prefix: str
    tmp_path: str
    normal_axis: Axis
    plane: MODE_PLANE_TYPE
    mode_spec: ModeSpecType
    precision: Literal["single", "double"]
    direction: Direction


class SubpixelModeSolver(ModeSolver):
    """Mode solver with subpixel averaging for improved accuracy."""

    subpixel_scheme: int = 0

    @cached_property
    def _uuid4(self):
        return uuid.uuid4().hex

    def _input_file_name_prefix(self, tmp_path: str):
        """File name for old simulation json. The json is created for each mode solver."""
        filename = "mode_eps_sub_sim_" + self._uuid4
        return os.path.join(tmp_path, filename)

    def _write_epsilon_frequency_independent_files(
        self, input_file_name_prefix: str, monitor: Monitor = None
    ):
        """Write files containing frequency-independent data so that they don't
        need to be computed again for each frequency.
        """
        if monitor is None:
            grid = self._solver_grid
            end_inds = [len(bounds) - 1 for bounds in grid.boundaries.to_list]
            end_inds[self.normal_axis] = 1
            span_inds = [[0, end_ind] for end_ind in end_inds]
        else:
            (comp_grid, mnt_grid, inds_mnt) = monitor_grid_inds(self.simulation, monitor)
            grid = comp_grid.grid
            span_inds = [[np.min(inds), np.max(inds) + 1] for inds in inds_mnt]

        write_material_yee_frequency_independent_files(
            sim=self.simulation,
            span_inds=span_inds,
            input_file_name_prefix=input_file_name_prefix,
            grid=grid,
        )

    @classmethod
    def _solver_eps(
        cls, freq: float, subpixel_scheme, input_file_name_prefix, normal_axis, tmp_path
    ):
        """Diagonal permittivity in the shape needed by solver, with normal axis rotated to z."""
        # Get components in the plane
        eps_sub, mu, split_curl = SubpixelSimulation._get_epsilon(
            freq=freq,
            subpixel_scheme=subpixel_scheme,
            input_file_name_prefix=input_file_name_prefix,
            tmp_path=tmp_path,
        )
        # tranformation
        eps_sub = cls._tensorial_material_profile_modal_plane_tranform(eps_sub, normal_axis)
        if mu is not None:
            mu = cls._tensorial_material_profile_modal_plane_tranform(mu, normal_axis)
        if split_curl is not None:
            split_curl = cls._diagonal_material_profile_modal_plane_tranform(
                split_curl, normal_axis
            )
        return eps_sub, mu, split_curl

    @classmethod
    def _solve_single_freq(cls, freq: float, subpixel_data: ModeSubpixelData):
        """Call the mode solver at a single frequency.

        The fields are rotated from propagation coordinates back to global coordinates.
        """

        eps_cross, mu, split_curl = cls._solver_eps(
            freq=freq,
            normal_axis=subpixel_data.normal_axis,
            subpixel_scheme=subpixel_data.subpixel_scheme,
            input_file_name_prefix=subpixel_data.input_file_name_prefix,
            tmp_path=subpixel_data.tmp_path,
        )
        solver_fields, n_complex, eps_spec = EigSolver.compute_modes(
            eps_cross=eps_cross,
            mu_cross=mu,
            split_curl_scaling=split_curl,
            coords=subpixel_data.coords,
            freq=freq,
            mode_spec=subpixel_data.mode_spec,
            symmetry=subpixel_data.symmetry,
            direction=subpixel_data.direction,
            precision=subpixel_data.precision,
            plane_center=cls.plane_center_tangential(subpixel_data.plane),
        )

        fields = ModeSolver._postprocess_solver_fields(
            solver_fields=solver_fields,
            normal_axis=subpixel_data.normal_axis,
            plane=subpixel_data.plane,
            mode_spec=subpixel_data.mode_spec,
            coords=subpixel_data.coords,
        )
        return n_complex, fields, eps_spec

    @classmethod
    def _solve_single_freq_relative(
        cls, freq: float, basis_fields: Dict[str, ArrayComplex4D], subpixel_data: ModeSubpixelData
    ) -> Tuple[float, Dict[str, ArrayComplex4D], EpsSpecType]:
        """Call the mode solver at a single frequency.
        Modes are computed as linear combinations of ``basis_fields``
        and the coefficients are returned.
        """

        solver_basis_fields = cls._postprocess_solver_fields_inverse(
            fields=basis_fields, normal_axis=subpixel_data.normal_axis, plane=subpixel_data.plane
        )
        eps_cross, mu, split_curl = cls._solver_eps(
            freq=freq,
            subpixel_scheme=subpixel_data.subpixel_scheme,
            input_file_name_prefix=subpixel_data.input_file_name_prefix,
            normal_axis=subpixel_data.normal_axis,
            tmp_path=subpixel_data.tmp_path,
        )
        solver_fields, n_complex, eps_spec = EigSolver.compute_modes(
            eps_cross=eps_cross,
            mu_cross=mu,
            split_curl_scaling=split_curl,
            coords=subpixel_data.coords,
            freq=freq,
            mode_spec=subpixel_data.mode_spec,
            symmetry=subpixel_data.symmetry,
            direction=subpixel_data.direction,
            plane_center=cls.plane_center_tangential(subpixel_data.plane),
            solver_basis_fields=solver_basis_fields,
            precision=subpixel_data.precision,
        )

        fields = ModeSolver._postprocess_solver_fields(
            solver_fields=solver_fields,
            normal_axis=subpixel_data.normal_axis,
            plane=subpixel_data.plane,
            mode_spec=subpixel_data.mode_spec,
            coords=subpixel_data.coords,
        )
        return n_complex, fields, eps_spec

    def _get_subpixel_data(self, coords, symmetry, input_file_name_prefix, tmp_path):
        subpixel_data = ModeSubpixelData(
            coords=coords,
            symmetry=symmetry,
            subpixel_scheme=self.subpixel_scheme,
            input_file_name_prefix=input_file_name_prefix,
            tmp_path=tmp_path,
            normal_axis=self.normal_axis,
            plane=self.plane,
            mode_spec=self.mode_spec,
            direction=self.direction,
            precision=self._precision,
        )
        return subpixel_data

    def _solve_all_freqs(self, coords, symmetry):
        """Solve for all frequencies."""
        with TempDir() as tmp_path:
            # Make the backend simulation object and export json and hdf5 files for mode solver.
            # Note: the simulation object in mode solver can be different from the parent
            #       simulation object because of subsection. Thus, a separate simulation json
            #       is exported for each mode solver.
            input_file_name_prefix = self._input_file_name_prefix(tmp_path=tmp_path)
            self._write_epsilon_frequency_independent_files(
                input_file_name_prefix=input_file_name_prefix
            )
            subpixel_data = self._get_subpixel_data(
                coords=coords,
                symmetry=symmetry,
                input_file_name_prefix=input_file_name_prefix,
                tmp_path=tmp_path,
            )

            fields = []
            n_complex = []
            eps_spec = []
            for freq in self.freqs:
                n_freq, fields_freq, eps_spec_freq = self._solve_single_freq(
                    freq=freq, subpixel_data=subpixel_data
                )
                fields.append(fields_freq)
                n_complex.append(n_freq)
                eps_spec.append(eps_spec_freq)
            return n_complex, fields, eps_spec

    def _solve_all_freqs_relative(
        self,
        coords: Tuple[ArrayFloat1D, ArrayFloat1D],
        symmetry: Tuple[Symmetry, Symmetry],
        basis_fields: List[Dict[str, ArrayComplex4D]],
    ) -> Tuple[List[float], List[Dict[str, ArrayComplex4D]], List[EpsSpecType]]:
        """Call the mode solver at all requested frequencies."""
        with TempDir() as tmp_path:
            # Make the backend simulation object and export the json for mode solver.
            input_file_name_prefix = self._input_file_name_prefix(tmp_path=tmp_path)
            self._write_epsilon_frequency_independent_files(
                input_file_name_prefix=input_file_name_prefix
            )
            subpixel_data = self._get_subpixel_data(
                coords=coords,
                symmetry=symmetry,
                input_file_name_prefix=input_file_name_prefix,
                tmp_path=tmp_path,
            )

            fields = []
            n_complex = []
            eps_spec = []
            for freq, basis_fields_freq in zip(self.freqs, basis_fields):
                n_freq, fields_freq, eps_spec_freq = self._solve_single_freq_relative(
                    freq=freq, basis_fields=basis_fields_freq, subpixel_data=subpixel_data
                )
                fields.append(fields_freq)
                n_complex.append(n_freq)
                eps_spec.append(eps_spec_freq)

            return n_complex, fields, eps_spec

    @classmethod
    def from_mode_solver(cls, mode_solver: ModeSolver) -> SubpixelModeSolver:
        """Convert a ModeSolver to a SubpixelModeSolver."""
        ms_dict = dict(mode_solver)
        ms_dict.pop("type")
        return cls.parse_obj(ms_dict)

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

    @staticmethod
    def _get_epsilon(freq, subpixel_scheme, input_file_name_prefix, tmp_path):
        """
        Compute the diagonal components of the epsilon tensor in the plane using subpixel.

        Note: `_write_epsilon_frequency_independent_files` must be called before calling
        this method.
        """

        # Files for input-output to the C++ subpixel permittivity getter will go in this folder
        eps_sub, mu, split_curl = get_material_yee_cpp(
            freqs=np.array([freq]),
            input_file_name_prefix=input_file_name_prefix,
            tmp_path=tmp_path,
            subpixel_scheme=subpixel_scheme,
            diagonal=False,
        )
        return (SubpixelModeSolver._reshape_from_gencoeffs(f) for f in [eps_sub, mu, split_curl])


class SubpixelModeSimulation(ModeSimulation):
    subpixel_scheme: int = 0

    @classmethod
    def from_mode_simulation(cls, sim: ModeSimulation, extra_kwargs: Dict = None):
        """Load a backend mode solver instance from a frontend mode simulation. Extra kwargs can
        also be passed. They will overwrite any of the existing values, if both provided.
        """
        mode_sim_dict = dict(sim)
        mode_sim_dict.pop("type")
        if extra_kwargs:
            mode_sim_dict.update(extra_kwargs)
        return cls.parse_obj(mode_sim_dict)

    def to_mode_simulation(self) -> ModeSimulation:
        """Convert the :class:`.SubpixelModeSimulation` to a :class:`.ModeSimulation`."""
        mode_sim_dict = dict(self)
        mode_sim_dict.pop("type")
        for key in MODE_SIM_MODE_SOLVER_EXTRA_ATTRS:
            mode_sim_dict.pop(key)
        return ModeSimulation.parse_obj(mode_sim_dict)

    @cached_property
    def _mode_solver(self) -> SubpixelModeSolver:
        """Convert the :class:`.SubpixelModeSimulation` to a :class:`.SubpixelModeSolver`."""
        kwargs = {key: getattr(self, key) for key in MODE_SIM_MODE_SOLVER_SHARED_ATTRS}
        extra_kwargs = {key: getattr(self, key) for key in MODE_SIM_MODE_SOLVER_EXTRA_ATTRS}
        return SubpixelModeSolver(simulation=self._as_fdtd_sim, **kwargs, **extra_kwargs)

    def run_local(self) -> ModeSimulationData:
        """Run the :class:`.SubpixelModeSimulation`."""
        if config.simulation.use_local_subpixel is False:
            return super().run_local()

        # repeat the calculation every time, in case use_local_subpixel changed
        self._invalidate_solver_cache()

        sim = self.to_mode_simulation()
        modes_raw = self._mode_solver.data_raw
        new_monitor = modes_raw.monitor.updated_copy(name="MODE_SOLVER_MONITOR")
        modes_raw = modes_raw.updated_copy(monitor=new_monitor)

        monitor_data = {}
        for monitor in sim.monitors:
            if isinstance(monitor, (MediumMonitor, PermittivityMonitor)):
                monitor_data[monitor.name] = self.get_medium_monitor_data(monitor=monitor)

        sim_data = ModeSimulationData(
            simulation=sim, modes_raw=modes_raw, data=list(monitor_data.values())
        )
        return sim_data

    def get_medium_monitor_data(
        self, monitor: Union[PermittivityMonitor, MediumMonitor]
    ) -> Union[PermittivityData, MediumData]:
        """Get permittivity/medium monitor data."""
        with TempDir() as tmp_path:
            input_file_name_prefix = self._mode_solver._input_file_name_prefix(tmp_path=tmp_path)
            self._mode_solver._write_epsilon_frequency_independent_files(
                input_file_name_prefix=input_file_name_prefix, monitor=monitor
            )
            # eps_xx, eps_yy, eps_zz
            eps_values = [[], [], []]
            mu_values = [[], [], []]
            (comp_grid, mnt_grid, inds_mnt) = monitor_grid_inds(self, monitor)
            for freq in monitor.freqs:
                # Get components in the plane
                eps_sub, mu_sub, split_curl = self._mode_solver._get_epsilon(
                    freq=freq,
                    subpixel_scheme=self.subpixel_scheme,
                    input_file_name_prefix=input_file_name_prefix,
                    tmp_path=tmp_path,
                )
                for i in range(3):
                    eps = eps_sub[4 * i]
                    eps_values[i].append(eps)
                    mu = mu_sub[4 * i]
                    mu_values[i].append(mu)
            mat_data = load_medium_monitor_data(
                eps_values,
                mu_values,
                comp_grid,
                mnt_grid,
                inds_mnt,
                self.symmetry,
                self.center,
                monitor,
            )
            return snap_zero_dim(self, mat_data)
