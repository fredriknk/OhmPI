"""
Created on  May 23 2023
@author: reclement
Simple quadripole measurement with fullwave graph
"""


import sys
import os
os.chdir("/home/pi/OhmPi")

file_sequence='ABMN.txt'
file_coord='coord.txt'

sys.path.append("/home/pi/OhmPi")
from ohmpi import OhmPi
### Define object from class OhmPi
k = OhmPi(use_mux=True, idps=True)
### Update settings if needed 
k.update_settings({"nb_electrodes": 64})
k.update_settings({"injection_duration":0.25})
k.update_settings({"nb_stack": 1})
### Reset mux
k.reset_mux()
### Load Sequence
k.load_sequence(file_sequence)
filename = k.run_sequence(tx_volt = 5, strategy = 'constant', autogain=True, duty_cycle = 0.5, best_tx_injtime = 0.150, plot_realtime_fulldata=False)
k.ohmpi_to_bert(filename,file_sequence,file_coord)