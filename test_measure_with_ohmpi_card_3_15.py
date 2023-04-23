import numpy as np
import matplotlib.pyplot as plt
from utils import change_config
change_config('config_ohmpi_card_3_15.py', verbose=False)
from OhmPi.measure import OhmPiHardware

k = OhmPiHardware()
# Test #1:
print('Testing _vab_pulse')
k._vab_pulse(vab=12, length=1., sampling_rate=k.rx.sampling_rate, polarity=1)
r = k.readings[:,2]/k.readings[:,1]
print(f'Mean resistance: {np.mean(r):.3f} Ohms, Dev. {100*np.std(r)/np.mean(r):.1f} %')
print(f'sampling rate: {k.rx.sampling_rate:.1f} ms, mean sample spacing: {np.mean(np.diff(k.readings[:,0]))*1000.:.1f} ms')

# Test #2:
print('\n\nTesting vab_square_wave')
k.vab_square_wave(vab=12, cycle_length=2., sampling_rate=k.rx.sampling_rate, cycles=3)
r = k.readings[:,2]/k.readings[:,1]
print(f'Mean resistance: {np.mean(r):.3f} Ohms, Dev. {100*np.std(r)/np.mean(r):.1f} %')
print(f'sampling rate: {k.rx.sampling_rate:.1f} ms, mean sample spacing: {np.mean(np.diff(k.readings[:,0]))*1000.:.1f} ms')
print(r)
print(f'length of array: {len(r)}, expected length: {6000./k.rx.sampling_rate}')
print(k.readings)
fig, ax = plt.subplots()
ax.plot(k.readings[:,0], k.readings[:,1], '-r')
ax.plot(k.readings[:,0], k.readings[:,2], '-b')
change_config('config_default.py', verbose=False)
