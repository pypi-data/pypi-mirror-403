<p align="center">
    <a href="https://mbd.pages.rwth-aachen.de/psimpy/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="http://hdl.handle.net/2262/103542">View Publication</a>
    ·
    <a href="https://mbd.pages.rwth-aachen.de/psimpy/examples.html">View Example</a>
    ·
    <a href="https://git.rwth-aachen.de/mbd/psimpy/-/issues">Report Bug</a>
    ·
    <a href="https://git.rwth-aachen.de/mbd/psimpy/-/issues">Request Feature</a>
</p>

<!-- omit in toc -->
## Table of Contents
<!-- TOC -->

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Installation in a Conda Environment (Recommended)](#installation-in-a-conda-environment-recommended)
- [Documentation](#documentation)
- [Usage](#usage)
- [Cite as](#cite-as)
  - [Corresponding publications](#corresponding-publications)
- [Research Studies Using Psimpy](#research-studies-using-psimpy)
- [License](#license)
<!-- /TOC -->

## Description

`PSimPy` (Predictive and probabilistic simulation with Python) implements
a Gaussian process emulation-based framework that enables systematic and
efficient investigation of uncertainties associated with physics-based models
(i.e. simulators).

## Prerequisites

Before installing and using `PSimPy`, please ensure that you have the following
prerequisites:\
(Please note that we will cover number 1 to 3 in our recommended installation
method: [Installation in a Conda Environment](#installation-in-a-conda-environment-recommended).)

1. **Python 3.9 or later**:\
    Make sure you have Python installed on your system. You can download the latest
version of Python from the official website:
[Python Downloads](https://www.python.org/downloads/)
2. **R Installed and Added to the PATH Environment Variable**:
   - Install R from the official [R Project](https://www.r-project.org/) website.
   - Add R to your system's PATH environment variable. This step is crucial for
   enabling communication between Python and R.
3. (Optional) **RobustGaSP - R package**:\
   The emulator module, `robustgasp.py`, relies on the R package [RobustGaSP](https://cran.r-project.org/web/packages/RobustGaSP/index.html). This has also been initegrated with other PSimPy modules, such as `active_learning.py`. In order to utilize these modules, make sure to install the R package [RobustGaSP](https://cran.r-project.org/web/packages/RobustGaSP/index.html) first.
4. (Optional) **r.avaflow - Mass Flow Simulation Tool**:\
`PSimPy` includes a simulator module, `ravaflow3G.py`, that interfaces
with the open source software [r.avaflow 3G](https://www.landslidemodels.org/r.avaflow/). If you intend to use this module, please refer to the official documentation of [r.avaflow 3G](https://www.landslidemodels.org/r.avaflow/) to for installation guide.

## Installation

`PSimPy` can be installed using `pip`.

```bash
$ pip install psimpy
```

This command will install the package along with its dependencies.

### Installation in a Conda Environment (Recommended)

We recommond you to install `PSimPy` in a virtual environment such as a `conda`
environment. In this section, we will ceate a `conda` environment with prerequisites (number 1 to 3), and install `PSimPy` in this environment. You may want to first install [Anaconda](https://docs.anaconda.com/free/anaconda/) or [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/) if you haven't. The steps afterwards are as follows:

1. Create a conda environment with Python, R, and RobustGaSP, and activate the environment:

    ```bash
    conda create --name your_env_name python r-base conda-forge::r-robustgasp
    conda activate your_env_name
    ```

2. Install `PSimPy` using `pip` in your conda environment:

    ```bash
    pip install psimpy
    ```

Now you should have `PSimPy` and its dependencies successfully installed in your
conda environment. You can use it in the Python terminal or in your Python IDE.

**Quick Note on R_HOME in Conda Environments:**

If you're running PSimPy in a conda environment without a predefined R_HOME variable, we automatically set it to the default R installation path of the active conda environment. This ensures PSimPy works smoothly with R without needing manual setup. If you prefer setting R_HOME yourself, please define it before starting PSimPy to use a custom R environment.

## Documentation
Detailed documentation of `PSimPy` is hosted at https://mbd.pages.rwth-aachen.de/psimpy/,
including the API and theory (or reference) of each module. 


## Usage
Usage examples are provided by the [Example Gallery](https://mbd.pages.rwth-aachen.de/psimpy/examples.html).


## Cite as

```bibtex
@misc{psimpy,
  author = {Hu Zhao},
  title = {PSimPy : Predictive and probabilistic simulation with Python},
  year = {2022},
  howpublished = {\url{https://git.rwth-aachen.de/mbd/psimpy}},
}
``` 

### Corresponding publications

Hu Zhao, Anil Yildiz, Nazanin Bagherinejad, Julia Kowalski, PSimPy: GP emulation-based sensitivity analysis, uncertainty quantification and calibration of landslide simulators, 14th International Conference on Applications of Statistics and Probability in Civil Engineering (ICASP14), Dublin, Ireland, 2023. http://hdl.handle.net/2262/103542

```bibtex
@InProceedings{zhao_et_al_2023,
  title       = {PSimPy: GP emulation-based sensitivity analysis, uncertainty quantification and calibration of landslide simulators},
  booktitle   = {14th International Conference on Applications of Statistics and Probability in Civil Engineering, ICASP14},
  author      = {Zhao, Hu and Yildiz, Anil and Bagherinejad, Nazanin and Kowalski, Julia},
  year        = {2023},
  address     = {{Dublin, Ireland}},
  note = {Available at \url{http://hdl.handle.net/2262/103542}},
}
``` 


## Research Studies Using Psimpy

- Tillmann, S., Behr, M., & Elgeti, S. (2024). Using Bayesian optimization for warpage compensation in injection molding. Materialwissenschaft und Werkstofftechnik, 55(1), 13-20.
- Correa, A. (2024, July 10). Seamless Reproducibility of Complex Simulation Workflows [Conference presentation]. JuliaCon 2024, Eindhoven, Netherlands. https://pretalx.com/juliacon2024/talk/FJRZL7/
- Kumar, V. M. and Kowalski, J.: A unified Bayesian model selection workflow for geophysical free-surface flow, EGU General Assembly 2024, Vienna, Austria, 14–19 Apr 2024, EGU24-18847, https://doi.org/10.5194/egusphere-egu24-18847, 2024.


## License

`PSimPy` was created by Hu Zhao at the Chair of Methods for Model-based
Development in Computational Engineering (RWTH Aachen University, Germany). It
is licensed under the terms of the MIT license.