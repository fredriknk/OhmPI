#!/bin/bash

# ensure that the libatlas-base-dev library is installed
sudo apt-get install -y libatlas-base-dev

# Create the virtual environment
python3 -m venv ohmpy

# Activate it
source ohmpy/bin/activate || exit 1  # NOTE: Added || exit to avoid installing requirements in system python if the virtual environment can't be loaded

# Solve issues associated to storage allocation
export CFLAGS=-fcommon

# install all required packages in the virtual environment.
pip install -r requirements.txt

