"""
"This" is my example-script
===========================

This example doesn't do much, it just makes a simple plot
"""

# %
# Test sub section
# -------------------------
#
# In the built documentation, it will be rendered as reST. All reST lines
# must begin with '# ' (note the space) including underlines below section
# headers.

import plotly
import copy
import os

import numpy as np

import plotly.graph_objects as go
import plotly.graph_objs._figure


def plot_topo_3D(
    z: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    ndv: int | float = -9999,
    vert_exag: float = 1,
    light_source: tuple[int, int] = None,
    add_walls: bool = True,
    add_floor: bool = True,
    saving_path: str = None,
    auto_open: bool = False
) -> plotly.graph_objs._figure.Figure:
    """
    Plot 3D topography with hillshading.

    Parameters
    ----------
    z : np.ndarray
        2D array of elevation values.
    x : np.ndarray
        1D array of X coordinates.
    y : np.ndarray
        1D array of Y coordinates.
    ndv : int or float, optional
        No-data value in the elevation array. The default is -9999.
    vert_exag : float, optional
        Vertical exaggeration factor. The default is 1.
    light_source : tuple[int], optional
        Light source direction for shading (azimuth, degrees from North and altitude, degrees from horizon). The default is None.
    add_walls : bool, optional
        If True, add walls under the figure. The default is True
    add_floor : bool, optional
        If True, add floor under the figure. The default is True
    saving_path : str, optional
        Folder path to save the html file. If None file saved in source folder. The default is None.
    auto_open : bool, optional
        If True, open the result. The default is False.

    Returns
    -------
    None
    """
    corrz = np.copy(z)
    z_base = np.nanmin(corrz)

    corrz[corrz == ndv] = np.nan

    if light_source is not None:
        az = np.radians(light_source[0])
        alt = np.radians(light_source[1])
    else:
        az = np.radians(90)
        alt = np.radians(45)
    

    fig = go.Figure(data=[
        go.Surface(
            z=corrz*vert_exag,
            x=x,
            y=y,
            surfacecolor=np.zeros_like(corrz),
            colorscale=[[0, 'lightgray'], [1, 'lightgray']],
            cmin=np.nanmin(z),
            cmax=np.nanmax(z),
            showscale=False,
            lighting=dict(ambient=0.5, diffuse=0.8, specular=0.5,
                          roughness=0.5, fresnel=0.2),
            lightposition=dict(x=float(np.cos(alt) * np.cos(az)),
                               y=float(np.cos(alt) * np.sin(az)), z=float(np.sin(alt)))
        )
    ])

    if add_walls:
        fig.add_trace(go.Surface(
            z=np.vstack([corrz[0], np.full_like(z[0], z_base)]),
            x=np.tile(x, (2, 1)),
            y=np.full((2, len(x)), y[0]),
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

        fig.add_trace(go.Surface(
            z=np.vstack([corrz[-1], np.full_like(z[-1], z_base)]),
            x=np.tile(x, (2, 1)),
            y=np.full((2, len(x)), y[-1]),
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

        fig.add_trace(go.Surface(
            z=np.column_stack([corrz[:, 0], np.full_like(z[:, 0], z_base)]),
            x=np.full((len(y), 2), x[0]),
            y=np.tile(y, (2, 1)).T,
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

        fig.add_trace(go.Surface(
            z=np.column_stack([corrz[:, -1], np.full_like(z[:, -1], z_base)]),
            x=np.full((len(y), 2), x[-1]),
            y=np.tile(y, (2, 1)).T,
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

    if add_floor:
        fig.add_trace(go.Surface(
            z=np.full_like(corrz, z_base),
            x=x,
            y=y,
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

    fig.update_layout(
        title='Topographic Surface',
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            aspectmode='auto'
        )
    )

    if saving_path is not None:
        fig.write_html(os.path.join(
            saving_path, "topography.html"), auto_open=auto_open)
    
    return fig


def plot_imshow_3D(
    x: np.ndarray,
    y: np.ndarray,
    data: np.ndarray,
    cmap: str = None,
    minval: int | float = None,
    maxval: int | float = None,
    minval_abs: float = None,
    vert_exag: float = 1.,
    saving_path: str = None,
    auto_open: bool = False
) -> plotly.graph_objs._figure.Figure:
    """3D imshow data

    jfdqsjf

    Parameters
    ----------
    x : np.ndarray
        1D array of X coordinates.
    y : np.ndarray
        1D array of Y coordinates.
    data : np.ndarray
        2D array of data values.
    cmap : str, optional
        Name of the colormap to use. If None, use "Hot" or "Rdbu. The default is None.
    minval : int or float, optional
        Minimum value to display. The default is None.
    maxval : int or float, optional
        Maximum value to display. The default is None.
    minval_abs : float, optional
        If set, masks values with absolute magnitude below this threshold. The default is None.
    vert_exag : float, optional
        Vertical exaggeration factor. The default is 1.
    saving_path : str, optional
        Folder path to save the html file. If None file saved in source folder. The default is None.
    auto_open : bool, optional
        If True, open the result. The default is False.

    Returns
    -------
    _type_
        _description_
    """
    f = copy.copy(data)

    if minval_abs is not None:
        f[np.abs(f) <= minval_abs] = np.nan
    else:
        f[f == 0] = np.nan

    if minval is None:
        minval = f.min()

    if maxval is None:
        maxval = f.min()

    if cmap is None:
        if (maxval*minval) <= 0:
            cmap = 'Rdbu'
        else:
            cmap = 'Hot'

    fig = go.Figure(data=[
        go.Surface(
            z=f*vert_exag,
            x=x,
            y=y,
            colorscale=cmap,
            cmin=minval,
            cmax=maxval,
            showscale=True
        )
    ])

    fig.update_layout(
        title='Data Surface',
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            aspectmode='auto'
        )
    )

    if saving_path is not None:
        fig.write_html(os.path.join(
            saving_path, "data.html"), auto_open=auto_open)
    
    return fig


def plot_data_on_topo_3D(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    data: np.ndarray,
    ndv: int | float = -9999,
    vert_exag: float = 1,
    light_source: tuple[int, int] = None,
    cmap: str = None,
    minval: int | float = None,
    maxval: int | float = None,
    minval_abs: float = None,
    add_walls: bool = True,
    add_floor: bool = True,
    saving_path: str = None,
    auto_open: bool = False
) -> plotly.graph_objs._figure.Figure:
    """
    Plot 3D array data on topo.

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
    ndv : int or float, optional
        No-data value in the elevation array. The default is -9999.
    light_source : tuple[int], optional
        Light source direction for shading (azimuth, degrees from North and altitude, degrees from horizon). The default is None.
    cmap : str, optional
        Name of the colormap to use. If None, use "Hot" or "Rdbu. The default is None.
    minval : int or float, optional
        Minimum value to display. The default is None.
    maxval : int or float, optional
        Maximum value to display. The default is None.
    minval_abs : float, optional
        If set, masks values with absolute magnitude below this threshold. The default is None.
    add_walls : bool, optional
        If True, add walls under the figure. The default is True
    add_floor : bool, optional
        If True, add floor under the figure. The default is True
    saving_path : str, optional
        Folder path to save the html file. If None file saved in source folder. The default is None.
    auto_open : bool, optional
        If True, open the result. The default is False.

    Returns
    -------
    None
    """
    corrz = np.copy(z)
    z_base = np.nanmin(corrz)

    corrz[corrz == ndv] = np.nan

    f = copy.copy(data)

    if minval_abs is not None:
        f[np.abs(f) <= minval_abs] = np.nan
    else:
        f[f == 0] = np.nan

    if minval is None:
        minval = f.min()

    if maxval is None:
        maxval = f.min()

    if cmap is None:
        if (maxval*minval) <= 0:
            cmap = 'Rdbu'
        else:
            cmap = 'Hot'
    
    if light_source is not None:
        az = np.radians(light_source[0])
        alt = np.radians(light_source[1])
    else:
        az = np.radians(90)
        alt = np.radians(45)

    new_data = np.where(~np.isnan(f), f + z + 1, np.nan)

    fig = go.Figure(data=[
        go.Surface(
            z=corrz,
            x=x,
            y=y,
            surfacecolor=np.zeros_like(corrz),
            colorscale=[[0, 'lightgray'], [1, 'lightgray']],
            cmin=np.nanmin(z),
            cmax=np.nanmax(z),
            showscale=False,
            lighting=dict(ambient=0.5, diffuse=0.8, specular=0.5,
                          roughness=0.5, fresnel=0.2),
            lightposition=dict(x=float(np.cos(alt) * np.cos(az)),
                               y=float(np.cos(alt) * np.sin(az)), z=float(np.sin(alt)))
        ),
        go.Surface(
            z=new_data,
            x=x,
            y=y,
            surfacecolor=f,
            colorscale=cmap,
            cmin=minval,
            cmax=maxval,
            showscale=True,
            colorbar=dict(title="Data thickness", thickness=15)
        )
    ])

    if add_walls:
        fig.add_trace(go.Surface(
            z=np.vstack([corrz[0], np.full_like(z[0], z_base)]),
            x=np.tile(x, (2, 1)),
            y=np.full((2, len(x)), y[0]),
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

        fig.add_trace(go.Surface(
            z=np.vstack([corrz[-1], np.full_like(z[-1], z_base)]),
            x=np.tile(x, (2, 1)),
            y=np.full((2, len(x)), y[-1]),
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

        fig.add_trace(go.Surface(
            z=np.column_stack([corrz[:, 0], np.full_like(z[:, 0], z_base)]),
            x=np.full((len(y), 2), x[0]),
            y=np.tile(y, (2, 1)).T,
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

        fig.add_trace(go.Surface(
            z=np.column_stack([corrz[:, -1], np.full_like(z[:, -1], z_base)]),
            x=np.full((len(y), 2), x[-1]),
            y=np.tile(y, (2, 1)).T,
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

    if add_floor:
        fig.add_trace(go.Surface(
            z=np.full_like(corrz, z_base),
            x=x,
            y=y,
            showscale=False, colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.8
        ))

    fig.update_layout(
        title='Data on Topography',
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            aspectmode='auto'
        )
    )

    if saving_path is not None:
        fig.write_html(os.path.join(
            saving_path, "data_on_topography.html"), auto_open=auto_open)

    return fig
