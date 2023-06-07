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
#k.reset_mux()
k.ohmpi_to_bert('/home/pi/OhmPi/data/measurement_20230607T111139.csv','ABMN.txt','coord.txt')