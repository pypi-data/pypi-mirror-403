# pytopomap

Documentation : https://pytopomap.readthedocs.io/en/latest/

- [Description](#description)
- [Installation with pip](#installation-pip)
- [Installation with anaconda](#installation-conda)


## Description <a name="description"></a>
`pytopomap` package contains generic functions for plotting raster data on shaded topographic maps.

Note that `pytopomap` is still under development, thus only minimal documentation is available at the moment, and testing is underway.


## Installation with pip <a name="installation-pip"></a>

To install `pytopomap` from GitHub or PyPi, you'll need to have `pip` installed on your computer. 

It is strongly recommended to install `pytopomap` in a virtual environnement dedicated to this package. This can be done with `virtualenv`
(see the documentation e.g. [here](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)).
Create the environnement with :

```bash
python -m venv /path/to/myenv
```

and activate it, on Linux:

```bash
source /path/to/myenv/bin/activate
```

and on Windows:

```cmd.exe
\path\to\myenv\Scripts\activate
```

Alternatively, if you are more used to Anaconda :

```bash
conda create -n pytopomap pip
conda activate pytopomap
```

or equivalently with Mamba :

```bash
mamba create -n pytopomap pip
mamba activate pytopomap
```

Before installing with `pip`, make sure `pip`, `steuptools` and `wheel` are up to date

```
python -m pip install --upgrade pip setuptools wheel
```

### Latest stable realease from PyPi <a name="pypi-install"></a>

```
python -m pip install pytopomap
```

### Development version on from GitHub <a name="source-install"></a>

Download the GithHub repository [here](https://github.com/marcperuz/pytopomap), or clone it with

```
git clone https://github.com/marcperuz/pytopomap.git
```

Open a terminal in the created folder and type:

```
python -m pip install .
```

## Installation with from conda-forge <a name="installation-conda"></a>

The latest stable version of `pytopomap` on PyPi is also (supposedly) distributed on `conda-forge`. It can be intalled with Anaconda (or any equivalent) with

```
conda install conda-forge::pytopomap
```
