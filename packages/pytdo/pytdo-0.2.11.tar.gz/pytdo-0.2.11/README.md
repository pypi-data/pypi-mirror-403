# `pytdo`

[![Latest Release](https://gitlab.in2p3.fr/himagnetos/pytdo/-/badges/release.svg)](https://gitlab.in2p3.fr/himagnetos/pytdo/-/releases)
[![PyPI](https://img.shields.io/pypi/v/pytdo.svg)](https://pypi.org/project/pytdo/)

## Description
`pytdo` provides a Python API to read and analyse tunnel diode oscillator experiments on samples exposed to a high magnetic field. It is bundled with a graphical user interface written with PyQt.

## Installation

### Method 1 : As an app
If you plan to just use the graphical user interface, consider installing `pytdo` as a tool managed by [uv](https://docs.astral.sh/uv/), a modern Python package manager.

To do so, install uv (see the official installation instructions : https://docs.astral.sh/uv/getting-started/installation/) :  
- On Windows, enter the following command in PowerShell :
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- On Linux and MacOS, enter the following in a terminal :
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

Once uv is installed, from the command line (PowerShell in Windows), install `pytdo` with uv :
```
uv tool install pytdo
```

`pytdo` will be installed along its dependencies in an isolated environment with no risks to mess up with your current tools and Python versions.

Then, launch the GUI by running `pytdo` from the command line.

To update, run : `uv tool upgrade pytdo`.

### Method 2 : As a library
Installing `pytdo` as a library will allow you to use the graphical user interface but also use the backend library from scripts and Jupyter notebooks (e.g. you will be able to import it with `import pytdo`).
Note that you can use the same environment than the one for [`pyuson`](https://gitlab.in2p3.fr/himagnetos/pyuson).

1. Create a Python environment with Python 3.12 :
    
    You can use your favorite Python environment manager. With [conda](https://conda-forge.org/miniforge/), this would be :
    ```
    conda create -n pytdo-env -c conda-forge python=3.12
    ```

    You may replace the environment name `pytdo-env` with whatever you want.

    Activate the environment with :
    ```
    conda activate pytdo-env
    ```

2. Install the `pytdo` package :

    With `pip`, with the `pytdo-env` activated : 
    ```
    pip install pytdo
    ```

#### Updates
To upgrade `pytdo` to the latest version, simply run from the activated environment :
```
pip install pytdo --upgrade
```

#### Manual download
1. Download the repository and extract it on your computer (or clone it).
2. Create and activate a conda environment as shown above.
3. Install the extracted repository with `pip` :
```
pip install "/path/to/pytdo-main"
```

Alternatively, if you wish to make modification to the source code so that your change is reflected immediately, use the editable mode :
```
pip install -e /path/to/pytdo-main
```

## Usage
You can use this package through the graphical user interface, or directly from the Python shell, script or Jupyter notebook using the `TDOProcessor` class. All this methods rely on a TOML configuration file that specifies the experiment parameters and analysis settings.

A template configuration file is provided in the `configs` folder. Copy-paste and edit it according to your need. Each entry of the file is commented so it should be somewhat straightforward to configure. Then :

- Run the graphical interface with `python -m pytdo` from a terminal with the `pyuson-env` environment activated. Drag & drop the configuration file in the window, load the data, extract the TDO signal and interactively choose the field-window in which the signal is detrended.
- Write your own script using the library :
    ```python
    import pytdo

    cfg_filename = "/path/to/your/config.toml"
    r = pytdo.TDOProcessor(cfg_filename)
    r.extract_tdo().remove_background().fft_inverse()
    r.save_results_csv()
    ```