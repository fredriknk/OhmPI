from ohmpi import OhmPi
import matplotlib.pyplot as plt
import numpy as np

# a = np.arange(13) + 1
# b = a + 3
# m = a + 1
# n = a + 2
# seq = np.c_[a, b, m, n]

k = OhmPi(idps=True)
k.settings['injection_duration'] = 1
k.settings['nbr_meas'] = 1
#k.sequence = seq
#k.reset_mux()
#k.switch_mux_on([1, 4, 2, 3])
#k.switch_mux_on([12, 15, 13, 14])
#k.measure(strategy='vmax')
#print('vab', k.compute_tx_volt(strategy='vmin'))
#k.rs_check()

R1=11.5 #sol
R2=200 # contact



out = k.run_measurement(quad=[1, 2, 3, 4], nb_stack=2, tx_volt=2, strategy='vmax', autogain=True)
print(k.sequence)

data = out['fulldata']
inan = ~np.isnan(data[:,0])
print(['R1:',R1,' ','R2:',R2,' ', out['R [ohm]'],out['Vmn [mV]'],out['I [mA]'],out['Ps [mV]'],out['nbStack'],out['Tx [V]']])
f=open(r'data_goog.txt','a+')
f.write("\n")
f.write('R1:'+';'+ str(R1)+';'+'R2:'+';'+str(R2)+';'+ str(out['R [ohm]'])+';' + str(out['Vmn [mV]'])+';' + str(out['I [mA]'])+';'+ str(out['Ps [mV]'])+';'+ str(out['nbStack'])+';'+ str(out['Tx [V]']))
f.close()

k.append_and_save('out_test_qualite.csv', out)

# out = k.run_measurement(quad=[1, 2, 3, 4], nb_stack=2, tx_volt=2, strategy='vmin', autogain=True)
# 
# data = out['fulldata']
# inan = ~np.isnan(data[:,0])
# print(out['R [ohm]'])
# k.append_and_save('out_test_qualite.csv', out)
# 
# out = k.run_measurement(quad=[1, 2, 3, 4], nb_stack=2, tx_volt=5, strategy='constant', autogain=True)
# 
# data = out['fulldata']
# inan = ~np.isnan(data[:,0])
# print(out['R [ohm]'])
# k.append_and_save('out_test_qualite.csv', out)

if True:
    fig, axs = plt.subplots(2, 1, sharex=True)
    ax = axs[0]
    ax.plot(data[inan,2], data[inan,0], 'r.-', label='current [mA]')
    ax.set_ylabel('Current AB [mA]')
    ax = axs[1]
    ax.plot(data[inan,2], data[inan,1], '.-', label='voltage [mV]')
    ax.set_ylabel('Voltage MN [mV]')
    ax.set_xlabel('Time [s]')
    plt.show()
    
#     fig,ax=plt.subplots()
#     
#    
#     ax.plot(data[inan,2], data[inan,0],  label='current [mA]', marker="o")
#     ax2=ax.twinx()
#     ax2.plot(data[inan,2], data[inan,1],'r.-' , label='current [mV]')
#     ax2.set_ylabel('Voltage [mV]', color='r')
#     ymin=-50
#     ymax=50
#     ymin1=-4500
#     ymax1= 4500
#     ax.set_ylim([ymin,ymax])
#     ax2.set_ylim([ymin1,ymax1])
#     
#     plt.show()
    


if False:
    from numpy.fft import fft, ifft

    x = data[inan, 1][10:300]
    t = np.linspace(0, len(x)*4, len(x))
    sr = 1/0.004

    X = fft(x)
    N = len(X)
    n = np.arange(N)
    T = N/sr
    freq = n/T 

    plt.figure(figsize = (12, 6))
    plt.subplot(121)

    plt.stem(freq, np.abs(X), 'b', \
             markerfmt=" ", basefmt="-b")
    plt.xlabel('Freq (Hz)')
    plt.ylabel('FFT Amplitude |X(freq)|')
    #plt.xlim(0, 10)

    plt.subplot(122)
    plt.plot(t, ifft(X), 'r')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    plt.show()
