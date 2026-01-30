# PyMCCE

Python implementation of core functions from [Gunner Lab's MCCE](https://github.com/GunnerLab/MCCE4-Alpha)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

PyMCCE is a Python package that provides core functionality for molecular dynamics calculations and continuum electrostatics, inspired by the Multi-Conformation Continuum Electrostatics (MCCE) method from Gunner Lab.

## Features

- **Core MCCE Functions**: Python implementation of essential MCCE algorithms
- **MCCE Tools**: MCCE tools: PBE solver, SAS calculator, PDB donwloader, etc

## Installation

### From PyPI (when available)

```bash
pip install pymcce
```

### From Source

```bash
git clone https://github.com/newbooks/PyMCCE.git
cd PyMCCE
pip install -e .
```

## Project Structure

```
├── CONTRIBUTING.md                       # How to develop code
├── docs                                  # Documentation source files
│   └── README.md                         # How to write and deploy documentation
├── LICENSE                               # License
├── Makefile                              # Shortcut commands using make utility
├── pyproject.toml                        # Pip packaging configuration
├── README.md                             # Readme
├── src                                   # Project source
│   └── pymcce                            # Main project pymcce
│       ├── cli.py                        # App commands
│       ├── core.py                       # Pseudo code like program flow for the app commands
│       ├── data                          # Data file: default prm and ftpl
│       │   ├── ftpl
│       │   │   ├── ala.ftpl
│       │   │   ├── arg.ftpl
│       │   │   ├── asn.ftpl
│       │   │   ├── asp.ftpl
│       │   └── prm
│       │       └── run.prm.default
│       ├── mcce.py                       # MCCE class - MCCE specific structure and functions
│       ├── __init__.py                   # Define accessible modules for other programs to import
│       └── utils.py                      # Support functions - Not protein structure related
└── tests

```

## Development

### Setting up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/newbooks/PyMCCE.git
   cd PyMCCE
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Gunner Lab's MCCE](https://github.com/GunnerLab/MCCE4-Alpha) for the original implementation
- The scientific computing community for the tools and libraries that make this work possible

## Contact

- **Author**: Junjun Mao
- **Email**: junjun.mao@gmail.com
- **GitHub**: [newbooks/PyMCCE](https://github.com/newbooks/PyMCCE)

## Roadmap

- [ ] Develop core MCCE algorithms &mdash; estimated 16 weeks
- [ ] Build MCCE tools &mdash; 4 weeks for pdbtools, 4 weeks for mccetools
- [ ] Write user documentation &mdash; estimated 2 weeks
- [ ] Prepare developer documentation &mdash; estimated 2 weeks
- [ ] Produce tutorial materials &mdash; estimated 2 weeks
- [ ] Optimize performance &mdash; ongoing

