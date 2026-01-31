#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 16:16:39 2021

@author: peruzzetto
"""

import matplotlib
import pytest
import os

import numpy as np

from pytopomap.plot import plot_topo, plot_imshow, plot_data_on_topo, plot_maps

temporary_folder = r".\\temp"
os.mkdir(temporary_folder)

x = np.linspace(0, 5, 100)
y = np.linspace(0, 5, 100)


def z_hill(x, y):
    z = np.zeros((len(x), len(y)))
    for i in range(len(x)):
        for j in range(len(y)):
            z[i][j] = 1 - ((x[i] - 2.5)**2)/2 - ((y[j] - 2.5)**2)/4
    return z


def z_complex_topo(x, y):
    z = np.zeros((len(x), len(y)))
    for i in range(len(x)):
        for j in range(len(y)):
            z[i][j] = (np.sin(x[i]) * np.cos(y[j]) + 0.5 * np.sin(3 * x[i] + 1) *
                       np.cos(2 * y[j] + 1) + 0.25 * np.sin(5 * x[i] + 2) * np.cos(4 * y[j] + 2))
    return z


@pytest.mark.parametrize("elevation", [
    np.zeros((100, 100)),
    z_hill(x, y),
    z_complex_topo(x, y),
])
def test_topo(elevation):
    assert isinstance(plot_topo(elevation, x, y), matplotlib.axes._axes.Axes)


def data_hill_1(x, y):
    data = np.zeros((len(x), len(y)))
    for i in range(len(x)):
        for j in range(len(y)):
            data[i][j] = 1 - ((x[i] - 2.5)**2)/3 - ((y[j] - 2.5)**2)/0.5
    return data


def data_hill_2(x, y):
    data = np.zeros((len(x), len(y)))
    for i in range(len(x)):
        for j in range(len(y)):
            data[i][j] = 1 - ((x[i] - 2.5)**2)/3 - ((y[j] - 2.5)**2)/0.5
    return data


def test_topo_with_param():
    assert isinstance(plot_topo(z_hill(x, y), x, y, contour_step=2, nlevels=2, level_min=-1.5, step_contour_bold=0.5, label_contour=False,
                      vert_exag=2, figsize=(12.1, 5.9), sea_level=-2.5, sea_color='blue', alpha=0.5, azdeg=20), matplotlib.axes._axes.Axes)


def test_imshow():
    assert isinstance(plot_imshow(x, y, data_hill_1(x, y)),
                      matplotlib.axes._axes.Axes)


def test_imshow_with_param():
    assert isinstance(plot_imshow(x, y, data_hill_1(x, y), figsize=(12.1, 4.6), cmap="viridis", minval=0.1, maxval=0.9,
                      alpha=0.9, cmap_intervals=[0.2, 0.3, 0.4, 0.5, 0.6], plot_colorbar=False), matplotlib.axes._axes.Axes)


def test_data_on_topo():
    assert isinstance(plot_data_on_topo(x, y, np.zeros(
        (100, 100)), data_hill_1(x, y)), matplotlib.axes._axes.Axes)


def test_data_on_topo_with_param():
    assert isinstance(plot_data_on_topo(x, y, z_hill(x, y), data_hill_1(x, y), figsize=(10, 10), cmap='viridis', minval=0.1, maxval=0.9, alpha=0.9, cmap_intervals=[
                      0.2, 0.3, 0.4, 0.5, 0.6], plot_colorbar=False, topo_kwargs={"sea_level": -2.5, "sea_color": 'blue'}), matplotlib.axes._axes.Axes)


def test_maps():
    plot_maps(x, y, z_hill(x, y), np.stack((data_hill_1(x, y), data_hill_2(
        x, y)), axis=-1), np.array([0.1, 0.2]), 'Test', temporary_folder)
    assert len(os.listdir(temporary_folder)) == 2
    os.remove(os.path.join(temporary_folder, "Test_0000.png"))
    os.remove(os.path.join(temporary_folder, "Test_0001.png"))
    os.rmdir(temporary_folder)
