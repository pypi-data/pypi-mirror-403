#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 16:16:39 2021

@author: peruzzetto
"""

import matplotlib

import numpy as np
import matplotlib.colors as mcolors

BOLD_CONTOURS_INTV = [
    0.1,
    0.2,
    0.5,
    1,
    2.0,
    5,
    10,
    20,
    50,
    100,
    200,
    500,
    1000,
]
NB_THIN_CONTOURS = 10
NB_BOLD_CONTOURS = 3


def centered_map(
    cmap: str,
    vmin: float,
    vmax: float,
    ncolors: int = 256
) -> matplotlib.colors.LinearSegmentedColormap:
    """
    Create centered colormap.

    Parameters
    ----------
    cmap : str
        Curent colormap of the plot.
    vmin : float
        Minimum value of the dataset.
    vmax : float
        Maximal value of the dataset.
    ncolors : int, optional
        Total number of colors contained in the new colormap. The default is 256.

    Returns
    -------
    new_map : matplotlib.colors.LinearSegmentedColormap
        New colormap objects centered in 0.
    """
    p = vmax / (vmax - vmin)
    npos = int(ncolors * p)
    if isinstance(cmap, list):
        cmap_tmp = mcolors.LinearSegmentedColormap.from_list("tmp", cmap)
    else:
        cmap_tmp = matplotlib.colormaps[cmap]
    colors1 = cmap_tmp(np.linspace(0.0, 1, npos * 2))
    colors2 = cmap_tmp(np.linspace(0.0, 1, (ncolors - npos) * 2))
    colors = np.concatenate(
        (colors2[: ncolors - npos, :], colors1[npos:, :]), axis=0
    )
    # colors[ncolors-npos-1,:]=np.ones((1,4))
    # colors[ncolors-npos,:]=np.ones((1,4))
    new_map = mcolors.LinearSegmentedColormap.from_list("my_colormap", colors)

    return new_map


def get_contour_intervals(
    zmin: float,
    zmax: float,
    nb_bold_contours: int = None,
    nb_thin_contours: int = None
) -> tuple[float, float]:
    """
    Provides the intervals for thin and bold contour lines

    Parameters
    ----------
    zmin : float
        Minimum altitude of the topography.
    zmax : float
        Maximum altitude of the topography.
    nb_bold_contours : int, optional
        Number of bold line. The default is None.
    nb_thin_contours : int, optional
        Number of thin line. The default is None.

    Returns
    -------
    bold_intv : float
        Interval between bold contour lines.

    thin_intv : float
        Interval between thin contour lines.
    """
    if nb_thin_contours is None:
        nb_thin_contours = NB_THIN_CONTOURS
    if nb_bold_contours is None:
        nb_bold_contours = NB_BOLD_CONTOURS

    intv = (zmax - zmin) / nb_bold_contours
    i = np.argmin(np.abs(np.array(BOLD_CONTOURS_INTV) - intv))

    bold_intv = BOLD_CONTOURS_INTV[i]
    if BOLD_CONTOURS_INTV[i] != BOLD_CONTOURS_INTV[0]:
        if bold_intv - intv > 0:
            bold_intv = BOLD_CONTOURS_INTV[i - 1]

    if nb_thin_contours is None:
        thin_intv = bold_intv / NB_THIN_CONTOURS
        if (zmax - zmin) / bold_intv > 5:
            thin_intv = thin_intv * 2
    else:
        thin_intv = bold_intv / nb_thin_contours

    return bold_intv, thin_intv


def auto_uniform_grey(
    z: np.ndarray,
    vert_exag: float,
    azdeg: int = 315,
    altdeg: int = 45,
    dx: float = 1.,
    dy: float = 1.,
    std_threshold: float = 0.01
) -> float:
    """
    Detect if shading must be applied to topography or not (uniform grey). The
    criterion in colors.LightSource.hillshade is the difference between min
    and max illumination, and seems to restrictive.

    Parameters
    ----------
    z : np.ndarray
        Altitude of each point of the topography.

    vert_exag : float
        Vertical exaggeration factor for hillshading.

    azdeg : int, optional
        Azimuth angle for light source (degrees from North). The default is 315. 

    altdeg : int, optional
        Altitude angle for light source (degrees above horizon). The default is 45

    dx : float, optional
        Cell size of the x axis. The default is 1.0.

    dy : float, optional
        Cell size of the y axis. The default is 1.0.

    std_treshold: float, optional
        Relief detection threshold. The default is 0.5.

    Returns
    -------
    float | None
        If no shading applied return None, else return 0.5.

    """
    # Get topography normal direction
    e_dy, e_dx = np.gradient(vert_exag * z, dy, dx)
    normal = np.empty(z.shape + (3,)).view(type(z))
    normal[..., 0] = -e_dx
    normal[..., 1] = -e_dy
    normal[..., 2] = 1
    sum_sq = 0
    for i in range(normal.shape[-1]):
        sum_sq += normal[..., i, np.newaxis] ** 2
    normal /= np.sqrt(sum_sq)

    # Light source direction
    az = np.radians(90 - azdeg)
    alt = np.radians(altdeg)
    direction = np.array(
        [np.cos(az) * np.cos(alt), np.sin(az) * np.cos(alt), np.sin(alt)]
    )

    # Compute intensity (equivalent to LightSource hillshade, whithour rescaling)
    intensity = normal.dot(direction)
    std = np.nanstd(intensity)

    if std > std_threshold:
        return None
    else:
        return 0.5


def colorbar(
    mappable,
    ax=None,
    cax=None,
    size: str = "5%",
    pad: float = 0.1,
    position: str = "right",
    **kwargs: dict
) -> matplotlib.colorbar.Colorbar:
    """
    Create nice colorbar matching height/width of axe.

    Parameters
    ----------
    mappable : matplotlib.cm.ScalarMappable
        Mappable object used to generate the colorbar.
    ax : matplotlib.axes.Axes, optional
        The axis associated with the colorbar. The default is None.
    cax : matplotlib.axes.Axes, optional
        Specific axis to draw the colorbar into. The default is None.
    size : str, optional
        Width or height of the colorbar relative to the parent axis. The default is "5%".
    pad : float, optional
        Padding between the parent axis and the colorbar, as a fraction of the parent axis size. The default is 0.1.
    position : str, optional
        Position of the colorbar relative to the parent axis. Options: 'right', 'left', 'top', 'bottom'. The default is "right".
    **kwargs : dict
        Additional keyword arguments passed to "fig.colorbar()".

    Returns
    -------
    matplotlib.colorbar.Colorbar
        The created Colorbar object.
    """
    if ax is None:
        ax = mappable.axes
    fig = ax.figure
    if position in ["left", "right"]:
        orientation = "vertical"
    else:
        orientation = "horizontal"

    # if cax is None:
    #     # divider = ax.get_axes_locator()
    #     # if divider is None:
    #     divider = make_axes_locatable(ax)
    #     cax = divider.append_axes(position, size=size, pad=pad)

    cc = fig.colorbar(mappable, cax=cax, orientation=orientation, **kwargs)

    if position == "top":
        cax.xaxis.tick_top()
        cax.xaxis.set_label_position("top")
    if position == "left":
        cax.yaxis.tick_left()
        cax.xaxis.set_label_position("left")
    return cc


def read_tiff(
    file
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Read tiff file to numpy ndarray.

    Parameters
    ----------
    file : str
        Path to the tiff file.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        x, y, z values of the tiff file.
    """
    import rasterio

    with rasterio.open(file, "r") as src:
        dem = src.read(1)
        ny, nx = dem.shape
        x = np.linspace(src.bounds.left, src.bounds.right, nx)
        y = np.linspace(src.bounds.bottom, src.bounds.top, ny)
    return x, y, dem


def read_ascii(
    file
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Read ascii grid file to numpy ndarray.

    Parameters
    ----------
    file : str
        Path to the ascii file.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        x, y, z values of the ascii file.
    """
    dem = np.loadtxt(file, skiprows=6)
    grid = {}
    with open(file, "r") as fid:
        for i in range(6):
            tmp = fid.readline().split()
            grid[tmp[0]] = float(tmp[1])
    try:
        x0 = grid["xllcenter"]
        y0 = grid["yllcenter"]
    except KeyError:
        x0 = grid["xllcorner"]
        y0 = grid["yllcorner"]
    nx = int(grid["ncols"])
    ny = int(grid["nrows"])
    dx = dy = grid["cellsize"]
    x = np.linspace(x0, x0 + (nx - 1) * dx, nx)
    y = np.linspace(y0, y0 + (ny - 1) * dy, ny)

    return x, y, dem


def read_raster(
    file
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract x, y, z values of a tif/ascii file.

    Parameters
    ----------
    file : str
        Path to the file.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        x, y, z values of the file.
    """
    if file.endswith(".asc") or file.endswith(".txt"):
        return read_ascii(file)
    elif file.endswith(".tif") or file.endswith(".tif"):
        return read_tiff(file)