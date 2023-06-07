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
k.test_led()