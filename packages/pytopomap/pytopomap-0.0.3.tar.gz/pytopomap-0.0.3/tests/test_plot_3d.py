#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 16:16:39 2021

@author: peruzzetto
"""

import pytest
import os

import numpy as np

from pytopomap.plot_3d import plot_topo_3D, plot_imshow_3D, plot_data_on_topo_3D

temporary_folder = r".\\temp_3d"
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
    plot_topo_3D(elevation, x, y, saving_path=temporary_folder)
    assert len(os.listdir(temporary_folder)) == 1
    clean_file()


def data_hill_1(x, y):
    data = np.zeros((len(x), len(y)))
    for i in range(len(x)):
        for j in range(len(y)):
            data[i][j] = 1 - ((x[i] - 2.5)**2)/3 - ((y[j] - 2.5)**2)/0.5
    return data


def test_imshow():
    plot_imshow_3D(x, y, data_hill_1(x, y), saving_path=temporary_folder)
    assert len(os.listdir(temporary_folder)) == 1
    clean_file()


def test_data_topo():
    plot_data_on_topo_3D(x, y, z_hill(x, y), data_hill_1(x, y), saving_path=temporary_folder)
    assert len(os.listdir(temporary_folder)) == 1
    clean_file()
    remove_folder()


def clean_file():
    if os.path.exists(os.path.join(temporary_folder, "topography.html")):
        os.remove(os.path.join(temporary_folder, "topography.html"))
    if os.path.exists(os.path.join(temporary_folder, "data.html")):
        os.remove(os.path.join(temporary_folder, "data.html"))
    if os.path.exists(os.path.join(temporary_folder, "data_on_topography.html")):
        os.remove(os.path.join(temporary_folder, "data_on_topography.html"))

def remove_folder():
    if len(os.listdir(temporary_folder)) == 0:
        os.rmdir(temporary_folder)
