"""Backend versions of frontend structure with custom medium classes (time modulated medium
is also considered as custom medium here).
"""

from typing import Optional, Tuple, Union

import h5py
import numpy as np
import pydantic.v1 as pd
import xarray as xr
from tidy3d import Coords, CustomMedium, Grid, Simulation, Structure
from tidy3d.components.base import Tidy3dBaseModel
from tidy3d.components.data.data_array import SpatialDataArray
from tidy3d.components.data.utils import CustomSpatialDataType, UnstructuredGridDataset
from tidy3d.components.medium import (
    AbstractCustomMedium,
    AnisotropicMedium,
    DispersiveMedium,
    MediumType,
)
from tidy3d.components.types import ArrayComplex3D, ArrayFloat3D, InterpMethod, Numpy
from tidy3d.exceptions import SetupError
from tidy3d.log import log
from tidy3d.components.nonlinear import (
    NonlinearSusceptibility,
    KerrNonlinearity,
    TwoPhotonAbsorption,
)

from .config import config

# for convenience
NAME_TO_IND = {"xx": 0, "yy": 1, "zz": 2}


def get_finalized_full_optical_medium_map(
    finalized_optical_medium_map: dict[MediumType, pd.NonNegativeInt],
) -> dict[MediumType, pd.NonNegativeInt]:
    """Returns dict mapping medium to index in material in finalized simulation, including
    media from which custom media have been derived.
    """
    full_medium_map = dict(finalized_optical_medium_map)
    next_index = len(full_medium_map)
    for medium in finalized_optical_medium_map.keys():
        if (
            isinstance(medium, AbstractCustomMedium)
            and medium.derived_from is not None
            and medium.derived_from not in full_medium_map
        ):
            full_medium_map[medium.derived_from] = next_index
            next_index += 1
    return full_medium_map


class StructureWithCustomMediumData(Tidy3dBaseModel):
    """Data class for the processed structure of custom media, and time modulated medium."""

    inds_range: Tuple = pd.Field(
        ...,
        title="Range of indices along each dimension",
        description="The permittivity of the custom media is interpolated "
        "inside this range. This list provides the lower "
        "and upper indices of the bounding box, in the format of "
        "[xl, xu, yl, yu, zl, zu]",
    )
    modulation_frequency: Tuple[float, float, float] = pd.Field(
        (0, 0, 0),
        title="Modulation frequency",
        description="Modulation frequency that can be anisotropic; ``0`` value "
        "at a component means that no modulation is applied along this component.",
    )
    eps_inf: Numpy = pd.Field(
        np.ones((1, 3)),
        title="Epsilon at Infinity",
        description="Epsilon at Infinity in the shape of [Mx*My*Mz, 3], where "
        "Mx=inds_range[1]-inds_range[0], etc.",
    )
    eps_inf_modulation: Tuple = pd.Field(
        (None, None, None),
        title="Epsilon at Infinity modulation amplitude and phase",
        description="In the format of ``(amp + 1j * phase / pi)``, and in the shape "
        "of [Mx*My*Mz, 3], where "
        "Mx=inds_range[1]-inds_range[0], etc.",
    )
    conductivity: Numpy = pd.Field(
        np.zeros((1, 3)),
        title="Conductivity",
        description="Conductivity in the shape of [Mx*My*Mz, 3], where "
        "Mx=inds_range[1]-inds_range[0], etc.",
    )
    conductivity_modulation: Tuple = pd.Field(
        (None, None, None),
        title="Conductivity modulation amplitude and phase",
        description="In the format of ``(amp + 1j * phase / pi)``, and in the shape "
        "of [Mx*My*Mz, 3], where "
        "Mx=inds_range[1]-inds_range[0], etc.",
    )
    poles_a: Tuple[Optional[Numpy], Optional[Numpy], Optional[Numpy]] = pd.Field(
        (None, None, None),
        title="Pole coefficient a_i",
        description="Each component of pole coefficient a_i in the shape of "
        "[num_poles, Mx*My*Mz], where Mx=inds_range[1]-inds_range[0], etc.",
    )
    poles_c: Tuple[Optional[Numpy], Optional[Numpy], Optional[Numpy]] = pd.Field(
        (None, None, None),
        title="Pole coefficient c_i",
        description="Each component of pole coefficient c_i in the shape of "
        "[num_poles, Mx*My*Mz], where Mx=inds_range[1]-inds_range[0], etc.",
    )
    subpixel: Tuple[bool, bool, bool] = pd.Field(
        ...,
        title="Subpixel averaging for each component",
        description="If ``True`` and simulation's ``subpixel`` is also ``True``, "
        "applies subpixel averaging of the permittivity "
        "on the interfaces of the structure.",
    )
    subpixel_identifier: int = pd.Field(
        0,
        title="Subpixel identifier",
        description="Custom medium of equal and nonzero identifier are considered equal in subpixel averaging.",
    )

    @pd.validator("inds_range", always=True)
    def _lower_index_no_greater_upper_index(cls, val):
        for ind_dim in range(3):
            if val[ind_dim * 2 + 1] < val[ind_dim * 2]:
                raise SetupError("Lower index cannot exceed upper index in 'inds_range'")
        return val

    @property
    def dispersive(self) -> Tuple[bool, bool, bool]:
        """The medium has dispersive xx, yy, zz components."""
        return tuple(f is not None for f in self.poles_a)


def fun_interp(
    coord_interp: Coords,
    input_data: Union[CustomSpatialDataType, float],
    interp_method: InterpMethod,
) -> Union[ArrayFloat3D, ArrayComplex3D]:
    """Function that interpolate data to grids"""
    if not isinstance(input_data, (xr.DataArray, UnstructuredGridDataset)):
        input_data = SpatialDataArray(
            np.ones((1, 1, 1)) * input_data, coords=dict(x=[0], y=[0], z=[0])
        )
    return coord_interp.spatial_interp(input_data, interp_method).values


def interpolated_isotropic_material_parameters(
    material, coord_interp: Coords, interp_method: InterpMethod
):
    """For a given component of a isotropic medium `material`, interpolate material
    parameters at `coord_interp`. The medium can be custom/regular.

    The returned interpolated parameters are: eps_inf, sigma, poles.
    """
    if isinstance(material, AbstractCustomMedium) and not material.is_isotropic:
        raise SetupError("'material' in this function must be isotropic.")

    mat_internal = material
    # `CustomMedium` needs special treatment in v2.0
    if isinstance(material, CustomMedium):
        mat_internal = material._medium

    # isotropic dispersive medium
    if isinstance(mat_internal, DispersiveMedium):
        mat_pole = mat_internal.pole_residue
        poles_interp = tuple(
            (fun_interp(coord_interp, a, interp_method), fun_interp(coord_interp, c, interp_method))
            for (a, c) in mat_pole.poles
        )
        eps_inf_interp = fun_interp(coord_interp, mat_pole.eps_inf, interp_method)
        sigma_interp = np.zeros_like(eps_inf_interp)
        return eps_inf_interp, sigma_interp, poles_interp

    # isotropic non-dispersive medium
    eps_inf_interp = fun_interp(coord_interp, mat_internal.permittivity, interp_method)
    sigma_interp = np.zeros_like(eps_inf_interp)
    if mat_internal.conductivity is not None:
        sigma_interp = fun_interp(coord_interp, mat_internal.conductivity, interp_method)
    return eps_inf_interp, sigma_interp, None


def interpolated_modulated_medium_parameters(mat_comp, coord_interp: Coords):
    """Interpolate time modulation parameters. `mat_comp` must be an isotropic medium, and
    time modulated.
    """
    modulation_frequency = None
    eps_inf_modulation = None
    sigma_modulation = None

    modulation = mat_comp.modulation_spec
    if modulation.permittivity is not None:
        modulation_frequency = modulation.permittivity.time_modulation.freq0
        eps_modulate_amp = fun_interp(
            coord_interp,
            modulation.permittivity.time_modulation.amplitude
            * modulation.permittivity.space_modulation.amplitude,
            modulation.permittivity.space_modulation.interp_method,
        )
        eps_modulate_phase = fun_interp(
            coord_interp,
            modulation.permittivity.time_modulation.phase
            + modulation.permittivity.space_modulation.phase,
            modulation.permittivity.space_modulation.interp_method,
        )
        eps_inf_modulation = (
            eps_modulate_amp.real.ravel() + 1j * eps_modulate_phase.real.ravel() / np.pi
        )

    if modulation.conductivity is not None:
        modulation_frequency = modulation.conductivity.time_modulation.freq0
        sigma_modulate_amp = fun_interp(
            coord_interp,
            modulation.conductivity.time_modulation.amplitude
            * modulation.conductivity.space_modulation.amplitude,
            modulation.conductivity.space_modulation.interp_method,
        )
        sigma_modulate_phase = fun_interp(
            coord_interp,
            modulation.conductivity.time_modulation.phase
            + modulation.conductivity.space_modulation.phase,
            modulation.conductivity.space_modulation.interp_method,
        )
        sigma_modulation = (
            sigma_modulate_amp.real.ravel() + 1j * sigma_modulate_phase.real.ravel() / np.pi
        )

    return modulation_frequency, eps_inf_modulation, sigma_modulation


def get_mat_comp_and_interp(mat, name_comp: str):
    """Find out the material along given component, and interp method.
    The variable `name_comp` is in the format "xx", etc.

    The material can be custom/non-custom, anisotropic/isotropic. For non-custom medium,
    use "nearest" interp method.
    """

    mat_comp = mat
    interp_method = "nearest"
    # interp method
    if isinstance(mat_comp, AbstractCustomMedium):
        interp_method = mat_comp._interp_method(  # pylint:disable=protected-access
            NAME_TO_IND[name_comp]
        )

    # mat component:
    # First, take care of custom meidum case
    # 1) custom anisotropic medium
    if isinstance(mat_comp, AbstractCustomMedium) and not mat_comp.is_isotropic:
        # `CustomMedium` might be anisotropic; to be deprecated in v3.0
        if isinstance(mat_comp, CustomMedium):
            mat_comp = mat_comp._medium
        mat_comp = mat_comp.components[name_comp]

    # Next, non-custom anisotropic medium
    if isinstance(mat_comp, AnisotropicMedium):
        mat_comp = mat_comp.components[name_comp]

    # the rest cases don't need special attention
    return mat_comp, interp_method


def structure_custom_medium_on_grid(  # pylint:disable=too-many-locals, too-many-statements
    structure: Structure, grid: Grid, span_inds: Numpy = None, subpixel_identifier: int = 0
) -> StructureWithCustomMediumData:
    """Returns ``StructureWithCustomMediumData`` that contains info for permittivity
    on the grids within union of ``span_inds`` and the bounding box of the structure.

    Parameters
    ----------
    structure : Structure
        The structure made of custom medium
    grid : Grid
        chunk_src_grid
    span_inds : Numpy, Optional
        If not ``None``, only interpolate permittivity over the grids inside the union of
        ``span_inds`` and the bounding box of the structure. If ``None``, inside the
        bounding box.
    """

    str_inds = grid._get_geo_inds(structure.geometry, span_inds)

    # handle structure outside domain (just set indexes min=max)
    for dim in range(3):
        if str_inds[dim][0] > str_inds[dim][1]:
            str_inds[dim][1] = str_inds[dim][0]

    eps_interp = {
        "inds_range": (ind_bound for ind_comp in str_inds for ind_bound in ind_comp),
    }

    # the number of points to be interpolated
    array_len = np.prod([np.diff(str_inds[pol]) for pol in range(3)])

    eps_inf_collected = np.zeros((array_len, 3))
    conductivity_collected = np.zeros((array_len, 3))
    modulation_frequency_collected = [0] * 3
    eps_inf_modulation_collected = [None] * 3
    conductivity_modulation_collected = [None] * 3
    subpixel_collected = [True] * 3
    poles_a_collected = [None] * 3
    poles_c_collected = [None] * 3

    # eps is colocated with E-field
    coord_eps = {"xx": grid.yee.E.x, "yy": grid.yee.E.y, "zz": grid.yee.E.z}
    if array_len > 0:
        for name_comp, coord_comp in coord_eps.items():
            # the grid coordiates where interpolation will be performed
            coord_comp = coord_comp.to_dict
            coord_interp = {
                comp: np.array(coord_comp[comp][slice(*str_inds[ind_comp])])
                for ind_comp, comp in enumerate("xyz")
            }
            coord_interp = Coords(**coord_interp)

            # material component
            mat_comp, interp_method = get_mat_comp_and_interp(structure._optical_medium, name_comp)

            # apply interpolation
            eps_inf_interp, sigma_interp, poles_interp = interpolated_isotropic_material_parameters(
                mat_comp, coord_interp, interp_method
            )
            if mat_comp.is_time_modulated:
                (
                    modulation_frequency_collected[NAME_TO_IND[name_comp]],
                    eps_inf_modulation_collected[NAME_TO_IND[name_comp]],
                    conductivity_modulation_collected[NAME_TO_IND[name_comp]],
                ) = interpolated_modulated_medium_parameters(mat_comp, coord_interp)

            if isinstance(mat_comp, AbstractCustomMedium):
                subpixel_collected[NAME_TO_IND[name_comp]] = mat_comp.subpixel

            ### post processing
            # process poles
            poles_a = None
            poles_c = None
            if poles_interp is not None:
                poles_a = []
                poles_c = []
                for a, c in poles_interp:
                    poles_a.append(a.ravel())
                    poles_c.append(c.ravel())
                poles_a = np.array(poles_a)
                poles_c = np.array(poles_c)

            # collect the interpolation result
            eps_inf_collected[:, NAME_TO_IND[name_comp]] = eps_inf_interp.ravel()
            conductivity_collected[:, NAME_TO_IND[name_comp]] = sigma_interp.ravel()
            poles_a_collected[NAME_TO_IND[name_comp]] = poles_a
            poles_c_collected[NAME_TO_IND[name_comp]] = poles_c

    eps_interp.update(
        {
            "eps_inf": eps_inf_collected,
            "conductivity": conductivity_collected,
            "poles_a": poles_a_collected,
            "poles_c": poles_c_collected,
            "subpixel": subpixel_collected,
            "subpixel_identifier": subpixel_identifier,
            "modulation_frequency": modulation_frequency_collected,
            "conductivity_modulation": conductivity_modulation_collected,
            "eps_inf_modulation": eps_inf_modulation_collected,
        }
    )
    return StructureWithCustomMediumData(**eps_interp)


def nonlinear_spec_frontend_to_backend(sim, medium):
    nonlinear_spec = {
        "numiters": 0,
        "freq0_set": 0,
        "freq0": 0,
        "n0_set": 0,
        "n0": 0,
        # chi3
        "chi3": 0,
        # kerr
        "n2": 0,
        # tpa
        "beta": 0,
        "tau": 0,
        "sigma": 0,
        "e_e": 0,
        "e_h": 0,
        "c_e": 0,
        "c_h": 0,
    }
    for model in medium._nonlinear_models:
        nonlinear_spec["numiters"] = medium._nonlinear_num_iters
        if isinstance(model, NonlinearSusceptibility):
            nonlinear_spec["chi3"] += model.chi3
        elif isinstance(model, KerrNonlinearity):
            nonlinear_spec["n2"] = model.n2
            if model.n0 is not None:
                nonlinear_spec["n0"] = model.n0
                nonlinear_spec["n0_set"] = 1
        elif isinstance(model, TwoPhotonAbsorption):
            nonlinear_spec["beta"] = model.beta
            nonlinear_spec["tau"] = model.tau
            nonlinear_spec["sigma"] = model.sigma
            nonlinear_spec["e_e"] = model.e_e
            nonlinear_spec["e_h"] = model.e_h
            nonlinear_spec["c_e"] = model.c_e
            nonlinear_spec["c_h"] = model.c_h
            if model.n0 is not None:
                nonlinear_spec["n0"] = model.n0
                nonlinear_spec["n0_set"] = 1
            if model.freq0 is not None:
                nonlinear_spec["freq0"] = model.freq0
                nonlinear_spec["freq0_set"] = 1
    return nonlinear_spec


def write_chunk_custom_medium(
    sim: Simulation,
    chunk_grid: Grid,
    chunk_file: h5py.File,
    mpirank: int,
    span_inds: Numpy = None,
):
    """Write the permittivity of structures made of custom medium inside the current chunk."""

    # Keep track of index of structures made of custom medium.
    # "0"is reserved for background medium for the possibility that it can be
    # custom medium; so all other structure indices should be +1
    istr_ind = []

    # for determining subpixel identifier
    full_medium_map = get_finalized_full_optical_medium_map(sim._finalized_optical_medium_map)

    # construct background structure; naively, one will take `sim.geometry`, but be
    # aware of PML layers.
    structures = [Structure(geometry=sim.simulation_geometry, medium=sim.medium)]
    structures += sim._finalized_volumetric_structures

    cgrp = chunk_file.create_group("custom_medium")
    for istr, sim_struct in enumerate(structures):
        mat = sim_struct._optical_medium
        if not (
            isinstance(mat, AbstractCustomMedium) or sim_struct._optical_medium.is_time_modulated
        ):
            continue

        istr_ind.append(istr)
        log.support(
            f"Setting up structure index {istr} made of custom/time modulated medium on rank {mpirank}."
        )

        subpixel_identifier = 0
        if isinstance(mat, AbstractCustomMedium) and mat.derived_from is not None:
            subpixel_identifier = full_medium_map[mat.derived_from]
        custom_medium_data = structure_custom_medium_on_grid(
            sim_struct, chunk_grid, span_inds=span_inds, subpixel_identifier=subpixel_identifier
        )

        sgrp = cgrp.create_group(f"custom_{istr:04d}")
        # subpixel identifier
        sgrp.create_dataset(
            "subpixel_identifier", data=np.array([subpixel_identifier]).astype(np.int32)
        )
        # subpixel
        sgrp.create_dataset("subpixel", data=custom_medium_data.subpixel)
        # eps_inf
        sgrp.create_dataset("eps_inf", data=custom_medium_data.eps_inf.astype(config.fp_type))
        # Conductivity
        sgrp.create_dataset("sigma", data=custom_medium_data.conductivity.astype(config.fp_type))
        # Indexes range
        sgrp.create_dataset(
            "inds_range", data=np.array(custom_medium_data.inds_range).astype(np.int32)
        )
        # poles
        sgrp.create_dataset("dispersive", data=custom_medium_data.dispersive)
        comp_list = "xyz"
        for ind, pole_a in enumerate(custom_medium_data.poles_a):
            if pole_a is not None:
                sgrp.create_dataset(
                    "pole_ar_" + comp_list[ind], data=np.real(pole_a).astype(config.fp_type)
                )
                sgrp.create_dataset(
                    "pole_ai_" + comp_list[ind], data=np.imag(pole_a).astype(config.fp_type)
                )
        for ind, pole_c in enumerate(custom_medium_data.poles_c):
            if pole_c is not None:
                sgrp.create_dataset(
                    "pole_cr_" + comp_list[ind], data=np.real(pole_c).astype(config.fp_type)
                )
                sgrp.create_dataset(
                    "pole_ci_" + comp_list[ind], data=np.imag(pole_c).astype(config.fp_type)
                )

        # time modulation
        sgrp.create_dataset(
            "modulation_frequency",
            data=np.array(custom_medium_data.modulation_frequency).astype(config.fp_type),
        )
        for ind in range(3):
            eps_modulate = custom_medium_data.eps_inf_modulation[ind]
            sigma_modulate = custom_medium_data.conductivity_modulation[ind]
            if eps_modulate is not None:
                sgrp.create_dataset(
                    "eps_modulate_amp_" + comp_list[ind],
                    data=np.real(eps_modulate).astype(config.fp_type),
                )
                sgrp.create_dataset(
                    "eps_modulate_phi_" + comp_list[ind],
                    data=np.imag(eps_modulate).astype(config.fp_type),
                )
            if sigma_modulate is not None:
                sgrp.create_dataset(
                    "sigma_modulate_amp_" + comp_list[ind],
                    data=np.real(sigma_modulate).astype(config.fp_type),
                )
                sgrp.create_dataset(
                    "sigma_modulate_phi_" + comp_list[ind],
                    data=np.imag(sigma_modulate).astype(config.fp_type),
                )

        # nonlinear
        if sim_struct.medium.nonlinear_spec is not None:
            nonlinear_spec = nonlinear_spec_frontend_to_backend(sim=sim, medium=sim_struct.medium)
            for key, val in nonlinear_spec.items():
                # for now, until custom nonlinearity is supported,
                # we just use a single-element array to encode the global value
                sgrp.create_dataset(
                    "nonlinear_spec_" + key, data=np.array([val]).astype(config.fp_type)
                )

    cgrp.create_dataset("istr_ind", data=np.array(istr_ind).astype(np.int32))
