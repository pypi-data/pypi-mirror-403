#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 16:16:39 2021

@author: peruzzetto
"""

import matplotlib
import copy
import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from pytopomap.tools import centered_map, get_contour_intervals, auto_uniform_grey
# from pytopomap.tools import colorbar


def plot_topo(
    z: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    contour_step: float = None,
    nlevels: int = None,
    level_min: float = None,
    step_contour_bold: float | str = "auto",
    contour_labels_properties: dict = None,
    label_contour: bool = True,
    contour_label_effect: list = None,
    axe: matplotlib.axes._axes.Axes = None,
    vert_exag: float = 1.,
    ndv: int | float = -9999,
    uniform_grey: str = "auto",
    contours_prop: dict = None,
    contours_bold_prop: dict = None,
    figsize: tuple[float] = None,
    interpolation: str = None,
    sea_level: int | float = 0,
    sea_color: str = None,
    alpha: float = 1.,
    azdeg: int | float = 315,
    altdeg: int | float = 45,
    ) -> matplotlib.axes._axes.Axes: 
    """
    Plot topography with hillshading.

    Parameters
    ----------
    z : np.ndarray
        2D array of elevation values.
    x : np.ndarray
        1D array of X coordinates.
    y : np.ndarray
        1D array of Y coordinates.
    contour_step : float, optional
        Interval between thin contour lines. Automatically determined if None. The default is None.
    nlevels : TYPE, optional
        Number of contour levels to draw if "contour_step" is not set. The default is None.
    level_min : float, optional
        Minimum contour level. Automatically calculated if None. The default is None.
    step_contour_bold : float or str, optional
        Interval between bold contour lines. If "auto", computed from elevation range. The default is "auto".
    contour_labels_properties : dict, optional
        Properties passed to "ax.clabel()" for contour labels. The default is None.
    label_contour : bool, optional
        If True, add labels to bold contour lines. The default is True.
    contour_label_effect : list, optional
        List of matplotlib.patheffects to apply to contour labels. The default is None.
    axe : matplotlib.axes._axes.Axes, optional
        Existing axes object to draw the plot on. The default is None.
    vert_exag : float, optional
        Vertical exaggeration factor for hillshading. The default is 1.
    ndv : int or float, optional
        No-data value in the elevation array. The default is -9999.
    uniform_grey : str, optional
        If "auto", use auto_uniform_grey to compute the hillshading. The default is "auto".
    contours_prop : dict, optional
        Properties for thin contour lines. The default is "auto".
    contours_bold_prop : dict, optional
        Properties for bold contour lines. The default is "auto".
    figsize : tuple[float], optional
        Figure size (width, height) if a new figure is created. The default is None.
    interpolation : str, optional
        Interpolation method for "imshow". The default is None.
    sea_level : int or float, optional
        Sea level threshold for optional sea overlay. The default is 0.
    sea_color : str, optional
        Color used to fill areas below sea level. If None, no sea mask is applied. The default is None.
    alpha : float, optional
        Transparency for the hillshading layer. The default is 1.
    azdeg : int or float, optional
        Azimuth angle for light source (degrees from North). The default is 315.
    altdeg : int or float, optional
        Altitude angle for light source (degrees above horizon). The default is 45.

    Returns
    -------
    axe : matplotlib.axes._axes.Axes
        Axes object containing the plotted topography.
    """
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    im_extent = [x[0] - dx / 2, x[-1] + dx / 2, y[0] - dy / 2, y[-1] + dy / 2]
    ls = mcolors.LightSource(azdeg=azdeg, altdeg=altdeg)

    auto_bold_intv = None

    tmpz = np.copy(z)
    tmpz[tmpz == ndv] = np.nan

    if nlevels is None and contour_step is None:
        auto_bold_intv, contour_step = get_contour_intervals(
            np.nanmin(tmpz), np.nanmax(tmpz)
        )

    if level_min is None:
        if contour_step is not None:
            level_min = np.ceil(np.nanmin(tmpz) / contour_step) * contour_step
        else:
            level_min = np.nanmin(tmpz)
    if contour_step is not None:
        levels = np.arange(level_min, np.nanmax(tmpz), contour_step)
    else:
        levels = np.linspace(level_min, np.nanmax(tmpz), nlevels)

    if axe is None:
        fig, axe = plt.subplots(1, 1, figsize=figsize, layout="constrained")

    axe.set_ylabel("Y (m)")
    axe.set_xlabel("X (m)")
    axe.set_aspect("equal")

    if uniform_grey == "auto":
        uniform_grey = auto_uniform_grey(
            z,
            vert_exag,
            azdeg=azdeg,
            altdeg=altdeg,
            dx=dx,
            dy=dx,
        )

    z_shade = np.copy(z)
    z_shade[np.isnan(z_shade)] = ndv
    if uniform_grey is None:
        shaded_topo = ls.hillshade(
            z_shade, vert_exag=vert_exag, dx=dx, dy=dy, fraction=1
        )
    else:
        shaded_topo = np.ones(z.shape) * uniform_grey
    shaded_topo[z == ndv] = np.nan
    shaded_topo[np.isnan(z)] = np.nan
    axe.imshow(
        shaded_topo,
        cmap="gray",
        extent=im_extent,
        interpolation=interpolation,
        alpha=alpha,
        vmin=0,
        vmax=1,
    )

    if contours_prop is None:
        contours_prop = dict(alpha=0.5, colors="k", linewidths=0.5)
    axe.contour(
        x,
        y,
        np.flip(tmpz, axis=0),
        extent=im_extent,
        levels=levels,
        **contours_prop
    )

    if contours_bold_prop is None:
        contours_bold_prop = dict(alpha=0.8, colors="k", linewidths=0.8)

    if step_contour_bold == "auto":
        if auto_bold_intv is None:
            auto_bold_intv, _ = get_contour_intervals(
                np.nanmin(tmpz), np.nanmax(tmpz)
            )
        step_contour_bold = auto_bold_intv

    if step_contour_bold > 0:
        lmin = np.ceil(np.nanmin(tmpz) / step_contour_bold) * step_contour_bold
        if lmin < level_min:
            lmin = lmin + step_contour_bold
        levels = np.arange(lmin, np.nanmax(tmpz), step_contour_bold)
        cs = axe.contour(
            x,
            y,
            np.flip(tmpz, axis=0),
            extent=im_extent,
            levels=levels,
            **contours_bold_prop
        )
        if label_contour:
            if contour_labels_properties is None:
                contour_labels_properties = {}
            clbls = axe.clabel(cs, **contour_labels_properties)
            if contour_label_effect is not None:
                plt.setp(clbls, path_effects=contour_label_effect)

    if sea_color is not None:
        cmap_sea = mcolors.ListedColormap([sea_color])
        cmap_sea.set_under(color="w", alpha=0)
        mask_sea = (z <= sea_level) * 1
        if mask_sea.any():
            axe.imshow(
                mask_sea,
                extent=im_extent,
                cmap=cmap_sea,
                vmin=0.5,
                interpolation="none",
            )

    return axe


def plot_imshow(
    x: np.ndarray,
    y: np.ndarray,
    data: np.ndarray,
    axe: matplotlib.axes._axes.Axes = None,
    figsize: tuple[float] = None,
    cmap: str = None,
    minval: int | float = None,
    maxval: int | float = None,
    vmin: float = None,
    vmax: float = None,
    alpha: float = 1.,
    minval_abs: float = None,
    cmap_intervals:  tuple[int] | tuple[float] = None,
    unique_values: bool = False,
    extend_cc: str = "max",
    plot_colorbar: bool = True,
    axecc: matplotlib.axes._axes.Axes = None,
    colorbar_kwargs: dict = None,
    aspect: str | float = None,
    ) -> matplotlib.axes._axes.Axes:
    """
    plt.imshow data with some pre-processing.

    Parameters
    ----------
    x : np.ndarray
        1D array of X coordinates.
    y : np.ndarray
        1D array of Y coordinates.
    data : np.ndarray
        2D array of data values.
    axe : matplotlib.axes._axes.Axes, optional
        Existing axes object to draw the plot on. The default is None.
    figsize : tuple[float], optional
        Figure size (width, height) if a new figure is created. The default is None.
    cmap : str, optional
        Name of the colormap to use. If None, use "hot_r" or "seismic". The default is None.
    minval : int or float, optional
        Minimum value to display. The default is None.
    maxval : int or float, optional
        Maximum value to display. The default is None.
    vmin : float, optional
        Alias for minval. The default is None.
    vmax : float, optional
        Alias for maxval. The default is None.
    alpha : float, optional
        Transparency for the data layer. The default is 1.
    minval_abs : float, optional
        If set, masks values with absolute magnitude below this threshold. The default is None.
    cmap_intervals : tuple of int or float, optional
        Explicit color intervals for categorical or segmented color mapping. The default is None.
    unique_values : bool, optional
        If True, use discrete colormap with ticks corresponding to unique values. The default is False.
    extend_cc : str, optional
        Behavior of colorbar outside bounds, can be "neither", "min", "max", "both". The default is "max".
    plot_colorbar : bool, optional
        Whether to add a colorbar. The default is True.
    axecc : matplotlib.axes._axes.Axes, optional
        Axes object for the colorbar. If None, colorbar is placed automatically. The default is None.
    colorbar_kwargs : dict, optional
        Additional keyword arguments passed to "figure.colorbar".
    aspect : str or float, optional
        Aspect ratio of the image. Can be "equal", "auto", or a numeric value.

    Returns
    -------
    axe : matplotlib.axes._axes.Axes
        Axes object with the image and optional colorbar.
    """
    if axe is None:
        _, axe = plt.subplots(1, 1, figsize=figsize, layout="constrained")

    f = copy.copy(data)

    # vmin and vmax are similar to minval and maxval
    # and supplent minval and maxval if used
    if vmin is not None:
        minval = vmin

    if vmax is not None:
        maxval = vmax

    # Remove values below and above minval and maxval, depending on whether
    # cmap_intervals are given with or without extend_cc
    if (cmap_intervals is not None) and not unique_values:
        if extend_cc in ["neither", "max"]:
            minval = cmap_intervals[0]
            f[f < minval] = np.nan
        elif extend_cc in ["neither", "min"]:
            maxval = cmap_intervals[-1]
            f[f > maxval] = np.nan
    else:
        if minval is not None:
            f[f < minval] = np.nan

    # Get min and max values
    if maxval is None:
        maxval = np.nanmax(f)
    if minval is None:
        minval = np.nanmin(f)

    if minval_abs:
        f[np.abs(f) <= minval_abs] = np.nan
    else:
        f[f == 0] = np.nan

    # Define colormap type
    if cmap is None:
        if maxval * minval >= 0:
            cmap = "hot_r"
        else:
            cmap = "seismic"

    norm = None
    if unique_values:
        if cmap_intervals is not None:
            values = cmap_intervals
        else:
            values = np.unique(f[~np.isnan(f)])
        n_values = len(values)
        if isinstance(cmap, list):
            color_map = mcolors.LinearSegmentedColormap.from_list('custom_cm', cmap, N=n_values)
        else:
            color_map = matplotlib.cm.get_cmap(cmap, n_values)
        bounds = np.zeros(n_values + 1)
        bounds[1:-1] = 0.5 * (values[1:] + values[:-1])
        bounds[0] = values[0] - 0.5
        bounds[-1] = values[-1] + 0.5
        norm = matplotlib.colors.BoundaryNorm(bounds, n_values)
        minval = None
        maxval = None
    else:
        if (maxval * minval >= 0) or np.isnan(maxval * minval):
            if isinstance(cmap, list):
                color_map = mcolors.LinearSegmentedColormap.from_list('custom_cm', cmap)
            else:
                color_map = matplotlib.colormaps[cmap]
        else:
            color_map = centered_map(cmap, minval, maxval)

    if cmap_intervals is not None and not unique_values:
        norm = matplotlib.colors.BoundaryNorm(
            cmap_intervals, 256, extend=extend_cc
        )
        maxval = None
        minval = None

    # get map_extent
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    im_extent = [x[0] - dx / 2, x[-1] + dx / 2, y[0] - dy / 2, y[-1] + dy / 2]

    # Plot data

    fim = axe.imshow(
        f,
        extent=im_extent,
        cmap=color_map,
        vmin=minval,
        vmax=maxval,
        alpha=alpha,
        interpolation="none",
        norm=norm,
        zorder=4,
        aspect=aspect,
    )

    # Plot colorbar
    if plot_colorbar:
        colorbar_kwargs = {} if colorbar_kwargs is None else colorbar_kwargs
        if cmap_intervals is not None and extend_cc is not None:
            colorbar_kwargs["extend"] = extend_cc
        cb = axe.figure.colorbar(fim, cax=axecc, **colorbar_kwargs)
        if unique_values:
            cb.set_ticks(
                [(b0 + b1) / 2 for b0, b1 in zip(bounds[:-1], bounds[1:])],
                labels=values,
            )

    return axe


def plot_data_on_topo(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    data: np.ndarray,
    axe: matplotlib.axes._axes.Axes = None,
    figsize: tuple[float] = None,
    cmap: str = None,
    minval: int | float = None,
    maxval: int | float = None,
    vmin: float = None,
    vmax: float = None,
    minval_abs: float = None,
    cmap_intervals: tuple[int] | tuple[float] = None,
    unique_values: bool = False,
    extend_cc: str = "max",
    topo_kwargs: dict = None,
    alpha: float = 1.,
    plot_colorbar: bool = True,
    axecc: matplotlib.axes._axes.Axes = None,
    colorbar_kwargs: dict = None,
    mask: np.ndarray = None,
    alpha_mask: float = None,
    color_mask: str = "k",
    xlims: int | float = None,
    ylims: int | float = None,
    ) -> matplotlib.axes._axes.Axes:
    """
    Plot array data on topo.

    Parameters
    ----------
    x : np.ndarray
        1D array of X coordinates.
    y : np.ndarray
        1D array of Y coordinates.
    z : np.ndarray
        2D array of elevation values.
    data : np.ndarray
        2D array of data values.
    axe : matplotlib.axes._axes.Axes, optional
        Existing axes object to draw the plot on. The default is None.
    figsize : tuple[float], optional
        Figure size (width, height) if a new figure is created. The default is None.
    cmap : str, optional
        Name of the colormap to use. If None, use "hot_r" or "seismic". The default is None.
    minval : int or float, optional
        Minimum value to display. The default is None.
    maxval : int or float, optional
        Maximum value to display. The default is None.
    vmin : float, optional
        Alias for minval. The default is None.
    vmax : float, optional
        Alias for maxval. The default is None.
    minval_abs : float, optional
        If set, masks values with absolute magnitude below this threshold. The default is None.
    cmap_intervals : tuple of int or float, optional
        Explicit color intervals for categorical or segmented color mapping. The default is None.
    unique_values : bool, optional
        If True, use discrete colormap with ticks corresponding to unique values. The default is False.
    extend_cc : str, optional
        Behavior of colorbar outside bounds, can be "neither", "min", "max", "both". The default is "max".
    topo_kwargs : dict, optional
        Additional keyword arguments passed to "plot_topo". The default is None.
    alpha : float, optional
        Transparency for the data layer. The default is 1.
    plot_colorbar : bool, optional
        Whether to add a colorbar. The default is True.
    axecc : matplotlib.axes._axes.Axes, optional
        Axes object for the colorbar. If None, colorbar is placed automatically. The default is None.
    colorbar_kwargs : dict, optional
        Additional keyword arguments passed to "figure.colorbar".
    mask : np.ndarray, optional
        Binary 2D array of same shape as "data". Used to overlay a mask.
        Masked regions are displayed with "color_mask". The default is None.
    alpha_mask : float, optional
        Transparency of the mask overlay. The default is None (fully opaque).
    color_mask : str, optional
        Color used to draw the mask overlay. The default is "k".
    xlims : tuple of float, optional
        X-axis display limits (min, max). If None, auto-scaled. The default is None.
    ylims : tuple of float, optional
        Y-axis display limits (min, max). If None, auto-scaled. The default is None.

    Returns
    -------
    axe : matplotlib.axes._axes.Axes
        The axes object containing the final plot.
    """
    # Initialize figure properties
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    im_extent = [x[0] - dx / 2, x[-1] + dx / 2, y[0] - dy / 2, y[-1] + dy / 2]
    if axe is None:
        fig, axe = plt.subplots(1, 1, figsize=figsize, layout="constrained")

    axe.set_ylabel("Y (m)")
    axe.set_xlabel("X (m)")
    axe.set_aspect("equal", adjustable="box")

    # Plot topo
    topo_kwargs = {} if topo_kwargs is None else topo_kwargs

    if z is not None:
        plot_topo(z, x, y, axe=axe, **topo_kwargs)

    # Plot mask
    if mask is not None:
        cmap_mask = mcolors.ListedColormap([color_mask])
        cmap_mask.set_under(color="w", alpha=0)
        axe.imshow(
            np.flip(mask, axis=0),
            extent=im_extent,
            cmap=cmap_mask,
            vmin=0.5,
            origin="lower",
            interpolation="none",
            # zorder=3,
            alpha=alpha_mask,
        )

    # Plot data
    plot_imshow(
        x,
        y,
        data,
        axe=axe,
        cmap=cmap,
        minval=minval,
        maxval=maxval,
        vmin=vmin,
        vmax=vmax,
        minval_abs=minval_abs,
        cmap_intervals=cmap_intervals,
        extend_cc=extend_cc,
        plot_colorbar=plot_colorbar,
        axecc=axecc,
        colorbar_kwargs=colorbar_kwargs,
        unique_values=unique_values,
        alpha=alpha,
    )

    # Adjust axes limits
    if xlims is not None:
        axe.set_xlim(xlims[0], xlims[1])

    if ylims is not None:
        axe.set_ylim(ylims[0], ylims[1])

    return axe


def plot_maps(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    data: np.ndarray,
    t: np.ndarray,
    file_name: str = None,
    folder_out: str = None,
    figsize: tuple[float] = None,
    dpi: int = None,
    fmt: str = "png",
    sup_plt_fn=None,
    sup_plt_fn_args=None,
    **kwargs
    ) -> None:
    """    
    Plot and save maps of simulations outputs at successive time steps

    Parameters
    ----------
    x : np.ndarray
        1D array of X coordinates.
    y : np.ndarray
        1D array of Y coordinates.
    z : np.ndarray
        2D array of elevation values.
    data : np.ndarray
        2D array of data values.
    t : np.ndarray
        List time steps, same length as the third dimension of "data".
    file_name : str, optional
        Base name for the output image files. The default is None.
    folder_out : str, optional
        Path to the output folder. If not provides, figures are not saved. The default is None.
    figsize : tuple[float], optional
        Size of each figure (width, height). The default is None.
    dpi : int, optional
        Resolution for saved figures. Only used if "folder_out" is set. The default is None.
    fmt : str, optional
        File format for saving figures. Default is "png".
    sup_plt_fn : callable, optional
        A custom function to apply additional plotting on the axes. The default is None.
    sup_plt_fn_args : dict, optional
        Arguments to pass to "sup_plt_fn". The default is None.
    **kwargs : dict
        Additional keyword arguments passed to "plot_data_on_topo".
    """
    nfigs = len(t)
    if nfigs != data.shape[2]:
        raise ValueError(
            "length of t must be similar to the last dimension of data"
        )
    if folder_out is not None:
        file_path = os.path.join(folder_out, file_name + "_{:04d}." + fmt)
    title_fmt = "t = {:.2f} s"

    for i in range(nfigs):
        axe = plot_data_on_topo(
            x, y, z, data[:, :, i], axe=None, figsize=figsize, **kwargs
        )
        axe.set_title(title_fmt.format(t[i]))
        if sup_plt_fn is not None:
            if sup_plt_fn_args is None:
                sup_plt_fn_args = dict()
            sup_plt_fn(axe, **sup_plt_fn_args)
        # axe.figure.tight_layout(pad=0.1)
        if folder_out is not None:
            axe.figure.savefig(
                file_path.format(i),
                dpi=dpi,
                bbox_inches="tight",
                pad_inches=0.05,
            )