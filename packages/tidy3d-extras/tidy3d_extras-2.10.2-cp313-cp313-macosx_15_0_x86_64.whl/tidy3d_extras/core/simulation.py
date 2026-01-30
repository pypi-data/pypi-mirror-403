"""Backend version of the frontend simulation class."""

import json
from typing import Dict, List, Tuple

import numpy as np
import pydantic.v1 as pd
from tidy3d import (
    AnisotropicMedium,
    Box,
    ClipOperation,
    Cylinder,
    EMESimulation,
    FullyAnisotropicMedium,
    Geometry,
    GeometryGroup,
    Medium,
    PECMedium,
    PMCMedium,
    PolySlab,
    Simulation,
    Sphere,
    SurfaceImpedance,
    Transformed,
    TriangleMesh,
)
from tidy3d.components.base import Tidy3dBaseModel
from tidy3d.components.geometry.utils import flatten_groups
from tidy3d.components.structure import Structure
from tidy3d.components.medium import (
    AbstractCustomMedium,
    AnisotropicMediumFromMedium2D,
    DispersiveMedium,
    LossyMetalMedium,
)
from tidy3d.components.types import Numpy
from tidy3d.config import config as frontend_config
from tidy3d.constants import MU_0, SECOND, fp_eps
from tidy3d.exceptions import SetupError

from .config import config
from .subgrid import SubGrid
from .custom_medium import nonlinear_spec_frontend_to_backend

# materials that only need to write type to json
MED_WRITE_TYPE_ONLY = ["PEC", "Custom", "PMC"]

FIXED_ANGLE_THRESHOLD = fp_eps


def build_geometry_dict(geometry: Geometry, made_of_2dmaterial: bool) -> Dict:
    """Create dictionary of the geometry-specific fields for each Geometry class.
    Compute normal_axis if it's made of 2d material.
    """
    if isinstance(geometry, Box):
        result = {
            "type": "Box",
            "x_cent": geometry.center[0],
            "y_cent": geometry.center[1],
            "z_cent": geometry.center[2],
            "x_span": geometry.size[0],
            "y_span": geometry.size[1],
            "z_span": geometry.size[2],
        }
    elif isinstance(geometry, Sphere):
        result = {
            "type": "Sphere",
            "x_cent": geometry.center[0],
            "y_cent": geometry.center[1],
            "z_cent": geometry.center[2],
            "radius": geometry.radius,
        }
    elif isinstance(geometry, Cylinder):
        result = {
            "type": "Cylinder",
            "x_cent": geometry.center[0],
            "y_cent": geometry.center[1],
            "z_cent": geometry.center[2],
            "axis": ["x", "y", "z"][geometry.axis],
            "radius": geometry.radius,
            "height": geometry.finite_length_axis,
            "sidewall_angle": geometry.sidewall_angle,
            "reference_plane": geometry.reference_plane,
        }
    elif isinstance(geometry, PolySlab):
        result = {
            "type": "PolySlab",
            "vertices": geometry.middle_polygon,
            "z_cent": geometry.center_axis,
            "z_size": geometry.finite_length_axis,
            "sidewall_angle": geometry.sidewall_angle,
            "dilation": 0,  # geometry.middle_polygon is already dilated
            "axis": "xyz"[geometry.axis],
        }
    elif isinstance(geometry, TriangleMesh):
        result = {
            "type": "TriangleMesh",
            "vectors": geometry.triangles,
        }
    elif isinstance(geometry, ClipOperation):
        result = {
            "type": "ClipOperation",
            "operation": geometry.operation,
            "operand_a": build_geometry_dict(geometry.geometry_a, made_of_2dmaterial),
            "operand_b": build_geometry_dict(geometry.geometry_b, made_of_2dmaterial),
        }
    elif isinstance(geometry, GeometryGroup):
        result = {
            "type": "GeometryGroup",
            "geometries": [build_geometry_dict(g, made_of_2dmaterial) for g in geometry.geometries],
        }
    elif isinstance(geometry, Transformed):
        result = {
            "type": "Transformed",
            "transform": geometry.transform,
            "geometry": build_geometry_dict(geometry.geometry, made_of_2dmaterial),
        }
    else:
        result = {}

    # default to z
    if len(result) > 0:
        normal_axis = 2
        if made_of_2dmaterial:
            normal_axis = geometry._normal_2dmaterial
        result.update({"normal_axis": normal_axis, "2dmaterial": int(made_of_2dmaterial)})
    return result


class BackendSimulation(Tidy3dBaseModel):
    """Backend simulation class."""

    class Config(Simulation.Config):
        """Sets a local config for :class:`BackendSimulation` objects to make them mutable."""

        frozen = False
        allow_mutation = True
        extra = "allow"

    courant_scaling: float = pd.Field(
        None,
        title="Courant number scaling rate",
        description="When conformal mesh is applied, courant number is "
        "scaled down depending on `conformal_mesh_spec`.",
    )

    time_step: float = pd.Field(
        None,
        title="Simulation time step",
        description="Simulation time step to be written to file for the solver.",
        units=SECOND,
    )

    total_time_steps: int = pd.Field(
        None,
        title="Number of time steps",
        description="Number of time steps to be written to file for the solver.",
    )

    struct_list: List[Dict] = pd.Field(
        None,
        title="Structure list",
        description="List of structures in solver-compatible format.",
    )

    source_time_list: List[Dict] = pd.Field(
        None,
        title="Additional properties of source time",
        description="List of additional properties of source time.",
    )

    medium_list: List[Dict] = pd.Field(
        None,
        title="Medium list",
        description="List of media in solver-compatible format.",
    )

    monitor_list: List[Dict] = pd.Field(
        None,
        title="Structure list",
        description="List of monitors in solver-compatible format.",
    )

    periodic_boundary: List[bool] = pd.Field(
        [False, False, False],
        title="Periodic boundary condition",
        description="Whether periodic boundary condition is applied in x/y/z direction.",
    )

    fixed_angle_axis: int = pd.Field(
        -1,
        title="Fixed Angle Propagation Axis",
        description="Fixed Angle Propagation Axis.",
    )

    fixed_angle_dir: List[float] = pd.Field(
        [0, 0, 0],
        title="Fixed Angle Direction",
        description="Fixed Angle Direction (scaled by the background real(n)).",
    )

    fixed_angle_center: List[float] = pd.Field(
        [0, 0, 0],
        title="Fixed Angle Center",
        description="Fixed Angle Center.",
    )

    simulation_bounds: Tuple[Tuple[float, float, float], Tuple[float, float, float]] = pd.Field(
        None,
        title="Simulation bounds including the PML regions",
        description="Simulation bounds including the PML regions.",
    )

    @staticmethod
    def parse_material_each_component(sim: Simulation, medium) -> Tuple[float, float, List[float]]:
        """For an isotropic medium, or a component of anisotropic medium,
        return (permittivity, conductivity, pole). Simple return ``None`` for PECmedium.
        """
        if isinstance(sim._subpixel.lossy_metal, SurfaceImpedance) and isinstance(
            medium, LossyMetalMedium
        ):
            # poles are for fitted Z/(-j omega); we also need to pass the fitted eps_inf,
            # which is included as the last pole.
            # We normalize it by MU_0, so that the final term is relative permeability.
            poles = []
            for a, c in medium.scaled_surface_impedance_model.poles:
                poles.append([a.real, a.imag, c.real / MU_0, c.imag / MU_0])
            poles.append([medium.scaled_surface_impedance_model.eps_inf / MU_0, 0, 0, 0])
            return (medium.permittivity, medium.conductivity, poles)
        if isinstance(medium, Medium):
            return (medium.permittivity, medium.conductivity, [])
        if isinstance(medium, DispersiveMedium):
            poles = []
            for a, c in medium.pole_residue.poles:
                poles.append([a.real, a.imag, c.real, c.imag])
            return (medium.pole_residue.eps_inf, 0, poles)
        return None, None, None

    @staticmethod
    def parse_material_type(medium) -> str:
        """pase material type for backend processing."""
        if isinstance(medium, LossyMetalMedium):
            return "LossyMetal"
        if isinstance(medium, PECMedium):
            return "PEC"
        if isinstance(medium, PMCMedium):
            return "PMC"
        if isinstance(medium, AbstractCustomMedium) or medium.is_time_modulated:
            return "Custom"
        if isinstance(medium, FullyAnisotropicMedium):
            return "FullyAnisotropic"
        if isinstance(medium, AnisotropicMedium):
            return "Anisotropic"
        return "Medium"

    @staticmethod
    def _get_background_n(source: Box, sim: Simulation, freqs: Numpy, axis: int):
        """Get background complex permittivity."""
        # Sample the permittivity at a single point only, but make sure it's within the simulation.
        src_grid = sim.discretize(source)
        single_point_grid = SubGrid(global_grid=src_grid, span_inds=[(0, 1) for i in range(3)])
        coord_key = ["Ex", "Ey", "Ez"][axis]
        background_n = np.zeros(freqs.size, dtype=config.cfp_type)
        for freq_id, freq in enumerate(freqs):
            # turn off subpixel for this
            use_local_subpixel = frontend_config.simulation.use_local_subpixel
            frontend_config.simulation.use_local_subpixel = False
            eps = sim.epsilon_on_grid(freq=freq, coord_key=coord_key, grid=single_point_grid.grid)
            frontend_config.simulation.use_local_subpixel = use_local_subpixel
            # We only use sim.medium in order to access the correct eps to nk conversion
            nk_medium = sim.medium.eps_complex_to_nk(eps.values)
            background_n[freq_id] = np.squeeze(nk_medium[0]) + 1j * np.squeeze(nk_medium[1])

        return background_n

    @staticmethod
    def _compute_fixed_angle_dir(sim: Simulation):
        """Compute fixed angle parameters:
        - the propagation axis,
        - the direction vector scaled by background n, and
        - the center of the source
        """
        fixed_angle_sources = sim._fixed_angle_sources
        if len(fixed_angle_sources) > 0:
            # if there are more than one fixed angle sources
            # frontend makes sure they are consistent
            # so we can consider just the first one
            src = fixed_angle_sources[0]
            background_n = BackendSimulation._get_background_n(
                source=src,
                sim=sim,
                freqs=np.array([src.source_time._freq0]),
                axis=src._injection_axis,
            )[0]
            fixed_angle_dir = np.array(src._dir_vector)
            fixed_angle_dir[np.abs(fixed_angle_dir) < FIXED_ANGLE_THRESHOLD] = 0
            fixed_angle_dir[src._injection_axis] = 0
            fixed_angle_dir *= np.real(background_n)

            return src._injection_axis, list(fixed_angle_dir), src.center

        return -1, [0, 0, 0], [0, 0, 0]

    def set_extra_fields(self, sim: Simulation):
        """Convert all Structure objects to a list of text-defined geometries,
        and all the corresponding Medium objects to a list of text-defined materials.
        Also sets other extra fields needed by the solver.
        """

        # additional source time properties
        self.source_time_list = []
        for source in sim.sources:
            self.source_time_list.append({"freq0": source.source_time._freq0})
        # subpixel methods
        self.subpixel_method = sim._subpixel

        self.courant_scaling = sim.scaled_courant / sim.courant
        self.courant = sim.scaled_courant
        self.time_step = sim.dt
        self.total_time_steps = sim.num_time_steps
        self.fixed_angle_axis, self.fixed_angle_dir, self.fixed_angle_center = (
            self._compute_fixed_angle_dir(sim=sim)
        )

        # periodic boundary and sim bounds
        self.periodic_boundary = list(sim._periodic)
        self.simulation_bounds = sim.simulation_bounds

        self.medium_list = []
        self.struct_list = []
        self.monitor_list = []

        volumetric_structures = sim._finalized_volumetric_structures
        medium_map = sim._finalized_optical_medium_map

        # bkg medium
        sim_optical_medium = Structure._get_optical_medium(sim.medium)
        if sim_optical_medium != Medium():
            self.struct_list.append(
                {
                    "name": "background",
                    "mat_index": medium_map[sim_optical_medium],
                    "str_index": 0,
                    "type": "Box",
                    "x_cent": 0,
                    "y_cent": 0,
                    "z_cent": 0,
                    "x_span": 1e10,
                    "y_span": 1e10,
                    "z_span": 1e10,
                }
            )

        for medium, imed in medium_map.items():
            med = {"name": f"mat_{imed}"}
            # find out material type
            med_type = self.parse_material_type(medium)
            med.update({"type": med_type})

            # no need to set permittivity etc. for those materials
            if med_type in MED_WRITE_TYPE_ONLY:
                self.medium_list.append(med)
                continue

            # set permittivity etc. values
            permittivity = []
            conductivity = []
            poles = []

            if med_type == "FullyAnisotropic":
                permittivity.extend(np.ravel(medium.permittivity))
                conductivity.extend(np.ravel(medium.conductivity))
            elif med_type == "Anisotropic":
                comp_types = []
                for medium_comp in [medium.xx, medium.yy, medium.zz]:
                    (
                        permittivity_comp,
                        conductivity_comp,
                        pole_comp,
                    ) = self.parse_material_each_component(sim, medium_comp)
                    medium_comp_type = self.parse_material_type(medium_comp)
                    permittivity.append(permittivity_comp)
                    conductivity.append(conductivity_comp)
                    poles.append(pole_comp)
                    comp_types.append(medium_comp_type)
                med.update({"comp_types": comp_types})
            else:
                (
                    permittivity_comp,
                    conductivity_comp,
                    pole_comp,
                ) = self.parse_material_each_component(sim, medium)
                permittivity = [permittivity_comp for _ in range(3)]
                conductivity = [conductivity_comp for _ in range(3)]
                poles = [pole_comp for _ in range(3)]

            med.update(
                {
                    "permittivity": permittivity,
                    "conductivity": conductivity,
                    "poles": poles,
                }
            )
            if medium.nonlinear_spec is not None:
                nonlinear_spec = nonlinear_spec_frontend_to_backend(sim=sim, medium=medium)
                med.update({"nonlinear_spec": nonlinear_spec})

            self.medium_list.append(med)

        for str_ind, structure in enumerate(volumetric_structures):
            str_optical_medium = structure._optical_medium
            mat_index = medium_map[str_optical_medium]
            # 2d material
            made_of_2dmaterial = isinstance(str_optical_medium, AnisotropicMediumFromMedium2D)
            # GeometryGroup and ClipOperation(operation="union", ...) can be flattened to improve
            # performance. Transformed groups can also be flattened by applying the cumulative
            # transform to each geometry
            self.struct_list.extend(
                {
                    "name": structure.name,
                    "mat_index": mat_index,
                    "str_index": str_ind + 1,
                    **build_geometry_dict(geometry, made_of_2dmaterial),
                }
                for geometry in flatten_groups(structure.geometry, flatten_transformed=True)
            )

        for monitor in sim.monitors:
            self.monitor_list.append(monitor._to_solver_monitor.dict())

    @staticmethod
    def backend_sim_to_json(sim: Simulation, file_name: str):
        """Make a backend simulation object, process it, and write to json."""
        # convert to FDTD for old sim json
        if isinstance(sim, Simulation):
            pass
        elif isinstance(sim, EMESimulation):
            sim = sim._as_fdtd_sim
        else:
            raise SetupError("Simulation type not supported for backend sim.")
        sim_backend = BackendSimulation()
        sim_backend.set_extra_fields(sim)

        json_string_sim = sim._json(exclude={"structures", "monitors"}, indent=None)
        json_string_simbck = sim_backend._json(indent=None)

        sim_dict = json.loads(json_string_sim)
        sim_dict["run_time"] = sim._run_time
        simbck_dict = json.loads(json_string_simbck)
        simbck_dict.pop("type")
        simbck_dict.update(sim_dict)

        with open(file_name, "w", encoding="utf-8") as file_handle:
            json.dump(simbck_dict, file_handle, indent=4)
