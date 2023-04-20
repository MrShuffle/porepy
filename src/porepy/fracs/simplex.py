"""The ``frac.simplex`` module contains various functionalities to create simplex grids
with fractures."""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

import meshio
import numpy as np

import porepy as pp

from . import msh_2_grid
from .gmsh_interface import PhysicalNames

logger = logging.getLogger(__name__)


def triangle_grid_embedded(file_name: str) -> list[list[pp.Grid]]:
    """Creates a triangular 2D grid of a domain embedded in 3D space, without
    meshing the 3D volume.

    The resulting grid can be used in a DFN model. The grid will be fully
    conforming along intersections between fractures.

    This function produces a set of grids for fractures and lower-dimensional
    objects, but it does nothing to merge the grids. To create a
    :class:`~porepy.grids.md_grid.MixedDimensionalGrid`,
    use the function :class:`~porepy.fracs.meshing.subdomains_to_mdg` instead.

    Parameters:
        file_name: Filename for communication with gmsh.

            The config file for gmsh will be ``f_name.geo``, with the grid output
            to ``f_name.msh``.

    Returns:
        A nested list with length 3, where for each dimension 2 to 0 the respective
        sub-list contains instances of :class:`~porepy.grids.grid.Grid` with that
        dimension. If there are no grids of a specific dimension, the respective
        sub-list is empty.

    """

    if file_name[-4:] == ".geo" or file_name[-4:] == ".msh":
        file_name = file_name[:-4]

    out_file = file_name + ".msh"

    pts, cells, cell_info, phys_names = _read_gmsh_file(out_file)

    g_2d = msh_2_grid.create_2d_grids(
        pts,
        cells,
        is_embedded=True,
        phys_names=phys_names,
        cell_info=cell_info,
    )
    g_1d, _ = msh_2_grid.create_1d_grids(pts, cells, phys_names, cell_info)
    g_0d = msh_2_grid.create_0d_grids(pts, cells, phys_names, cell_info)

    grids: list[list[pp.Grid]] = [g_2d, g_1d, g_0d]  # type: ignore

    logger.info("\n")
    for g_set in grids:
        if len(g_set) > 0:
            s = (
                "Created "
                + str(len(g_set))
                + " "
                + str(g_set[0].dim)
                + "-d grids with "
            )
            num = 0
            for g in g_set:
                num += g.num_cells
            s += str(num) + " cells"
            logger.info(s)
    logger.info("\n")

    return grids


def triangle_grid_from_gmsh(
    file_name: str, constraints: Optional[np.ndarray] = None, **kwargs
) -> list[list[pp.Grid]]:
    """Creates a nested list of grids dimensions ``{2, 1, 0}``, starting from meshes
    created by gmsh.

    Parameters:
        file_name: Path to a ``*.msh``-file containing gmsh specifications.
        constraints: ``default=None``

            Indices of fracture lines that are constraints in the meshing,
            but should not have a lower-dimensional mesh.
        **kwargs: Optional keyword arguments for
            :func:`~porepy.fracs.msh_2_grid.create_1d_grids`

    Returns:
        A nested list with length 3, where for each dimension 2 to 0 the respective
        sub-list contains instances of :class:`~porepy.grids.grid.Grid` with that
        dimension. If there are no grids of a specific dimension, the respective
        sub-list is empty.

    """

    if constraints is None:
        constraints = np.empty(0, dtype=int)

    start_time = time.time()

    if file_name.endswith(".msh"):
        file_name = file_name[:-4]
    out_file = file_name + ".msh"

    pts, cells, cell_info, phys_names = _read_gmsh_file(out_file)

    # Create grids from gmsh mesh.
    logger.info("Create grids of various dimensions")
    g_2d = msh_2_grid.create_2d_grids(
        pts, cells, is_embedded=False, phys_names=phys_names, cell_info=cell_info
    )
    g_1d, _ = msh_2_grid.create_1d_grids(
        pts,
        cells,
        phys_names,
        cell_info,
        line_tag=PhysicalNames.FRACTURE.value,
        constraints=constraints,
        **kwargs,
    )
    g_0d = msh_2_grid.create_0d_grids(pts, cells, phys_names, cell_info)
    grids: list[list[pp.Grid]] = [g_2d, g_1d, g_0d]  # type: ignore

    logger.info(
        "Grid creation completed. Elapsed time " + str(time.time() - start_time)
    )

    for g_set in grids:
        if len(g_set) > 0:
            s = (
                "Created "
                + str(len(g_set))
                + " "
                + str(g_set[0].dim)
                + "-d grids with "
            )
            num = 0
            for g in g_set:
                num += g.num_cells
            s += str(num) + " cells"
            logger.info(s)

    return grids


def line_grid_from_gmsh(
    file_name: str, constraints: Optional[np.ndarray] = None, **kwargs
) -> list[list[pp.Grid]]:
    """Creates a nested list of grids with dimensions ``{1, 0}``, starting from meshes
    created by gmsh.

    Parameters:
        file_name: Path to a ``*.msh``-file containing gmsh specifications.
        constraints: ``default=None``

            Indices of fracture lines that are constraints in the meshing,
            but should not have a lower-dimensional mesh.
        **kwargs: Optional keyword arguments for
            :func:`~porepy.fracs.msh_2_grid.create_1d_grids`.

    Returns:
        A nested list with length 2, where for dimensions 1 and 0 the respective
        sub-list contains instances of :class:`~porepy.grids.grid.Grid` with that
        dimension. If there are no grids of a specific dimension, the respective
        sub-list is empty.

    """

    if constraints is None:
        constraints = np.empty(0, dtype=int)

    start_time = time.time()

    if file_name.endswith(".msh"):
        file_name = file_name[:-4]
    out_file = file_name + ".msh"

    pts, cells, cell_info, phys_names = _read_gmsh_file(out_file)

    # Create grids from gmsh mesh.
    logger.info("Create grids of various dimensions")
    g_1d, _ = msh_2_grid.create_1d_grids(
        pts,
        cells,
        phys_names,
        cell_info,
        line_tag=PhysicalNames.FRACTURE.value,
        constraints=constraints,
        **kwargs,
    )
    g_0d = msh_2_grid.create_0d_grids(pts, cells, phys_names, cell_info)
    grids: list[list[pp.Grid]] = [g_1d, g_0d]  # type: ignore

    logger.info(
        "Grid creation completed. Elapsed time " + str(time.time() - start_time)
    )

    for g_set in grids:
        if len(g_set) > 0:
            s = (
                "Created "
                + str(len(g_set))
                + " "
                + str(g_set[0].dim)
                + "-d grids with "
            )
            num = 0
            for g in g_set:
                num += g.num_cells
            s += str(num) + " cells"
            logger.info(s)

    return grids


def tetrahedral_grid_from_gmsh(
    file_name: str, constraints: Optional[np.ndarray] = None, **kwargs
) -> list[list[pp.Grid]]:
    """Creates a nested list of grids dimensions ``{3, 2, 1, 0}``, starting from meshes
    created by ``gmsh``.

    Parameters:
        file_name: Path to a ``*.msh``=file containing ``gmsh`` specifications.
        constraints: ``default=None``

            See argument ``constraints`` for
            :func:`~porepy.fracs.msh_2_grid.create_2d_grids`
        **kwargs: Currently supported keyword arguments are

            - ``'verbose``: If greater than 0, additional information on grids is
              logged.

    Returns:
        A nested list with length 4, where for dimensions 3 to 0 the respective
        sub-list contains instances of :class:`~porepy.grids.grid.Grid` with that
        dimension. If there are no grids of a specific dimension, the respective
        sub-list is empty.

    """

    start_time = time.time()
    # Verbosity level
    verbose = kwargs.get("verbose", 1)

    if file_name.endswith(".msh"):
        file_name = file_name[:-4]
    file_name = file_name + ".msh"

    pts, cells, cell_info, phys_names = _read_gmsh_file(file_name)

    # Call upon helper functions to create grids in various dimensions.
    # The constructors require somewhat different information, reflecting the
    # different nature of the grids.
    g_3d = msh_2_grid.create_3d_grids(pts, cells)
    g_2d = msh_2_grid.create_2d_grids(
        pts,
        cells,
        is_embedded=True,
        phys_names=phys_names,
        cell_info=cell_info,
        constraints=constraints,
    )

    g_1d, _ = msh_2_grid.create_1d_grids(pts, cells, phys_names, cell_info)
    g_0d = msh_2_grid.create_0d_grids(pts, cells, phys_names, cell_info)

    grids: list[list[pp.Grid]] = [g_3d, g_2d, g_1d, g_0d]  # type: ignore

    if verbose > 0:
        logger.info(
            "Grid creation completed. Elapsed time " + str(time.time() - start_time)
        )
        for g_set in grids:
            if len(g_set) > 0:
                s = (
                    "Created "
                    + str(len(g_set))
                    + " "
                    + str(g_set[0].dim)
                    + "-d grids with "
                )
                num = 0
                for g in g_set:
                    num += g.num_cells
                s += str(num) + " cells"
                logger.info(s)

    return grids


def _read_gmsh_file(
    file_name: str,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray], dict[int, str]]:
    """Auxiliary function to read a ``*.msh``-file, and convert the result to a format
    that is compatible with the porepy functionality for mesh processing.

    Parameters:
        file_name: Name of the file to be processed.

    Returns:
        A 4-tuple containing

        :obj:`~numpy.ndarray`: ``shape=(npt, dim)``
            Coordinates of all vertices in the grid, where ``npt`` is the number of
            vertices and ``dim`` the ambient dimension.
        :obj:`dict`:
            Mapping between cells of different shapes, and the indices of
            vertices constituting the cell wrapped in a numpy array.
        :obj:`dict`:
            Mapping between cells of different shapes, and the ``gmsh`` tags of each
            cell wrapped in a numpy array.
        :obj:`dict`:
            Mapping from ``gmsh`` tags to the physical names (strings) assigned in the
            ``*.geo``-file.

    """
    mesh = meshio.read(file_name)

    pts = mesh.points
    cells = mesh.cells
    cell_info = mesh.cell_data
    # Invert phys_names dictionary to map from physical tags to corresponding
    # physical names
    # The first
    phys_names = {v[0]: k for k, v in mesh.field_data.items()}

    # The API of meshio is constantly changing; this if-else is needed to take care
    # of different generations of meshio.
    if isinstance(cells, list):
        # This is tested for meshio v4
        # The cells are stored as a list of namedtuples, consisting of an attribute
        # 'type' which is the type of the cell (line, triangle etc.), and an attribute
        # 'data', which gives the vertex numbers for each cell.
        # We will convert this into a simpler dictionary, that maps the type to an
        # array of vertexes.
        # Moreover, the cell_info, which gives the tags of each cell, is stored in a
        # list, with ordering equal to that of the cells. This list will again be split
        # into a dictionary with the cell type as keys, and tags as values.

        # Initialize the dictionaries to be constructed
        tmp_cells: dict[str, Any] = {}
        tmp_info: dict[str, Any] = {}
        keys = set([cb.type for cb in cells])
        for key in keys:
            tmp_cells[key] = []
            tmp_info[key] = []

        # Loop simulatneously over cells and the cell info; process data
        for cb, info in zip(cells, cell_info["gmsh:physical"]):
            tmp_cells[cb.type].append(cb.data)
            tmp_info[cb.type].append(info)

        # Repack the data
        for k, v in tmp_cells.items():
            tmp_cells[k] = np.vstack([part for part in v])
        for k, v in tmp_info.items():
            tmp_info[k] = np.hstack([part for part in v])

        cells = tmp_cells
        cell_info = tmp_info
    else:
        # Meshio v2. May also work for v3?
        # This data format is much closer to what is used in the further processing in
        # porepy. The only thing we need to do is to dump a subdictionary level in
        # cell_info.
        for k, v in cell_info.items():
            cell_info[k] = v["gmsh:physical"]

    return pts, cells, cell_info, phys_names
