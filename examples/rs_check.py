from ohmpi import OhmPi
import matplotlib.pyplot as plt
import numpy as np
os.chdir("/home/pi/OhmPi")
sys.path.append("/home/pi/OhmPi")

a = np.arange(13) + 1
b = a + 3
m = a + 1
n = a + 2
seq = np.c_[a, b, m, n]

k = OhmPi(idps=True, use_mux=True)
k.settings['injection_duration'] = .5
k.sequence = seq

k.rs_check(tx_volt=5)
