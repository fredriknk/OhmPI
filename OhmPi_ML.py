from ohmpi import OhmPi
import matplotlib.pyplot as plt
import time
import numpy as np
import adafruit_ads1x15.ads1115 as ads  # noqa
from adafruit_ads1x15.analog_in import AnalogIn  # noqa

import os
from utils import get_platform
import json
import warnings
from copy import deepcopy
import numpy as np
import csv
import time
import shutil
from datetime import datetime
from termcolor import colored
import threading
from logging_setup import setup_loggers
from config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG, EXEC_LOGGING_CONFIG
from logging import DEBUG

# finish import (done only when class is instantiated as some libs are only available on arm64 platform)
try:
    import board  # noqa
    import busio  # noqa
    import adafruit_tca9548a  # noqa
    import adafruit_ads1x15.ads1115 as ads  # noqa
    from adafruit_ads1x15.analog_in import AnalogIn  # noqa
    from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
    from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
    import digitalio  # noqa
    from digitalio import Direction  # noqa
    from gpiozero import CPUTemperature  # noqa
    import minimalmodbus  # noqa

    arm64_imports = True
except ImportError as error:
    if EXEC_LOGGING_CONFIG['logging_level'] == DEBUG:
        print(colored(f'Import error: {error}', 'yellow'))
    arm64_imports = False
except Exception as error:
    print(colored(f'Unexpected error: {error}', 'red'))
    arm64_imports = None

def append_and_save_new(filename: str, last_measurement: dict, cmd_id=None):
    """Appends and saves the last measurement dict.

    Parameters
    ----------
    filename : str
        filename to save the last measurement dataframe
    last_measurement : dict
        Last measurement taken in the form of a python dictionary
    cmd_id : str, optional
        Unique command identifier
    """
    last_measurement = deepcopy(last_measurement)
    if 'fulldata' in last_measurement:
        d = last_measurement['fulldata']
        n = d.shape[0]
        if n > 1:
            idic = dict(zip(['i' + str(i) for i in range(n)], d[:, 0]))
            udic = dict(zip(['u' + str(i) for i in range(n)], d[:, 1]))
            tdic = dict(zip(['t' + str(i) for i in range(n)], d[:, 2]))
            uxdic = dict(zip(['ux' + str(i) for i in range(n)], d[:, 3]))
            uydic = dict(zip(['uy' + str(i) for i in range(n)], d[:, 4]))
            last_measurement.update(idic)
            last_measurement.update(udic)
            last_measurement.update(tdic)
            last_measurement.update(uxdic)
            last_measurement.update(uydic)
        last_measurement.pop('fulldata')

    if os.path.isfile(filename):
        # Load data file and append data to it
        with open(filename, 'a') as f:
            w = csv.DictWriter(f, last_measurement.keys())
            w.writerow(last_measurement)
            # last_measurement.to_csv(f, header=False)
    else:
        # create data file and add headers
        with open(filename, 'a') as f:
            w = csv.DictWriter(f, last_measurement.keys())
            w.writeheader()
            w.writerow(last_measurement)

# def _read_voltage(self,ads,ads_pin):
#
def run_measurement_old(self, quad=None, nb_stack=None, injection_duration=None,
                    autogain=True, strategy='constant', tx_volt=5, best_tx_injtime=0.1,
                    cmd_id=None, duty_cycle=0.9):
    """Measures on a quadrupole and returns transfer resistance.

    Parameters
    ----------
    quad : iterable (list of int)
        Quadrupole to measure, just for labelling. Only switch_mux_on/off
        really create the route to the electrodes.
    nb_stack : int, optional
        Number of stacks. A stacl is considered two half-cycles (one
        positive, one negative).
    injection_duration : int, optional
        Injection time in seconds.
    autogain : bool, optional
        If True, will adapt the gain of the ADS1115 to maximize the
        resolution of the reading.
    strategy : str, optional
        (V3.0 only) If we search for best voltage (tx_volt == 0), we can choose
        vmax strategy : find the highest voltage that stays in the range
        For a constant value, just set the tx_volt.
    tx_volt : float, optional
        (V3.0 only) If specified, voltage will be imposed. If 0, we will look
        for the best voltage. If the best Tx cannot be found, no
        measurement will be taken and values will be NaN.
    best_tx_injtime : float, optional
        (V3.0 only) Injection time in seconds used for finding the best voltage.
    cmd_id : str, optional
        Unique command identifier
    """
    self.exec_logger.debug('Starting measurement')
    self.exec_logger.debug('Waiting for data')
    # check arguments
    if quad is None:
        quad = [0, 0, 0, 0]

    if self.on_pi:
        if nb_stack is None:
            nb_stack = self.settings['nb_stack']
        if injection_duration is None:
            injection_duration = self.settings['injection_duration']
        tx_volt = float(tx_volt)

        # inner variable initialization
        sum_i = 0
        sum_vmn = 0
        sum_ps = 0

        # let's define the pin again as if we run through measure()
        # as it's run in another thread, it doesn't consider these
        # and this can lead to short circuit!

        self.pin0 = self.mcp_board.get_pin(0)
        self.pin0.direction = Direction.OUTPUT
        self.pin0.value = False
        self.pin1 = self.mcp_board.get_pin(1)
        self.pin1.direction = Direction.OUTPUT
        self.pin1.value = False
        self.pin7 = self.mcp_board.get_pin(7)  # IHM on mesaurement
        self.pin7.direction = Direction.OUTPUT
        self.pin7.value = False

        if self.sequence is None:
            if self.idps:
                # self.switch_dps('on')
                self.pin2 = self.mcp_board.get_pin(2)  # dsp +
                self.pin2.direction = Direction.OUTPUT
                self.pin2.value = True
                self.pin3 = self.mcp_board.get_pin(3)  # dsp -
                self.pin3.direction = Direction.OUTPUT
                self.pin3.value = True
                time.sleep(4)

        self.pin5 = self.mcp_board.get_pin(5)  # IHM on mesaurement
        self.pin5.direction = Direction.OUTPUT
        self.pin5.value = True
        self.pin6 = self.mcp_board.get_pin(6)  # IHM on mesaurement
        self.pin6.direction = Direction.OUTPUT
        self.pin6.value = False
        self.pin7 = self.mcp_board.get_pin(7)  # IHM on mesaurement
        self.pin7.direction = Direction.OUTPUT
        self.pin7.value = False
        if self.idps:
            if self.DPS.read_register(0x05, 2) < 11:
                self.pin7.value = True  # max current allowed (100 mA for relays) #voltage

        # get best voltage to inject AND polarity
        if self.idps:
            tx_volt, polarity, Rab = self._compute_tx_volt(
                best_tx_injtime=best_tx_injtime, strategy=strategy, tx_volt=tx_volt, autogain=autogain)
            self.exec_logger.debug(f'Best vab found is {tx_volt:.3f}V')
        else:
            polarity = 1
            Rab = None

        # first reset the gain to 2/3 before trying to find best gain (mode 0 is continuous)
        self.ads_current = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860,
                                       address=self.ads_current_address, mode=0)
        self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860,
                                       address=self.ads_voltage_address, mode=0)
        # turn on the power supply
        start_delay = None
        end_delay = None
        out_of_range = False
        if self.idps:
            if not np.isnan(tx_volt):
                self.DPS.write_register(0x0000, tx_volt, 2)  # set tx voltage in V
                self.DPS.write_register(0x09, 1)  # DPS5005 on
                time.sleep(0.3)
            else:
                self.exec_logger.debug('No best voltage found, will not take measurement')
                out_of_range = True

        if not out_of_range:  # we found a Vab in the range so we measure
            gain = 2 / 3
            self.ads_voltage = ads.ADS1115(self.i2c, gain=gain, data_rate=860,
                                           address=self.ads_voltage_address, mode=0)
            if autogain:

                # compute autogain
                gain_voltage = []
                for n in [0, 1]:  # make short cycle for gain computation

                    if n == 0:
                        self.pin0.value = True
                        self.pin1.value = False
                        if self.board_version == 'mb.2023.0.0':
                            self.pin6.value = True  # IHM current injection led on
                    else:
                        self.pin0.value = False
                        self.pin1.value = True  # current injection nr2
                        if self.board_version == 'mb.2023.0.0':
                            self.pin6.value = True  # IHM current injection led on

                    time.sleep(injection_duration)
                    gain_current = self._gain_auto(AnalogIn(self.ads_current, ads.P0))

                    if polarity > 0:
                        if n == 0:
                            gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))
                        else:
                            gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
                    else:
                        if n == 0:
                            gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
                        else:
                            gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))

                    self.pin0.value = False
                    self.pin1.value = False
                    time.sleep(injection_duration)
                    if n == 0:
                        gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))
                    else:
                        gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
                    if self.board_version == 'mb.2023.0.0':
                        self.pin6.value = False  # IHM current injection led off

                    gain = np.min(gain_voltage)
                self.exec_logger.debug(
                    f'Gain current: {gain_current:.3f}, gain voltage: {gain_voltage[0]:.3f}, '
                    f'{gain_voltage[1]:.3f}')
                self.ads_current = ads.ADS1115(self.i2c, gain=gain_current, data_rate=860,
                                               address=self.ads_current_address, mode=0)

            self.pin0.value = False
            self.pin1.value = False

            # one stack = 2 half-cycles (one positive, one negative)
            pinMN = 0 if polarity > 0 else 2  # noqa

            # sampling for each stack at the end of the injection
            sampling_interval = 10  # ms    # TODO: make this a config option
            self.nb_samples = int(
                injection_duration * 1000 // sampling_interval) + 1  # TODO: check this strategy

            # full data for waveform
            fulldata = []

            #  we sample every 10 ms (as using AnalogIn for both current
            # and voltage takes about 7 ms). When we go over the injection
            # duration, we break the loop and truncate the meas arrays
            # only the last values in meas will be taken into account
            start_time = time.time()  # start counter
            for n in range(0, nb_stack * 2):  # for each half-cycles
                # current injection
                if (n % 2) == 0:
                    self.pin0.value = True
                    self.pin1.value = False
                    if autogain:  # select gain computed on first half cycle
                        self.ads_voltage = ads.ADS1115(self.i2c, gain=(gain_voltage[0]), data_rate=860,
                                                       address=self.ads_voltage_address, mode=0)
                else:
                    self.pin0.value = False
                    self.pin1.value = True  # current injection nr2
                    if autogain:  # select gain computed on first half cycle
                        self.ads_voltage = ads.ADS1115(self.i2c, gain=(gain_voltage[1]), data_rate=860,
                                                       address=self.ads_voltage_address, mode=0)
                self.exec_logger.debug(f'Stack {n} {self.pin0.value} {self.pin1.value}')
                if self.board_version == 'mb.2023.0.0':
                    self.pin6.value = True  # IHM current injection led on
                # measurement of current i and voltage u during injection
                meas = np.zeros((self.nb_samples, 5)) * np.nan
                start_delay = time.time()  # stating measurement time
                dt = 0
                k = 0
                for k in range(0, self.nb_samples):
                    # reading current value on ADS channels
                    meas[k, 0] = (AnalogIn(self.ads_current, ads.P0).voltage * 1000) / (50 * self.r_shunt)
                    if self.board_version == 'mb.2023.0.0':
                        if pinMN == 0:
                            meas[k, 1] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                            meas[k, 3] = meas[k, 1]
                            meas[k, 4] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1.0
                        else:
                            meas[k, 1] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1.0
                            meas[k, 4] = meas[k, 1]
                            meas[k, 3] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.

                    elif self.board_version == '22.10':
                        meas[k, 1] = -AnalogIn(self.ads_voltage, ads.P0, ads.P1).voltage * self.coef_p2 * 1000
                    # else:
                    #    self.exec_logger.debug('Unknown board')
                    time.sleep(sampling_interval / 1000)
                    dt = time.time() - start_delay  # real injection time (s)
                    meas[k, 2] = time.time() - start_time
                    if dt > (injection_duration - 0 * sampling_interval / 1000.):
                        break

                # stop current injection
                self.pin0.value = False
                self.pin1.value = False
                self.pin6.value = False  # IHM current injection led on
                end_delay = time.time()

                # truncate the meas array if we didn't fill the last samples  #TODO: check why
                meas = meas[:k + 1]

                # measurement of current i and voltage u during off time
                print(duty_cycle)
                measpp = np.zeros((int(meas.shape[0]*(1/duty_cycle-1)), 5)) * np.nan
                print(measpp.shape)
                time.sleep(sampling_interval / 1000)
                start_delay_off = time.time()  # stating measurement time
                dt = 0
                for k in range(0, measpp.shape[0]):
                    # reading current value on ADS channels
                    measpp[k, 0] = (AnalogIn(self.ads_current, ads.P0).voltage * 1000.) / (50 * self.r_shunt)
                    if self.board_version == 'mb.2023.0.0':
                        #print('crenau %i sample %i'%(n,k))
                        if pinMN == 0:
                           measpp[k, 1] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                           measpp[k, 3] = measpp[k, 1]
                           measpp[k, 4] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1.0
                        else:
                            measpp[k, 3] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                            measpp[k, 1] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1.0
                            measpp[k, 4] = measpp[k, 1]

                    elif self.board_version == '22.10':
                        measpp[k, 1] = -AnalogIn(self.ads_voltage, ads.P0,
                                                 ads.P1).voltage * self.coef_p2 * 1000.
                    else:
                        self.exec_logger.debug('unknown board')
                    time.sleep(sampling_interval / 1000)
                    dt = time.time() - start_delay_off  # real injection time (s)
                    measpp[k, 2] = time.time() - start_time
                    if dt > (injection_duration - 0 * sampling_interval / 1000.):
                        break

                end_delay_off = time.time()

                # truncate the meas array if we didn't fill the last samples
                measpp = measpp[:k + 1]

                # we alternate on which ADS1115 pin we measure because of sign of voltage
                if pinMN == 0:
                    pinMN = 2  # noqa
                else:
                    pinMN = 0  # noqa

                # store data for full wave form
                fulldata.append(meas)
                fulldata.append(measpp)

            # TODO get battery voltage and warn if battery is running low
            # TODO send a message on SOH stating the battery level

            # let's do some calculation (out of the stacking loop)

            # i_stack = np.empty(2 * nb_stack, dtype=object)
            # vmn_stack = np.empty(2 * nb_stack, dtype=object)
            i_stack, vmn_stack = [], []
            # select appropriate window length to average the readings
            window = int(np.min([f.shape[0] for f in fulldata[::2]]) // 3)
            for n, meas in enumerate(fulldata[::2]):
                # take average from the samples per stack, then sum them all
                # average for the last third of the stacked values
                #  is done outside the loop
                i_stack.append(meas[-int(window):, 0])
                vmn_stack.append(meas[-int(window):, 1])

                sum_i = sum_i + (np.mean(meas[-int(meas.shape[0] // 3):, 0]))
                vmn1 = np.mean(meas[-int(meas.shape[0] // 3), 1])
                if (n % 2) == 0:
                    sum_vmn = sum_vmn - vmn1
                    sum_ps = sum_ps + vmn1
                else:
                    sum_vmn = sum_vmn + vmn1
                    sum_ps = sum_ps + vmn1

        else:
            sum_i = np.nan
            sum_vmn = np.nan
            sum_ps = np.nan
            fulldata = None

        if self.idps:
            self.DPS.write_register(0x0000, 0, 2)  # reset to 0 volt
            self.DPS.write_register(0x09, 0)  # DPS5005 off

        # reshape full data to an array of good size
        # we need an array of regular size to save in the csv
        if not out_of_range:
            fulldata = np.vstack(fulldata)
            # we create a big enough array given nb_samples, number of
            # half-cycles (1 stack = 2 half-cycles), and twice as we
            # measure decay as well
            a = np.zeros((nb_stack * self.nb_samples * 2 * 2, 5)) * np.nan
            a[:fulldata.shape[0], :] = fulldata
            fulldata = a
        else:
            np.array([[]])

        vmn_stack_mean = np.mean(
            [np.diff(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) / 2 for i in range(nb_stack)])
        vmn_std = np.sqrt(np.std(vmn_stack[::2]) ** 2 + np.std(
            vmn_stack[1::2]) ** 2)  # np.sum([np.std(vmn_stack[::2]),np.std(vmn_stack[1::2])])
        i_stack_mean = np.mean(i_stack)
        i_std = np.mean(np.array([np.std(i_stack[::2]), np.std(i_stack[1::2])]))
        r_stack_mean = vmn_stack_mean / i_stack_mean
        r_stack_std = np.sqrt((vmn_std / vmn_stack_mean) ** 2 + (i_std / i_stack_mean) ** 2) * r_stack_mean
        ps_stack_mean = np.mean(
            np.array([np.mean(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) for i in range(nb_stack)]))

        # create a dictionary and compute averaged values from all stacks
        # if self.board_version == 'mb.2023.0.0':
        d = {
            "time": datetime.now().isoformat(),
            "A": quad[0],
            "B": quad[1],
            "M": quad[2],
            "N": quad[3],
            "inj time [ms]": (end_delay - start_delay) * 1000. if not out_of_range else 0.,
            "Vmn [mV]": sum_vmn / (2 * nb_stack),
            "I [mA]": sum_i / (2 * nb_stack),
            "R [ohm]": sum_vmn / sum_i,
            "Ps [mV]": sum_ps / (2 * nb_stack),
            "nbStack": nb_stack,
            "Tx [V]": tx_volt if not out_of_range else 0.,
            "CPU temp [degC]": CPUTemperature().temperature,
            "Nb samples [-]": self.nb_samples,
            "fulldata": fulldata,
            "I_stack [mA]": i_stack_mean,
            "I_std [mA]": i_std,
            "I_per_stack [mA]": np.array([np.mean(i_stack[i * 2:i * 2 + 2]) for i in range(nb_stack)]),
            "Vmn_stack [mV]": vmn_stack_mean,
            "Vmn_std [mV]": vmn_std,
            "Vmn_per_stack [mV]": np.array(
                [np.diff(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1))[0] / 2 for i in range(nb_stack)]),
            "R_stack [ohm]": r_stack_mean,
            "R_std [ohm]": r_stack_std,
            "R_per_stack [Ohm]": np.mean(
                [np.diff(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) / 2 for i in range(nb_stack)]) / np.array(
                [np.mean(i_stack[i * 2:i * 2 + 2]) for i in range(nb_stack)]),
            "PS_per_stack [mV]": np.array(
                [np.mean(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) for i in range(nb_stack)]),
            "PS_stack [mV]": ps_stack_mean,
            "R_ab [ohm]": Rab,
            "Gain_Vmn": gain
        }

    else:  # for testing, generate random data
        d = {'time': datetime.now().isoformat(), 'A': quad[0], 'B': quad[1], 'M': quad[2], 'N': quad[3],
             'R [ohm]': np.abs(np.random.randn(1)).tolist()}

    # to the data logger
    dd = d.copy()
    dd.pop('fulldata')  # too much for logger
    dd.update({'A': str(dd['A'])})
    dd.update({'B': str(dd['B'])})
    dd.update({'M': str(dd['M'])})
    dd.update({'N': str(dd['N'])})

    # round float to 2 decimal
    for key in dd.keys():
        if isinstance(dd[key], float):
            dd[key] = np.round(dd[key], 3)

    dd['cmd_id'] = str(cmd_id)
    self.data_logger.info(dd)
    self.pin5.value = False  # IHM led on measurement off
    if self.sequence is None:
        self.switch_dps('off')
    
    return d

def run_measurement_new(self, quad=None, nb_stack=None, injection_duration=None,
                        autogain=True, strategy='constant', tx_volt=5, best_tx_injtime=0.1, duty_cycle=0.5,
                        cmd_id=None):
    """Measures on a quadrupole and returns transfer resistance.

    Parameters
    ----------
    quad : iterable (list of int)
        Quadrupole to measure, just for labelling. Only switch_mux_on/off
        really create the route to the electrodes.
    nb_stack : int, optional
        Number of stacks. A stacl is considered two half-cycles (one
        positive, one negative).
    injection_duration : int, optional
        Injection time in seconds.
    autogain : bool, optional
        If True, will adapt the gain of the ADS1115 to maximize the
        resolution of the reading.
    strategy : str, optional
        (V3.0 only) If we search for best voltage (tx_volt == 0), we can choose
        vmax strategy : find the highest voltage that stays in the range
        For a constant value, just set the tx_volt.
    tx_volt : float, optional
        (V3.0 only) If specified, voltage will be imposed. If 0, we will look
        for the best voltage. If the best Tx cannot be found, no
        measurement will be taken and values will be NaN.
    best_tx_injtime : float, optional
        (V3.0 only) Injection time in seconds used for finding the best voltage.
    duty_cycle : float, optional, default: 0.5
        Ratio of time between injection duration and no injection duration during a half-cycle
        It should be comprised between 0.5 (no injection duration same as injection duration) and 1 (no injection
        duration equal to 0)
    cmd_id : str, optional
        Unique command identifier
    """
    self.exec_logger.debug('Starting measurement')
    self.exec_logger.debug('Waiting for data')

    # check arguments
    if quad is None:
        quad = [0, 0, 0, 0]

    if self.on_pi:
        if nb_stack is None:
            nb_stack = self.settings['nb_stack']
        if injection_duration is None:
            injection_duration = self.settings['injection_duration']
        tx_volt = float(tx_volt)

        # inner variable initialization
        sum_i = 0
        sum_vmn = 0
        sum_ps = 0

        # let's define the pin again as if we run through measure()
        # as it's run in another thread, it doesn't consider these
        # and this can lead to short circuit!

        self.pin0 = self.mcp_board.get_pin(0)
        self.pin0.direction = Direction.OUTPUT
        self.pin0.value = False
        self.pin1 = self.mcp_board.get_pin(1)
        self.pin1.direction = Direction.OUTPUT
        self.pin1.value = False
        self.pin7 = self.mcp_board.get_pin(7)  # IHM on mesaurement
        self.pin7.direction = Direction.OUTPUT
        self.pin7.value = False

        if self.sequence is None:
            if self.idps:
                # self.switch_dps('on')
                self.pin2 = self.mcp_board.get_pin(2)  # dsp +
                self.pin2.direction = Direction.OUTPUT
                self.pin2.value = True
                self.pin3 = self.mcp_board.get_pin(3)  # dsp -
                self.pin3.direction = Direction.OUTPUT
                self.pin3.value = True
                time.sleep(4)

        self.pin5 = self.mcp_board.get_pin(5)  # IHM on mesaurement
        self.pin5.direction = Direction.OUTPUT
        self.pin5.value = True
        self.pin6 = self.mcp_board.get_pin(6)  # IHM on mesaurement
        self.pin6.direction = Direction.OUTPUT
        self.pin6.value = False
        self.pin7 = self.mcp_board.get_pin(7)  # IHM on mesaurement
        self.pin7.direction = Direction.OUTPUT
        self.pin7.value = False
        if self.idps:
            if self.DPS.read_register(0x05, 2) < 11:
                self.pin7.value = True  # max current allowed (100 mA for relays) #voltage

        # get best voltage to inject AND polarity
        if self.idps:
            tx_volt, polarity, Rab = self._compute_tx_volt(
                best_tx_injtime=best_tx_injtime, strategy=strategy, tx_volt=tx_volt, autogain=autogain)
            self.exec_logger.debug(f'Best vab found is {tx_volt:.3f}V')
        else:
            polarity = 1
            Rab = None

        # first reset the gain to 2/3 before trying to find best gain (mode 0 is continuous)
        self.ads_current = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860,
                                       address=self.ads_current_address, mode=0)
        self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860,
                                       address=self.ads_voltage_address, mode=0)
        # turn on the power supply
        start_delay = None
        end_delay = None
        out_of_range = False
        if self.idps:
            if not np.isnan(tx_volt):
                self.DPS.write_register(0x0000, tx_volt, 2)  # set tx voltage in V
                self.DPS.write_register(0x09, 1)  # DPS5005 on
                time.sleep(0.3)
            else:
                self.exec_logger.debug('No best voltage found, will not take measurement')
                out_of_range = True

        if not out_of_range:  # we found a Vab in the range so we measure
            gain = 2 / 3
            self.ads_voltage = ads.ADS1115(self.i2c, gain=gain, data_rate=860,
                                           address=self.ads_voltage_address, mode=0)
            if autogain:
                # compute autogain
                gain_voltage = []
                for n in [0, 1]:  # make short cycle for gain computation
                    if n == 0:
                        self.pin0.value = True
                        self.pin1.value = False
                        if self.board_version == 'mb.2023.0.0':
                            self.pin6.value = True  # IHM current injection led on
                    else:
                        self.pin0.value = False
                        self.pin1.value = True  # current injection nr2
                        if self.board_version == 'mb.2023.0.0':
                            self.pin6.value = True  # IHM current injection led on

                    time.sleep(best_tx_injtime)
                    gain_current = self._gain_auto(AnalogIn(self.ads_current, ads.P0))
                    gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))
                    gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
                    # if polarity > 0:
                    #     if n == 0:
                    #         gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))
                    #     else:
                    #         gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
                    # else:
                    #     if n == 0:
                    #         gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
                    #     else:
                    #         gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))

                    self.pin0.value = False
                    self.pin1.value = False
                    time.sleep(best_tx_injtime)
                    # if n == 0:
                    #     gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))
                    # else:
                    #     gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
                    if self.board_version == 'mb.2023.0.0':
                        self.pin6.value = False  # IHM current injection led off
                    gain = np.min(gain_voltage)
                self.exec_logger.debug(f'Gain current: {gain_current:.3f}, gain voltage: {gain_voltage[0]:.3f}, '
                                       f'{gain_voltage[1]:.3f}')
                self.ads_current = ads.ADS1115(self.i2c, gain=gain_current, data_rate=860,
                                               address=self.ads_current_address, mode=0)

            self.pin0.value = False
            self.pin1.value = False

            # one stack = 2 half-cycles (one positive, one negative)
            pinMN = 0 if polarity > 0 else 2  # noqa

            # sampling for each stack at the end of the injection
            sampling_interval = 10  # ms    # TODO: make this a config option
            self.nb_samples = int(injection_duration * 1000 // sampling_interval) + 1  # TODO: check this strategy

            # full data for waveform
            fulldata = []

            #  we sample every 10 ms (as using AnalogIn for both current
            # and voltage takes about 7 ms). When we go over the injection
            # duration, we break the loop and truncate the meas arrays
            # only the last values in meas will be taken into account
            start_time = time.time()  # start counter
            for n in range(0, nb_stack * 2):  # for each half-cycles
                # current injection
                if (n % 2) == 0:
                    self.pin0.value = True
                    self.pin1.value = False
                    if autogain:  # select gain computed on first half cycle
                        self.ads_voltage = ads.ADS1115(self.i2c, gain=np.min(gain_voltage), data_rate=860,
                                                       address=self.ads_voltage_address, mode=0)
                else:
                    self.pin0.value = False
                    self.pin1.value = True  # current injection nr2
                    if autogain:  # select gain computed on first half cycle
                        self.ads_voltage = ads.ADS1115(self.i2c, gain=np.min(gain_voltage), data_rate=860,
                                                       address=self.ads_voltage_address, mode=0)
                self.exec_logger.debug(f'Stack {n} {self.pin0.value} {self.pin1.value}')
                if self.board_version == 'mb.2023.0.0':
                    self.pin6.value = True  # IHM current injection led on
                # measurement of current i and voltage u during injection
                meas = np.zeros((self.nb_samples, 5)) * np.nan
                start_delay = time.time()  # stating measurement time
                dt = 0
                k = 0
                for k in range(0, self.nb_samples):
                    # reading current value on ADS channels
                    meas[k, 0] = (AnalogIn(self.ads_current, ads.P0).voltage * 1000) / (50 * self.r_shunt)
                    if self.board_version == 'mb.2023.0.0':
                        # if pinMN == 0:
                        #     meas[k, 1] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                        #     meas[k, 3] = meas[k, 1]
                        #     meas[k, 4] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1.0
                        # else:
                        #     meas[k, 1] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1.0
                        #     meas[k, 4] = meas[k, 1]
                        #     meas[k, 3] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                        u0 = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                        u2 = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000.
                        u = np.max([u0, u2]) * (np.heaviside(u0 - u2, 1.) * 2 - 1.)
                        meas[k, 1] = u
                        meas[k, 3] = u0
                        meas[k, 4] = u2 *-1.0
                    elif self.board_version == '22.10':
                        meas[k, 1] = -AnalogIn(self.ads_voltage, ads.P0, ads.P1).voltage * self.coef_p2 * 1000
                    # else:
                    #    self.exec_logger.debug('Unknown board')
                    time.sleep(sampling_interval / 1000)
                    dt = time.time() - start_delay  # real injection time (s)
                    meas[k, 2] = time.time() - start_time
                    if dt > (injection_duration - 0 * sampling_interval / 1000.):
                        break

                # stop current injection
                self.pin0.value = False
                self.pin1.value = False
                if self.board_version == 'mb.2023.0.0':
                    self.pin6.value = False  # IHM current injection led on
                end_delay = time.time()

                # truncate the meas array if we didn't fill the last samples  #TODO: check why
                meas = meas[:k + 1]

                # measurement of current i and voltage u during off time
                measpp = np.zeros((int(meas.shape[0] * (1 / duty_cycle - 1)), 5)) * np.nan
                time.sleep(sampling_interval / 1000)
                start_delay_off = time.time()  # stating measurement time
                dt = 0
                for k in range(0, measpp.shape[0]):
                    # reading current value on ADS channels
                    measpp[k, 0] = (AnalogIn(self.ads_current, ads.P0).voltage * 1000.) / (50 * self.r_shunt)
                    if self.board_version == 'mb.2023.0.0':
                        # if pinMN == 0:
                        #     measpp[k, 1] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                        #     measpp[k, 3] = measpp[k, 1]
                        #     measpp[k, 4] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1.0
                        # else:
                        #     measpp[k, 3] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                        #     measpp[k, 1] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1.0
                        #     measpp[k, 4] = measpp[k, 1]
                        u0 = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                        u2 = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000.
                        u = np.max([u0, u2]) * (np.heaviside(u0 - u2, 1.) * 2 - 1.)
                        measpp[k, 1] = u
                        measpp[k, 3] = u0
                        measpp[k, 4] = u2*-1.0
                    elif self.board_version == '22.10':
                        measpp[k, 1] = -AnalogIn(self.ads_voltage, ads.P0, ads.P1).voltage * self.coef_p2 * 1000.
                    else:
                        self.exec_logger.debug('unknown board')
                    time.sleep(sampling_interval / 1000)
                    dt = time.time() - start_delay_off  # real injection time (s)
                    measpp[k, 2] = time.time() - start_time
                    if dt > (injection_duration - 0 * sampling_interval / 1000.):
                        break

                end_delay_off = time.time()

                # truncate the meas array if we didn't fill the last samples
                measpp = measpp[:k + 1]

                # we alternate on which ADS1115 pin we measure because of sign of voltage
                if pinMN == 0:
                    pinMN = 2  # noqa
                else:
                    pinMN = 0  # noqa

                # store data for full wave form
                fulldata.append(meas)
                fulldata.append(measpp)

            # TODO get battery voltage and warn if battery is running low
            # TODO send a message on SOH stating the battery level

            # let's do some calculation (out of the stacking loop)

            # i_stack = np.empty(2 * nb_stack, dtype=object)
            # vmn_stack = np.empty(2 * nb_stack, dtype=object)
            i_stack, vmn_stack = [], []
            # select appropriate window length to average the readings
            window = int(np.min([f.shape[0] for f in fulldata[::2]]) // 3)
            for n, meas in enumerate(fulldata[::2]):
                # take average from the samples per stack, then sum them all
                # average for the last third of the stacked values
                #  is done outside the loop
                i_stack.append(meas[-int(window):, 0])
                vmn_stack.append(meas[-int(window):, 1])

                sum_i = sum_i + (np.mean(meas[-int(meas.shape[0] // 3):, 0]))
                vmn1 = np.mean(meas[-int(meas.shape[0] // 3), 1])
                if (n % 2) == 0:
                    sum_vmn = sum_vmn - vmn1
                    sum_ps = sum_ps + vmn1
                else:
                    sum_vmn = sum_vmn + vmn1
                    sum_ps = sum_ps + vmn1

        else:
            sum_i = np.nan
            sum_vmn = np.nan
            sum_ps = np.nan
            fulldata = None

        if self.idps:
            self.DPS.write_register(0x0000, 0, 2)  # reset to 0 volt
            self.DPS.write_register(0x09, 0)  # DPS5005 off

        # reshape full data to an array of good size
        # we need an array of regular size to save in the csv
        if not out_of_range:
            fulldata = np.vstack(fulldata)
            # we create a big enough array given nb_samples, number of
            # half-cycles (1 stack = 2 half-cycles), and twice as we
            # measure decay as well
            a = np.zeros((nb_stack * self.nb_samples * 2 * 2, 5)) * np.nan
            a[:fulldata.shape[0], :] = fulldata
            fulldata = a
        else:
            np.array([[]])

        vmn_stack_mean = np.mean(
            [np.diff(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) / 2 for i in range(nb_stack)])
        vmn_std = np.sqrt(np.std(vmn_stack[::2]) ** 2 + np.std(
            vmn_stack[1::2]) ** 2)  # np.sum([np.std(vmn_stack[::2]),np.std(vmn_stack[1::2])])
        i_stack_mean = np.mean(i_stack)
        i_std = np.mean(np.array([np.std(i_stack[::2]), np.std(i_stack[1::2])]))
        r_stack_mean = vmn_stack_mean / i_stack_mean
        r_stack_std = np.sqrt((vmn_std / vmn_stack_mean) ** 2 + (i_std / i_stack_mean) ** 2) * r_stack_mean
        ps_stack_mean = np.mean(
            np.array([np.mean(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) for i in range(nb_stack)]))

        # create a dictionary and compute averaged values from all stacks
        # if self.board_version == 'mb.2023.0.0':
        d = {
            "time": datetime.now().isoformat(),
            "A": quad[0],
            "B": quad[1],
            "M": quad[2],
            "N": quad[3],
            "inj time [ms]": (end_delay - start_delay) * 1000. if not out_of_range else 0.,
            "Vmn [mV]": sum_vmn / (2 * nb_stack),
            "I [mA]": sum_i / (2 * nb_stack),
            "R [ohm]": sum_vmn / sum_i,
            "Ps [mV]": sum_ps / (2 * nb_stack),
            "nbStack": nb_stack,
            "Tx [V]": tx_volt if not out_of_range else 0.,
            "CPU temp [degC]": CPUTemperature().temperature,
            "Nb samples [-]": self.nb_samples,
            "fulldata": fulldata,
            "I_stack [mA]": i_stack_mean,
            "I_std [mA]": i_std,
            "I_per_stack [mA]": np.array([np.mean(i_stack[i * 2:i * 2 + 2]) for i in range(nb_stack)]),
            "Vmn_stack [mV]": vmn_stack_mean,
            "Vmn_std [mV]": vmn_std,
            "Vmn_per_stack [mV]": np.array(
                [np.diff(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1))[0] / 2 for i in range(nb_stack)]),
            "R_stack [ohm]": r_stack_mean,
            "R_std [ohm]": r_stack_std,
            "R_per_stack [ohm]": np.mean(
                [np.diff(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) / 2 for i in range(nb_stack)]) / np.array(
                [np.mean(i_stack[i * 2:i * 2 + 2]) for i in range(nb_stack)]),
            "PS_per_stack [mV]": np.array(
                [np.mean(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) for i in range(nb_stack)]),
            "PS_stack [mV]": ps_stack_mean,
            "R_ab [ohm]": Rab,
            "Gain_Vmn": gain
        }
        # print(np.array([(vmn_stack[i*2:i*2+2]) for i in range(nb_stack)]))
        # elif self.board_version == '22.10':
        #     d = {
        #         "time": datetime.now().isoformat(),
        #         "A": quad[0],
        #         "B": quad[1],
        #         "M": quad[2],
        #         "N": quad[3],
        #         "inj time [ms]": (end_delay - start_delay) * 1000. if not out_of_range else 0.,
        #         "Vmn [mV]": sum_vmn / (2 * nb_stack),
        #         "I [mA]": sum_i / (2 * nb_stack),
        #         "R [ohm]": sum_vmn / sum_i,
        #         "Ps [mV]": sum_ps / (2 * nb_stack),
        #         "nbStack": nb_stack,
        #         "Tx [V]": tx_volt if not out_of_range else 0.,
        #         "CPU temp [degC]": CPUTemperature().temperature,
        #         "Nb samples [-]": self.nb_samples,
        #         "fulldata": fulldata,
        #     }

    else:  # for testing, generate random data
        d = {'time': datetime.now().isoformat(), 'A': quad[0], 'B': quad[1], 'M': quad[2], 'N': quad[3],
             'R [ohm]': np.abs(np.random.randn(1)).tolist()}

    # to the data logger
    dd = d.copy()
    dd.pop('fulldata')  # too much for logger
    dd.update({'A': str(dd['A'])})
    dd.update({'B': str(dd['B'])})
    dd.update({'M': str(dd['M'])})
    dd.update({'N': str(dd['N'])})

    # round float to 2 decimal
    for key in dd.keys():
        if isinstance(dd[key], float):
            dd[key] = np.round(dd[key], 3)

    dd['cmd_id'] = str(cmd_id)
    self.data_logger.info(dd)
    self.pin5.value = False  # IHM led on measurement off
    if self.sequence is None:
        self.switch_dps('off')

    return d