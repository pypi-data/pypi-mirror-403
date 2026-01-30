"""Subgrid class used for handling monitor grids, MPI chunking, and symmetries."""

from __future__ import annotations

from typing import List, Tuple, Union

import numpy as np
from tidy3d import Coords, Geometry, Grid
from tidy3d.components.base import Tidy3dBaseModel
from tidy3d.components.boundary import BlochBoundary, Periodic
from tidy3d.components.data.monitor_data import (
    FieldData,
    FieldTimeData,
    PermittivityData,
    MediumData,
)
from tidy3d.components.monitor import Monitor
from tidy3d.components.simulation import Simulation
from tidy3d.components.types import Numpy


class SubGrid(Tidy3dBaseModel):
    """A class defining a subgrid as a subspace of a global grid. The subspace is defined by the
    (beg, end) indexes in the global grid in each direction. These indexes can extend past
    the cell indexes in the global grid, in which case the subgrid is padded by applying either
    periodic or reflective boundaries at the global grid truncation, depending on the ``periodic``
    argument for each dimension. A halo size at each of the six sides of the subgrid can also
    be defined, which allows to distinguish between the full subgrid and its "inside".

    Parameters
    ----------
    global_grid : :class:`tidy3d.Grid`
        x,y,z coordinates of the boundaries between cells, defining the FDTD grid.
    span_inds : Tuple[Tuple[int, int]]
        The ``(beg, end)`` index into the global grid in each of the three dimensions.
    num_halos : Tuple[Tuple[int, int]], optional
        The halo width on each side for each dimension.
    periodic: Tuple[bool, bool, bool]:
        For each dimension, whether periodic or reflective boundaries should be applied if
        extending past the global grid domain.
    """

    global_grid: Grid
    span_inds: List[Tuple[int, int]]
    num_halos: List[Tuple[int, int]] = [(0, 0), (0, 0), (0, 0)]
    periodic: Tuple[bool, bool, bool] = (True, True, True)

    @property
    def grid(self) -> Grid:
        """The subgrid, computed from global_grid and span_inds."""

        grid, _ = self.grid_and_first_dual

        return grid

    @property
    def grid_and_first_dual(self) -> Grid:
        """The subgrid and first dual step, computed from global_grid and span_inds."""

        # If there is splitting along a given dimension, expand on negative side to retrieve enough
        # cells for computing dual step before halo cell. Otherwise, in C++ prerocess this dual
        # step will be computed based on periodically wrapping the grid, which is incorrect if
        # the current chunk does not have the entire grid along that dimension. Typically,
        # this causes no issues, but for fixed angle simulations we use not only fields from
        # halo cells, but also update coefficients. If the dual step before the halo cell
        # does not coincide with the corresponding dual step on the neighboring chunk,
        # that will also lead to a sligthly different update coefficient in the halo cell
        # compared to corresponding coefficient on the neighboring chunk. Which appears to be
        # sufficient to trigger an instability.
        #
        #   [need correct update coefficient here]
        #          |   [halo cell on (n+1)-th chunk]
        #          *   /
        #        o=|==o==|---o---|--o--|--
        #    --|-o-|--o--|===o===|
        #                    \
        #         [halo cell on n-th chunk]

        boundary_dict = {}
        dual_step_before_halo = -np.ones(3)
        for idim, (dim, periodic) in enumerate(zip("xyz", self.periodic)):
            ind_beg, ind_end = self.span_inds[idim]

            # extend if multiple chunks along this dimension
            multiple_chunks = self.num_halos[idim][0] > 0

            # ind_end + 1 because we're selecting boundaries, not cells
            grid_1d = self.global_grid.extended_subspace(
                idim, ind_beg - multiple_chunks, ind_end + 1, periodic
            )

            # compute the dual step before negative halo
            # and discard the additional cells
            if multiple_chunks:
                dual_step_before_halo[idim] = 0.5 * (grid_1d[1] - grid_1d[0])
                grid_1d = grid_1d[1:]

            boundary_dict[dim] = grid_1d

        return Grid(boundaries=Coords(**boundary_dict)), dual_step_before_halo

    def fold_inds_1d(self, inds, axis):
        """For a set of ``inds`` along ``axis`` of the global grid which may extend outside of the
        ``(0, num_cells)`` range, return a set of mapped indexed inside that range, using periodic
        or reflected mapping based on ``self.periodic`` along that axis."""

        folded_inds = np.copy(inds)
        num_cells = self.global_grid.num_cells[axis]

        if self.periodic[axis]:
            # Apply periodicity
            folded_inds = np.mod(folded_inds, num_cells)
        else:
            # Apply reflections at the boundaries until all indexes are inside
            while not (all(folded_inds >= 0) and all(folded_inds < num_cells)):
                folded_inds[folded_inds < 0] = -folded_inds[folded_inds < 0] - 1
                inds_out = folded_inds >= num_cells
                folded_inds[inds_out] = 2 * num_cells - folded_inds[inds_out] - 1

        return folded_inds

    def ginds_inside_1d(self, ginds: List[Numpy], include_halos: bool = True) -> List[Numpy]:
        """For an input list of three 1D arrays ``ginds`` of cells indexes in the global grid along
        each of the three axes, return a list of indexes that is inside the subgrid.

        Parameters
        ----------
        ginds : List[Numpy]
            Three arrays of indexes in each of the axes of the global grid.
        include_halos : bool, optional
            Whether to include the subgrid halos in the truncation.

        Returns
        -------
        inds_in : List[Numpy]
            The subset of the global grid indexes that are inside the subgrid can be obtained, for
            each dimesnion, as ``ginds[dim][inds_in[dim]]``.

        Note
        ----
            Extension is **not** applied. For example, if the subgrid extends past the edge of the
            global grid on the right, but does not include the edge on the left, the global grid
            index 0 will not be counted as "inside" the subgrid.
        """

        inds_beg = np.array(self.span_inds)[:, 0]
        inds_end = np.array(self.span_inds)[:, 1]

        if not include_halos:
            inds_beg += np.array(self.num_halos)[:, 0]
            inds_end -= np.array(self.num_halos)[:, 1]

        inds_in_1d = []
        for ginds_1d, ind0, ind1 in zip(ginds, inds_beg, inds_end):
            inds_in = np.where((ginds_1d >= ind0) & (ginds_1d < ind1))[0]
            inds_in_1d.append(inds_in)

        return inds_in_1d

    def sinds_to_ginds_1d(self, sinds: List[Numpy]) -> List[Numpy]:
        """For a list of three 1D arrays ``sinds`` of cells indexes in the subgrid, return a list of
        arrays with the same shape with cell indexes in the global grid. Extension is applied for
        indexes outside the global grid range."""

        ginds = []
        for dim, sinds_1d in enumerate(sinds):
            # Offset to global grid coordinates
            ginds_1d = sinds_1d + self.span_inds[dim][0]
            # Fold within (0, num_cells)
            ginds_1d = self.fold_inds_1d(ginds_1d, dim)

            ginds.append(ginds_1d)

        return ginds

    def ginds_to_sinds_1d(self, ginds: List[Numpy]) -> List[Numpy]:
        """For a list of three 1D arrays ``ginds`` of cells indexes in the global grid, return a
        list of arrays of cell indexes in the subgrid. If any indexes are outside the subgrid range
        they are excluded, so the new array can have a smaller size than the input one.
        Also see note in ginds_inside."""

        # Truncate indexes to within the subgrid region
        inds_in = self.ginds_inside_1d(ginds)
        # Offset to subgrid indexing
        sinds = [ginds[dim][inds_in[dim]] - self.span_inds[dim][0] for dim in range(3)]

        return sinds

    def ginds_inside(self, ginds: Numpy, include_halos: bool = True) -> Numpy:
        """For an array ``ginds`` of shape (Np, 3) of cells indexes in the global grid, return an
        indexing into the subset that is inside the subgrid, with or without the halo.

        Parameters
        ----------
        ginds : Numpy
            Indexes in the global grid.
        include_halos : bool, optional
            Whether to include the subgrid halos in the truncation.

        Returns
        -------
        inds_in : Numpy
            The subset of the global grid indexes that are inside the subgrid can be obtained as
            ``ginds_in = ginds[inds_in]``.

        Note
        ----
            Extension is **not** applied. For example, if the subgrid extends past the edge of the
            global grid on the right, but does not include the edge on the left, the global grid
            index 0 will not be counted as "inside" the subgrid.
        """

        inds_beg = np.array(self.span_inds)[:, 0]
        inds_end = np.array(self.span_inds)[:, 1]

        if not include_halos:
            inds_beg += np.array(self.num_halos)[:, 0]
            inds_end -= np.array(self.num_halos)[:, 1]

        inds_in = np.prod(ginds >= inds_beg, axis=1).astype(bool)
        inds_in *= np.prod(ginds < inds_end, axis=1).astype(bool)

        return inds_in

    def sinds_to_ginds(self, sinds: Numpy) -> Numpy:
        """For an array ``sinds`` of shape (Np, 3) of cells indexes in the subgrid, return an array
        of the same shape with cell indexes in the global grid. Periodicity is applied for indexes
        outside the global grid range."""

        # Offset to global grid coordinates
        ginds = sinds + np.array(self.span_inds)[:, 0]
        # Fold within (0, num_cells) range
        for axis in range(3):
            ginds[:, axis] = self.fold_inds_1d(ginds[:, axis], axis)

        return ginds

    def ginds_to_sinds(self, ginds: Numpy) -> Tuple[Numpy, Numpy]:
        """For an array ``ginds`` of shape (Np, 3) of cells indexes in the global grid, return an
        array of cell indexes in the subgrid. If any indexes are outside the subgrid range they are
        excluded, so the new array can have a smaller size than the input one. Also see note in
        ginds_inside."""

        # Truncate indexes to within the subgrid region
        inds_in = self.ginds_inside(ginds)
        # Offset to subgrid indexing
        sinds = ginds[inds_in] - np.array(self.span_inds)[:, 0]

        return sinds

    def discretize(
        self,
        box: Geometry,
        extend: bool = False,
        include_halos: bool = False,
        relax_precision: bool = False,
    ) -> SubGrid:
        """Like Simulation.discretize, but returns a SubGrid instead of a Grid, and optionally the
        halos of the global SubGrid can be excluded."""

        span_inds = self.grid.discretize_inds(box, extend=extend, relax_precision=relax_precision)
        # convert tuples to lists
        span_inds = [[sinds[0], sinds[1]] for sinds in span_inds]

        if not include_halos:
            for dim in range(3):
                span_inds[dim][0] = max(span_inds[dim][0], self.num_halos[dim][0])
                num_cells = self.span_inds[dim][1] - self.span_inds[dim][0]
                span_inds[dim][1] = min(span_inds[dim][1], num_cells - self.num_halos[dim][1])
                # Avoid ind_start > ind_stop
                span_inds[dim][1] = max(span_inds[dim][1], span_inds[dim][0])

        # trim extra cells that are not part of self.grid
        if extend and include_halos:
            for dim in range(3):
                if span_inds[dim][0] < 0:
                    span_inds[dim][0] = 0
                num_cells = self.span_inds[dim][1] - self.span_inds[dim][0]
                if span_inds[dim][1] > num_cells:
                    span_inds[dim][1] = num_cells

        return SubGrid(global_grid=self.grid, span_inds=span_inds)


def get_subgrid_inds(chunk_grid: SubGrid):
    """Get the list of indices for a given subgrid."""
    inds_1d = [np.arange(0, npts) for npts in chunk_grid.grid.num_cells]
    inds_1d = chunk_grid.sinds_to_ginds_1d(inds_1d)
    inds_mesh = np.meshgrid(*inds_1d, indexing="ij")
    return np.stack([inds.ravel() for inds in inds_mesh], axis=1)


def computational_grid(sim: Simulation, truncate_sym=True, pbc_ghost: bool = False) -> SubGrid:
    """FDTD grid as a subgrid of the simulation grid. This is a bit misleading as it is actually
    **larger** than the simulation grid, with ghost pixels potentially added for boundary
    conditions. Optionally, it can also be truncated to the main symmetry quadrant.

    Parameters
    ----------
    sim : Simulation
        A Tidy3D simulation.
    truncate_sym : bool
        Whether the computational grid should be truncated to the main symmetry quadrant. This is
        how it should be supplied to the solver.
    pbc_ghost : bool
        Whether to add a ghost pixel for Periodic boundaries. For the solver, the ghost pixel should
        be off (default), but when computing field coordinates in post-processing, it is convenient
        to turn it on.

    Returns
    -------
    SubGrid
        The computational grid with ghost pixels due to boundary conditions, and symmetry
        truncation, if requested.
    """

    periodic = list(sim._periodic)
    span_inds = []
    zipped = zip(sim.boundary_spec.to_list, sim.symmetry, sim.grid.num_cells)
    for idim, (boundary1d, sym, num_cells) in enumerate(zipped):
        if sym != 0:
            periodic[idim] = False
            if truncate_sym:
                span_inds.append((num_cells // 2 - 1, num_cells + 1))
            else:
                span_inds.append((-1, num_cells + 1))
        elif isinstance(boundary1d[0], Periodic) and not pbc_ghost:
            # no ghost pixels for periodic boundary conditions if not requested
            span_inds.append((0, num_cells))
        else:
            span_inds.append((-1, num_cells + 1))

    return SubGrid(global_grid=sim.grid, span_inds=span_inds, periodic=periodic)


def monitor_grid_inds(sim: Simulation, monitor: Monitor):
    """Compute the symmetry-truncated computational grid, the monitor grid as a subgrid of the
    full computational grid, and the indexes into the symmetry-truncated grid at which the monitor
    records values (e.g. after symmetries and downsampling have been applied).

    As opposed to the preprocessing, here we add a ghost pixel for all boundaries (which is to say,
    we add a ghost pixel for Periodic boundaries, since all other ones get one anyway). This helps
    us use the indexes directly to get the coordinates of the recorded fields.
    """

    comp_grid_full = computational_grid(sim, truncate_sym=False, pbc_ghost=True)
    comp_grid = computational_grid(sim, pbc_ghost=True)
    mnt_grid = monitor_subgrid(sim, monitor, comp_grid_full)
    inds_comp_grid = indexes_record(sim, monitor, mnt_grid, wrap_bloch=False)

    return (comp_grid, mnt_grid, inds_comp_grid)


def monitor_subgrid(sim: Simulation, monitor: Monitor, comp_grid: SubGrid) -> SubGrid:
    """Compute a monitor subgrid of the computational grid that spans a large enough region to be
    able to interpolate everywhere within the monitor geometry.

    Parameters
    ----------
    sim : Simulation
        Original simulation.
    monitor : Monitor
        Monitor to compute a subgrid for.
    comp_grid : SubGrid
        A SubGrid of the original simulation grid. This should typically be obtained through
        the setup.py::computational_grid function. For typical uses in combination with
        ``indexes_record`` below, the computational grid should not be symmetry-truncated.

    Returns
    -------
    SubGrid
        A SubGrid of the monitor into the provided computational grid.
    """

    span_inds = sim._discretize_inds_monitor(monitor)

    # Span of the monitor grid in the computational grid
    mnt_span_inds = []
    for inds, comp_span in zip(span_inds, comp_grid.span_inds):
        mnt_span_inds.append((inds[0] - comp_span[0], inds[1] - comp_span[0]))

    # Monitor subgrid of the computational gird
    return SubGrid(global_grid=comp_grid.grid, span_inds=mnt_span_inds)


def indexes_record(sim: Simulation, monitor: Monitor, mnt_grid: SubGrid, wrap_bloch: bool = True):
    """Compute the indexes into the symmetry-truncated computational grid (i.e. the grid used by
    the solver) at which the monitor should record field values. This takes symmetries,
    downsampling, and boundary conditions into account.

    Parameters
    ----------
    sim : Simulation
        Original simulation.
    monitor : Monitor
        Monitor to compute the indexes for.
    mnt_grid : SubGrid
        SubGrid of the monitor into a computational grid as obtained from monitor_subgrid.
    wrap_bloch : bool, optional
        Whether to wrap indexes that extend past a Bloch boundary periodically. This is needed for
        passing the indexes to the solver, but can be turned off to e.g. get the correct grid
        locations without wrapping.

    Returns
    -------
    List[Numpy]
        Indexes into the symmetry-truncated computational grid along the three axes. This assumes
        that the global grid of ``mnt_grid`` was a computational grid that was *not*
        symmetry-truncated.
    """

    # Indexes in the monitor subgrid at which to store data
    inds_mnt_grid = [
        monitor.downsample(np.arange(num_cells), axis=dim)
        for dim, num_cells in enumerate(mnt_grid.grid.num_cells)
    ]

    # Indexes in the full computational grid at which to store data
    inds_comp_full = mnt_grid.sinds_to_ginds_1d(inds_mnt_grid)

    # Fix based on boundaries and move indexing to symmetry-truncated computational grid
    boundaries = sim.boundary_spec.to_list
    inds_comp_grid = []
    for dim, (sym, boundary, inds_dim) in enumerate(zip(sim.symmetry, boundaries, inds_comp_full)):
        if sym != 0:
            # If monitor extends outside of simulation domain on the left, drop the symmetry
            # ghost pixel on that side, as there is not enough data on the right to fully cover it.
            # However, relevant values to be able to colocate to the simulation boundary on the left
            # after the grid is expanded will still be present.
            inds_dim = inds_dim[inds_dim != 0]
            # Move indexes from full comp grid to symmetry-truncated comp grid
            inds_dim -= sim.grid.num_cells[dim] // 2
            # Flip indexes to the main symmetry quadrant. In the symmetry-restricted comp grid,
            # index 0 is in the extra pixel on the left needed for the symmetry application.
            flip_inds = inds_dim < 1
            inds_dim[flip_inds] = -inds_dim[flip_inds] + 2

            # If the monitor is not colocating, and potentially down-sampling, we also need
            # the pixel on the left of the flipped pixels for components that live at yee grid
            # centers. Potential duplication of indexes (e.g. without downsampling) is handled
            # by taking the unique elements below.
            if not monitor.colocate:
                # Some edge cases have to be fixed for non-colocating monitors due to the fact that
                # primal-grid components and dual-grid components have a different mapping.
                # Above, the primal grid mapping was used, so if monitors colocate, all is good.
                # Potential duplication of indexes is handled by taking the unique elements below.
                if monitor.size[dim] == 0 and flip_inds.size > 0:
                    # Extra pixel on the left for 2D monitors that need pixels from the left of
                    # the symmetry plane
                    inds_dim = np.concatenate((inds_dim, inds_dim - 1))
                elif monitor.interval_space[dim] > 1:
                    # Extra pixel to the left for down-sampling, for pixels that are to the left of
                    # the symmetry plane.
                    inds_dim = np.append(inds_dim, inds_dim[flip_inds] - 1)

            # Take unique indexes only (may have been doubled due to symmetry)
            inds_dim = np.unique(inds_dim)

        if wrap_bloch and isinstance(boundary[0], BlochBoundary):
            # For Bloch boundaries, the indexes at domain edges need to be wrapped to store
            # fields periodically, as the Bloch phase is not applied to all field components in the
            # Bloch ghost pixel during the solver run. The Bloch phase is instead then applied
            # in the postprocessing in load.py.
            if inds_dim[0] == 0:
                # this monitor touches the minus edge of the domain along this dim
                inds_dim[0] = sim.grid.num_cells[dim]
            if inds_dim[-1] == sim.grid.num_cells[dim] + 1:
                # this monitor touches the plus edge of the domain along this dim
                inds_dim[-1] = 1

        inds_comp_grid.append(inds_dim)

    return inds_comp_grid


def snap_zero_dim(
    sim: Simulation, field_data: Union[PermittivityData, MediumData, FieldData, FieldTimeData]
) -> Union[PermittivityData, MediumData, FieldData, FieldTimeData]:
    """Colocate fields to exact location along dimensions where monitor or simulation size is 0.
    If there are no such dimensions, the monitor grid should already be equivalent to
    ``sim._discretize_grid_monitor(field_data.monitor)``. If there are, apart from the snapping the
    data we also overwrite ``grid_expanded`` using that.
    """

    colocate_coords = {}
    for dim, axis in enumerate("xyz"):
        if sim.grid.num_cells[dim] == 1:
            # Simulation itself is zero-dim along this direction
            colocate_coords[axis] = [sim.center[dim]]
        elif field_data.monitor.size[dim] == 0:
            # Monitor is zero-dim along this direction
            center = field_data.monitor.center[dim]
            if sim.symmetry[dim] != 0 and center < sim.center[dim]:
                center = 2 * sim.center[dim] - center
            colocate_coords[axis] = [center]
    if len(colocate_coords) == 0:
        return field_data

    new_fields = {"grid_expanded": sim.discretize_monitor(field_data.monitor)}
    for field_name, scalar_data in field_data.field_components.items():
        dtype = scalar_data.dtype
        tmp_arr = scalar_data.interp(**colocate_coords).astype(dtype)
        new_fields[field_name] = type(scalar_data)(tmp_arr.values, coords=tmp_arr.coords)

    return field_data.updated_copy(**new_fields, deep=False)
