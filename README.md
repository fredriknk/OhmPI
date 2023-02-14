# OhmPi

[![Build Status](https://gitlab.irstea.fr/%{project_path}/badges/%{default_branch}/pipeline.svg)](https://reversaal.gitlab.irstea.page/OhmPi)

Development of a low-cost multi-electrodes resistivity meter for electrical resistivity mesaurement for lab applications, based on raspberry board

## Installation

All dependencies are specified in *requirements.txt*

**Note:** all instructions below should be typed in the terminal

It is first necessary to create an OhmPi virtual environment and install all dependancies
`.create_ohmpi_virtual_envrinment.sh`

When the installation is completed check that requirements are met using 
`pip list`


We strongly recommend users to create a virtual environment to run the code and installed all required dependencies:
*  activate it using the following command:
   `source ohmpy/bin/activate`
*  you should run you code within the virtual environment
*  to leave the virtual environment simply type: `deactivate`

## First run with four electrodes

In the examples folder, you will find the code "simple_measurement.py".

Running this code, in Thonny (IDE) or in the terminal, will allow you to make a simple 4 electrodes measurement A B M N.


## Citing Ohmpi

If you use Ohmpi for you work, please cite [this paper](https://www.sciencedirect.com/science/article/pii/S2468067220300316) as:

    Rémi Clement, Yannick Fargier, Vivien Dubois, Julien Gance, Emile Gros, Nicolas Forquet, OhmPi: An open source data logger for 
    dedicated applications of electrical resistivity imaging at the small and laboratory scale, HardwareX, Volume 8, 2020, e00122, ISSN 2468-0672, https://doi.org/10.1016/j.ohx.2020.e00122..


## License information

You may redistribute and modify this documentation and make products using it under the terms of the CERN-OHL-P v2 (https:/cern.ch/cern-ohl). This documentation is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE. Please see the CERN-OHL-P v2 for applicable conditions
