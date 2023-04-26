import importlib
import datetime
import time

import numpy as np
from OhmPi.logging_setup import create_stdout_logger
from OhmPi.config import HARDWARE_CONFIG
from threading import Thread, Event

controller_module = importlib.import_module(f'OhmPi.hardware.{HARDWARE_CONFIG["controller"]["model"]}')
tx_module = importlib.import_module(f'OhmPi.hardware.{HARDWARE_CONFIG["tx"]["model"]}')
rx_module = importlib.import_module(f'OhmPi.hardware.{HARDWARE_CONFIG["rx"]["model"]}')
mux_module = importlib.import_module(f'OhmPi.hardware.{HARDWARE_CONFIG["mux"]["model"]}')
TX_CONFIG = tx_module.TX_CONFIG
RX_CONFIG = rx_module.RX_CONFIG
MUX_CONFIG = mux_module.MUX_CONFIG

current_max = np.min([TX_CONFIG['current_max'], MUX_CONFIG['current_max']])
voltage_max = np.min([TX_CONFIG['voltage_max'], MUX_CONFIG['voltage_max']])
voltage_min = RX_CONFIG['voltage_min']

def elapsed_seconds(start_time):
    lap = datetime.datetime.utcnow() - start_time
    return lap.total_seconds()

class OhmPiHardware:
    def __init__(self, **kwargs):
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_hw')
        self.data_logger = kwargs.pop('exec_logger', None)
        if self.data_logger is None:
            self.data_logger = create_stdout_logger('data_hw')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_hw')
        self.tx_sync = Event()
        self.controller = kwargs.pop('controller',
                                     controller_module.Controller(exec_logger=self.exec_logger,
                                                                   data_logger=self.data_logger,
                                                                   soh_logger=self.soh_logger))
        self.rx = kwargs.pop('rx', rx_module.Rx(exec_logger=self.exec_logger,
                                                 data_logger=self.data_logger,
                                                 soh_logger=self.soh_logger,
                                                 controller=self.controller))
        self.tx = kwargs.pop('tx', tx_module.Tx(exec_logger=self.exec_logger,
                                                 data_logger=self.data_logger,
                                                 soh_logger=self.soh_logger,
                                                 controller=self.controller))
        self.mux = kwargs.pop('mux', mux_module.Mux(exec_logger=self.exec_logger,
                                                    data_logger=self.data_logger,
                                                    soh_logger=self.soh_logger,
                                                    controller=self.controller))
        self.readings = np.array([])  # time series of acquired data
        self._start_time = None  # time of the beginning of a readings acquisition
        self._pulse = 0  # pulse number

    def _clear_values(self):
        self.readings = np.array([])
        self._start_time = None
        self._pulse = 0

    def _inject(self, duration):
            self.tx_sync.set()
            self.tx.voltage_pulse(length=duration)
            self.tx_sync.clear()

    @property
    def pulses(self):
        pulses = {}
        for i in np.unique(self.readings[:,1]):
            r = self.readings[self.readings[:, 1] == i, :]
            assert np.all(np.isclose(r[:,2], r[0, 2]))  # Polarity cannot change within a pulse
            pulses.update({i: {'polarity': int(r[0, 2]), 'iab': r[:,3], 'vmn' : r[:,4]}})  # TODO: check how to generalize in case of multi-channel RX
        return pulses

    def _read_values(self, sampling_rate, append=False):  # noqa
        if not append:
            self._clear_values()
            _readings = []
        else:
            _readings = self.readings.tolist()
        sample = 0
        self.tx_sync.wait()
        if not append or self._start_time is None:
            self._start_time = datetime.datetime.utcnow()
        while self.tx_sync.is_set():
            lap = datetime.datetime.utcnow()
            _readings.append([elapsed_seconds(self._start_time), self._pulse, self.tx.polarity, self.tx.current,
                              self.rx.voltage])
            sample+=1
            sleep_time = self._start_time + datetime.timedelta(seconds = sample * sampling_rate / 1000) - lap
            time.sleep(np.min([0, np.abs(sleep_time.total_seconds())]))
        self.readings = np.array(_readings)
        self._pulse += 1

    @property
    def sp(self):
        if len(self.readings[self.readings[:,2]==1, :]) < 1 or len(self.readings[self.readings[:,2]==-1, :]) < 1:
            self.exec_logger.warning('Unable to compute sp: readings should at least contain one positive and one negative pulse')
            return 0.
        else:
            n_pulses = int(np.max(self.readings[:, 1]))
            polarity = np.array([np.mean(self.readings[self.readings[:, 1] == i, 2]) for i in range(n_pulses + 1)])
            mean_vmn = []
            mean_iab = []
            for i in range(n_pulses + 1):
                mean_vmn.append(np.mean(self.readings[self.readings[:, 1] == i, 4]))
                mean_iab.append(np.mean(self.readings[self.readings[:, 1] == i, 3]))
            mean_vmn = np.array(mean_vmn)
            mean_iab = np.array(mean_iab)
            # print(f'Vmn: {mean_vmn}, Iab: {mean_iab}')  # TODO: delete me
            sp = np.mean(mean_vmn[np.ix_(polarity==1)] - mean_vmn[np.ix_(polarity==-1)]) / 2
            return sp

    def _compute_tx_volt(self, best_tx_injtime=0.1, strategy='vmax', tx_volt=5,
                         vab_max=voltage_max, vmn_min=voltage_min):
        """Estimates best Tx voltage based on different strategies.
        At first a half-cycle is made for a short duration with a fixed
        known voltage. This gives us Iab and Rab. We also measure Vmn.
        A constant c = vmn/iab is computed (only depends on geometric
        factor and ground resistivity, that doesn't change during a
        quadrupole). Then depending on the strategy, we compute which
        vab to inject to reach the minimum/maximum Iab current or
        min/max Vmn.
        This function also compute the polarity on Vmn (on which pin
        of the ADS1115 we need to measure Vmn to get the positive value).

        Parameters
        ----------
        best_tx_injtime : float, optional
            Time in milliseconds for the half-cycle used to compute Rab.
        strategy : str, optional
            Either:
            - vmax : compute Vab to reach a maximum Iab without exceeding vab_max
            - vmin : compute Vab to reach at least vmn_min
            - constant : apply given Vab
        tx_volt : float, optional
            Voltage to apply for guessing the best voltage. 5 V applied
            by default. If strategy "constant" is chosen, constant voltage
            to applied is "tx_volt".
        vab_max : float, optional
            Maximum injection voltage to apply to tx (used by all strategies)
        vmn_min : float, optional
            Minimum voltage target for rx (used by vmin strategy)

        Returns
        -------
        vab : float
            Proposed Vab according to the given strategy.
        polarity:
            Polarity of VMN relative to polarity of VAB
        rab : float
            Resistance between injection electrodes
        """

        vab_max = np.abs(vab_max)
        vmn_min = np.abs(vmn_min)
        vab = np.min([np.abs(tx_volt), vab_max])
        self.tx.polarity = 1
        self.tx.turn_on()
        if self.rx.sampling_rate*1000 > best_tx_injtime:
            sampling_rate = best_tx_injtime
        else:
            sampling_rate = self.tx.sampling_rate
        self._vab_pulse(vab=vab, length=best_tx_injtime, sampling_rate=sampling_rate)
        vmn = np.mean(self.readings[:,4])
        iab = np.mean(self.readings[:,3])
        # if np.abs(vmn) is too small (smaller than voltage_min), strategy is not constant and vab < vab_max ,
        # then we could call _compute_tx_volt with a tx_volt increased to np.min([vab_max, tx_volt*2.]) for example
        if strategy == 'vmax':
            # implement different strategies
            if vab < vab_max and iab < current_max :
                vab = vab * np.min([0.9 * vab_max / vab, 0.9 * current_max / iab])  # TODO: check if setting at 90% of max as a safety margin is OK
            self.tx.exec_logger.debug(f'vmax strategy: setting VAB to {vab} V.')
        elif strategy == 'vmin':
            if vab <= vab_max and iab < current_max:
                vab = vab * np.min([0.9 * vab_max / vab, vmn_min / np.abs(vmn), 0.9 * current_max / iab])  # TODO: check if setting at 90% of max as a safety margin is OK
        elif strategy != 'constant':
            self.tx.exec_logger.warning(f'Unknown strategy {strategy} for setting VAB! Using {vab} V')
        else:
            self.tx.exec_logger.debug(f'Constant strategy for setting VAB, using {vab} V')
        self.tx.turn_off()
        self.tx.polarity = 0
        rab = (np.abs(vab) * 1000.) / iab
        self.exec_logger.debug(f'RAB = {rab:.2f} Ohms')
        if vmn < 0:
            polarity = -1  # TODO: check if we really need to return polarity
        else:
            polarity = 1
        return vab, polarity, rab

    def vab_square_wave(self, vab, cycle_length, sampling_rate, cycles=3, polarity=1, append=False):
        self.tx.polarity = polarity
        lengths = [cycle_length/2]*2*cycles  # TODO: delete me
        print(f'vab_square_wave lengths: {lengths}')
        self._vab_pulses(vab, lengths, sampling_rate, append=append)

    def _vab_pulse(self, vab, length, sampling_rate=None, polarity=None, append=False):
        """ Gets VMN and IAB from a single voltage pulse
        """

        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if polarity is not None and polarity != self.tx.polarity:
            self.tx.polarity = polarity
        self.tx.voltage = vab
        injection = Thread(target=self._inject, kwargs={'duration':length})
        readings = Thread(target=self._read_values, kwargs={'sampling_rate': sampling_rate, 'append': append})
        # set gains automatically
        self.tx.adc_gain_auto()
        self.rx.adc_gain_auto()
        readings.start()
        injection.start()
        readings.join()
        injection.join()

    def _vab_pulses(self, vab, lengths, sampling_rate, polarities=None, append=False):
        n_pulses = len(lengths)
        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if polarities is not None:
            assert len(polarities)==n_pulses
        else:
            polarities = [-self.tx.polarity * np.heaviside(i % 2, -1.) for i in range(n_pulses)]
        if not append:
            self._clear_values()
        print(f'Polarities: {polarities}, sampling_rate: {sampling_rate}') # TODO: delete me
        for i in range(n_pulses):
            self._vab_pulse(self, length=lengths[i], sampling_rate=sampling_rate, polarity=polarities[i], append=True)