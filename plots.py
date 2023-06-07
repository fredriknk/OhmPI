import matplotlib.pyplot as plt
import numpy as np


def plot_fulldata(fulldata, axes=None, fig=None, save=False, output="fulldata.png", show=False, realtime=False,
                  xlim=None, plot_ads=False):

    if axes is None:
        fig, (ax1,ax2) = plt.subplots(2, sharex=True)
    else:
        (ax1,ax2) = axes

    line1, = ax1.plot(fulldata[:, 2], fulldata[:, 0], 'r.-', label='current [mA]')
    ax1.set_ylabel('Current (mA)')
    ax1.set_title('Current')
    line2, = ax2.plot(fulldata[:, 2], fulldata[:, 1], '.-', label='Voltage [mV]',alpha=.5)
    if plot_ads:
        line3, = ax2.plot(fulldata[:, 2], fulldata[:, 3], '.-', label='Voltage U0 [mV]', alpha=.5)
        line4, = ax2.plot(fulldata[:, 2], fulldata[:, 4], '.-', label='Voltage U2 [mV]', alpha=.5)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (mV)')
    ax2.set_title('Voltage')

    if xlim is not None:
        ax1.set_xlim(xlim)
        ax2.set_xlim(xlim)

    if save:
        fig.savefig(output,dpi=300,bbox_inches='tight')
    if show:
        plt.show()
    
    if realtime:
        fig.canvas.draw()
        fig.canvas.flush_events()
        if plot_ads:
           return fig, (ax1,ax2), (line1,line2)
        else:
            return fig, (ax1, ax2), (line1, line2, line3, line4)
    else:
        return fig, (ax1, ax2)


def update_realtime_fulldata_plot(last_measurement, acquired_dataset, lines, axes, fig, x_window=10, plot_ads=False):
    (ax1,ax2) = axes
    t = np.append(acquired_dataset[:,2], last_measurement[:, 2][~np.isnan(last_measurement[:, 2])] + acquired_dataset[:,2][-1])
    i_rt = np.append(acquired_dataset[:,0], last_measurement[:, 0][~np.isnan(last_measurement[:, 2])])
    u_rt = np.append(acquired_dataset[:,1], last_measurement[:, 1][~np.isnan(last_measurement[:, 2])])
    lines[0].set_ydata(i_rt)
    lines[0].set_xdata(t)
    lines[1].set_ydata(u_rt)
    lines[1].set_xdata(t)
    if plot_ads:
        lines[2].set_ydata(u_rt)
        lines[2].set_xdata(t)
        lines[3].set_ydata(u_rt)
        lines[3].set_xdata(t)

    ax1.relim()
    ax2.relim()
    ax1.autoscale_view(scalex=False)
    ax2.autoscale_view(scalex=False)
    ax1.set_xlim([t[-1] - x_window, t[-1]])
    ax2.set_xlim([t[-1] - x_window, t[-1]])

    fig.canvas.draw()
    fig.canvas.flush_events()
    
    return fig,(ax1,ax2), lines, np.array([i_rt,u_rt,t]).T