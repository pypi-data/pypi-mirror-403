import numpy as np

# transposition of tetcube to 2D case

trirect = (
    (
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
    ),
    (
        (0, 1, 2),
        (0, 2, 3),
    ),
)


def trigrid(shape: int | tuple, extent=(0, 1, 0, 1)) -> tuple[np.ndarray, np.ndarray]:
    """Generate a regular grid of (nx, ny) triangulated rectangles.

    Args:
        shape (int or tuple of ints): shape of the grid, e.g., (3, 3) or 3.
        extent (tuple, optional): Extent of the grid as (xmin, xmax, ymin, ymax). Defaults to (0, 1, 0, 1).

    Returns:
        tuple[np.ndarray, np.ndarray]: 2-tuple of vertices (n-by-2 array) and triangle indices (n-by-3 array).
    """

    nx, ny = [shape] * 2 if isinstance(shape, int) else shape
    xmin, xmax, ymin, ymax = extent
    dx, dy = (xmax - xmin) / nx, (ymax - ymin) / ny

    # from number of cells to number vertices per side
    nx, ny = nx + 1, ny + 1
    vertices = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2).astype(float)

    # rescale/translate grid points
    vertices[..., 0] *= dx
    vertices[..., 0] += xmin
    vertices[..., 1] *= dy
    vertices[..., 1] += ymin

    # build the tetras from tetcube template
    cell = np.asarray(trirect[1])
    # match vertex indices with grid shape
    template = {
        0: 0,
        1: 1,
        2: nx + 1,
        3: nx,
    }
    cells = np.array([template[i] for i in cell.flat]).reshape(
        cell.shape
    )  # 2 triangles
    cells = np.vstack([cells + k for k in range(nx - 1)])  # along Ox
    cells = np.vstack([cells + nx * k for k in range(ny - 1)])  # along Oy

    return vertices, cells
