<img src="https://gitlab.in2p3.fr/metis-geophysics/pyckster/-/raw/master/images/pyckster.png?ref_type=heads" alt="pyckster" width="200"/>

[![pipeline status](https://gitlab.in2p3.fr/metis-geophysics/pyckster/badges/master/pipeline.svg)](https://gitlab.in2p3.fr/metis-geophysics/pyckster/-/commits/master) 
[![GitLab Tag](https://img.shields.io/gitlab/v/tag/metis-geophysics%2Fpyckster?gitlab_url=https%3A%2F%2Fgitlab.in2p3.fr)](https://gitlab.in2p3.fr/metis-geophysics/pyckster/-/tags)
[![PyPI - Version](https://img.shields.io/pypi/v/pyckster)](https://pypi.org/project/pyckster/)
[![PyPI Downloads](https://static.pepy.tech/badge/pyckster)](https://pepy.tech/projects/pyckster)
![PyPI - Downloads](https://img.shields.io/pypi/dm/PyCKSTER)

PyCKSTER is an open-source PyQt5-based GUI for processing and analysis of active near-surface seismic data, with a focus on traveltime picking and surface wave dispersion analysis.

**Core Features:**
- **File I/O**: Read and write seismic files in SEG2, SEGY, and Seismic Unix (SU) formats
- **Data Editing**: Edit headers information (source and trace coordinates, topography integration, delay, ffid) and traces (move, swap, mute, delete) 
- **Traveltime Analysis**: Interactive picking with multiple visualization options (source/geophone diagrams, hodochrones) and direct inversion using [pyGIMLi](https://www.pygimli.org)
- **Surface Wave Analysis**: Compute dispersion images using phase-shift transform, simple windowing with interactive picking capabilities, and import/export dispersion curves with [SWIP](https://github.com/spasquet/SWIP) MATLAB package compatibility.

**Coming Soon**: Advanced dispersion windowing and stacking, surface wave dispersion inversion

Picked traveltimes are saved in pyGIMLi's unified format for seamless subsurface velocity model reconstruction.

## Installation

PyCKSTER has now a built-in inversion module based on pyGIMLi. So far it seems to work better if pyGIMLi is installed first:
``` bash
conda create -n pyckster -c gimli -c conda-forge "pygimli>=1.5.0" "suitesparse=5"
```

Then you can simply download the package from PyPi:
``` bash
pip install pyckster
```

To update PyCKSTER, run the following command:
``` bash
pip install pyckster --upgrade
```

## Troubleshooting

If numpy > 2 is installed in your environment, you might not be able to run pygimli. If so you can downgrade numpy with the following command :
``` bash
pip install numpy==1.26.4 --upgrade
```

## Running PyCKSTER

Open a terminal and run:
```bash
pyckster
```
## How to use PyCKSTER

### Mouse Controls

- **Left click**: Add a single pick at cursor position
- **Left drag**: Pan the plot
- **Ctrl + Left drag**: Draw freehand picks along multiple traces
- **Middle click**: Remove a single pick
- **Middle drag**: Pan the plot
- **Ctrl + Middle drag**: Select and remove multiple picks in a rectangle
- **Right click**: Context menu with plot options
- **Right drag**: Zoom along axes (horizontal or vertical)
- **Ctrl + Right drag**: Rectangle zoom (zoom to selected area)

Here is an example of PyCKSTER in action:

<img src="https://gitlab.in2p3.fr/metis-geophysics/pyckster/-/raw/master/images/screenshot_01.png?ref_type=heads"/>

More detailed instructions coming soon...

## Author
PyCKSTER is currently developped by [Sylvain Pasquet](https://orcid.org/0000-0002-3625-9212)\
[sylvain.pasquet@sorbonne-universite.fr](sylvain.pasquet@sorbonne-universite.fr)


*CNRS, Sorbonne Université*\
*UAR 3455 OSU OMA TERRA*\
*UMR 7619 METIS*


Any feedback or help is welcome.

## Licence

PyCKSTER is distributed under the terms of the GPLv3 license. Details on
the license agreement can be found [here].

[here]: LICENCE