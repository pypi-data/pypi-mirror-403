import numpy as np

# from pyvista import CellType, UnstructuredGrid

__all__ = ["tetcube", "tetdomain", "tetgrid", "tetmesh", "tetplot"]

tetcube = (
    (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0),
        (1.0, 1.0, 0.0),
        (1.0, 1.0, 1.0),
        (0.0, 1.0, 1.0),
    ),
    (
        (1, 2, 3, 5),
        (2, 3, 5, 6),
        (0, 1, 3, 5),
        (3, 5, 6, 7),
        (3, 4, 5, 7),
        (0, 3, 4, 5),
    ),
)


def tetgrid(
    shape: int | tuple, extent=(0, 1, 0, 1, 0, 1)
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a regular grid of (nx, ny, nz) tesselated cubes.

    Note that a single cube will produce 8 vertices and 5 tetras,
    the total number of tetras equals 5*nx*ny*nz

    Args:
        shape (int or tuple of ints): shape of the grid, e.g., (3, 3, 3) or 3.
        extent (tuple, optional): Extent of the grid as (xmin, xmax, ymin, ymax, zmin, zmax). Defaults to (0, 1, 0, 1, 0, 1).

    Returns:
        tuple[np.ndarray, np.ndarray]: 2-tuple of vertices (n-by-3 array) and tetras indices (n-by-4 array).
    """

    nx, ny, nz = [shape] * 3 if isinstance(shape, int) else shape
    xmin, xmax, ymin, ymax, zmin, zmax = extent
    dx, dy, dz = (xmax - xmin) / nx, (ymax - ymin) / ny, (zmax - zmin) / nz

    # from number of voxet to number vertices per side
    nx, ny, nz = nx + 1, ny + 1, nz + 1
    vertices = np.mgrid[0:nx, 0:ny, 0:nz].T.reshape(-1, 3).astype(float)

    # rescale/translate grid points
    vertices[..., 0] *= dx
    vertices[..., 0] += xmin
    vertices[..., 1] *= dy
    vertices[..., 1] += ymin
    vertices[..., 2] *= dz
    vertices[..., 2] += zmin

    # build the tetras from tetcube template
    cell = np.asarray(tetcube[1])
    # match vertex indices with grid shape
    template = {
        0: 0,
        1: 1,
        2: nx + 1,
        3: nx,
        4: nx * ny,
        5: nx * ny + 1,
        6: nx * ny + nx + 1,
        7: nx * ny + nx,
    }
    cells = np.array([template[i] for i in cell.flat]).reshape(
        cell.shape
    )  # single tetcube (cube of 5 tetras)
    cells = np.vstack([cells + k for k in range(nx - 1)])  # line of tetcubes
    cells = np.vstack([cells + nx * k for k in range(ny - 1)])  # square of tetcubes
    cells = np.vstack([cells + ny * nx * k for k in range(nz - 1)])  # cube of tetcubes

    return vertices, cells


def tetdomain(
    extent: tuple[float] = (-1, 1, -1, 1, -1, 1),
    resolution: float | tuple[float] = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Covers a 3D extent with a regular grid of maximal size tesselated cubes.

    Note that a single cube will produce 8 vertices and 5 tetras,
    the total number of tetras equals 5*nx*ny*nz

    Args:
        extent (tuple of floats: Extent of the grid as (xmin, xmax, ymin, ymax, zmin, zmax).
        resolution (float or tuple of floats): Minimum length between grid points, e.g., (3, 3, 3) or 3.

    Returns:
        tuple[np.ndarray, np.ndarray]: 2-tuple of vertices (n-by-3 array) and tetras indices (n-by-4 array).
    """

    dx, dy, dz = (
        [resolution] * 3 if isinstance(resolution, (int, float)) else resolution
    )
    xmin, xmax, ymin, ymax, zmin, zmax = extent
    # deduce the number of cubes
    nx, ny, nz = (
        max((xmax - xmin) // dx, 1),
        max((ymax - ymin) // dy, 1),
        max((zmax - zmin) // dz, 1),
    )
    shape = np.array((nx, ny, nz), dtype=int)
    return tetgrid(shape, extent)


# def tetmesh(vertices, cells) -> UnstructuredGrid:
#     """Wrap tetrahedral mesh as pyvista.UnstructuredGrid object.

#     Args:
#         vertices (ArrayLike): n-by-3 array of vertices coordinates.
#         cells (ArrayLike): m-by-4 array of tetrahedron vertex indices.

#     Returns:
#         UnstructuredGrid: pyvista.UnstructuredGrid mesh object.
#     """
#     n = len(cells)
#     cells = np.c_[np.full((n, 1), 4), cells].ravel()
#     celltypes = [CellType.TETRA] * n
#     return UnstructuredGrid(cells, celltypes, vertices)


# def tetplot(vertices, cells, **kwargs):
#     """Helper to fast plot tetraherons"""
#     tetmesh(vertices, cells).plot(**kwargs)


# if __name__ == "__main__":
#     import sys

#     from pyvista import Plotter

#     nargv = len(sys.argv)
#     n = int(sys.argv[1]) if nargv > 1 else 8
#     vertices, cells = tetgrid(n, (-1, 1, -1, 1, -1, 1))

#     plotter = Plotter()
#     if n <= 4:
#         plotter.add_point_labels(vertices, range(len(vertices)))

#     plotter.add_mesh(tetmesh(vertices, cells), opacity=0.5, show_edges=True)
#     plotter.show_bounds()
#     plotter.show()
