"""
Created on  May 23 2023
@author: reclement
Simple quadripole measurement with fullwave graph
"""
import os
import numpy as np
import time
import matplotlib.pyplot as plt
os.chdir("/home/pi/OhmPi")
import sys
sys.path.append("/home/pi/OhmPi")
from ohmpi import OhmPi
### Define object from class OhmPi
k = OhmPi(use_mux=True, idps=True)
### Update settings if needed 
k.update_settings({"nb_electrodes": 64})
k.update_settings({"injection_duration":0.5})
k.update_settings({"nb_stack": 3})
### Reset mux
k.reset_mux()
### switch_mux_on on the selected quadrupole
k.switch_mux_on([1,4,2,3])
### run_measurement
#to measure Rho and IP duty_cycle=0.5
#to measure only Rho duty cycle = 0.98 , NEVERS WRITE 1
out = k.run_measurement(quad=[1,4,2,3], tx_volt = 10, strategy = 'constant', autogain=True, duty_cycle = 0.5, best_tx_injtime = 0.150)
### switch_mux_off on the selected quadrupole
#k.switch_mux_off([19,22,20,21])
### Save all data on txt file
k.append_and_save('simple_measurement.csv', out)
### Plot de result
data = out['fulldata']
inan = ~np.isnan(data[:,0])
fig, axs = plt.subplots(2, 1, sharex=True)
ax = axs[0]
ax.plot(data[inan,2], data[inan,0], 'r.-', label='current [mA]')
ax.set_ylabel('Current AB [mA]')
ax = axs[1]
ax.plot(data[inan,2], data[inan,1], '.-', label='voltage [mV]')
# ax.plot(data[inan,2], data[inan,3], '.-', label='voltage U0 [mV]')
# ax.plot(data[inan,2], data[inan,4], '.-', label='voltage U2 [mV]')
ax.set_ylabel('Voltage MN [mV]')
ax.set_xlabel('Time [s]')
ax.legend()

plt.grid(True)
plt.show()



