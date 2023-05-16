# -*- coding: utf-8 -*-
"""
created on January 6, 2020.
Updates dec 2023; in-depth refactoring May 2023.
Hardware: Licensed under CERN-OHL-S v2 or any later version
Software: Licensed under the GNU General Public License v3.0
Ohmpi.py is a program to control a low-cost and open hardware resistivity meters within the OhmPi project by
Rémi CLEMENT (INRAE), Vivien DUBOIS (INRAE), Hélène GUYARD (IGE), Nicolas FORQUET (INRAE), Yannick FARGIER (IFSTTAR)
Olivier KAUFMANN (UMONS), Arnaud WATLET (UMONS) and Guillaume BLANCHY (FNRS/ULiege).
"""

import os
import json
from copy import deepcopy
import numpy as np
import csv
import time
from shutil import rmtree
from threading import Thread
from inspect import getmembers, isfunction
from datetime import datetime
from termcolor import colored
from logging import DEBUG
from ohmpi.utils import get_platform
from ohmpi.logging_setup import setup_loggers
from ohmpi.config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG, EXEC_LOGGING_CONFIG
import ohmpi.deprecated as deprecated
from ohmpi.hardware_system import OhmPiHardware

# finish import (done only when class is instantiated as some libs are only available on arm64 platform)
try:
    arm64_imports = True
except ImportError as error:
    if EXEC_LOGGING_CONFIG['logging_level'] == DEBUG:
        print(colored(f'Import error: {error}', 'yellow'))
    arm64_imports = False
except Exception as error:
    print(colored(f'Unexpected error: {error}', 'red'))
    arm64_imports = None

VERSION = '3.0.0-alpha'


class OhmPi(object):
    """ OhmPi class.
    """

    def __init__(self, settings=None, sequence=None, mqtt=True, onpi=None):
        """Constructs the ohmpi object

        Parameters
        ----------
        settings:

        sequence:

        mqtt: bool, defaut: True
            if True publish on mqtt topics while logging, otherwise use other loggers only
        onpi: bool,None default: None
            if None, the platform on which the class is instantiated is determined to set on_pi to either True or False.
            if False the behaviour of an ohmpi will be partially emulated and return random data.
        """

        if onpi is None:
            _, onpi = get_platform()
        elif onpi:
            assert get_platform()[1]  # Checks that the system actually runs on a pi if onpi is True
        self.on_pi = onpi  # True if runs from the RaspberryPi with the hardware, otherwise False for random data # TODO : replace with dummy hardware?

        self._sequence = sequence
        self.nb_samples = 0
        self.status = 'idle'  # either running or idle
        self.thread = None  # contains the handle for the thread taking the measurement

        # set loggers
        self.exec_logger, _, self.data_logger, _, self.soh_logger, _, _, msg = setup_loggers(mqtt=mqtt)
        print(msg)

        # read in hardware parameters (config.py)
        self._hw = OhmPiHardware(**{'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                  'soh_logger': self.soh_logger})
        self.exec_logger.info('Hardware configured...')
        # default acquisition settings
        self.settings = {
            'injection_duration': 0.2,
            'nb_meas': 1,
            'sequence_delay': 1,
            'nb_stack': 1,
            'export_path': 'data/measurement.csv'
        }
        # read in acquisition settings
        if settings is not None:
            self.update_settings(settings)

        self.exec_logger.debug('Initialized with settings:' + str(self.settings))

        # read quadrupole sequence
        if sequence is not None:
            self.load_sequence(sequence)

        # set controller
        self.mqtt = mqtt
        self.cmd_id = None
        if self.mqtt:
            import paho.mqtt.client as mqtt_client

            self.exec_logger.debug(f"Connecting to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']}"
                                   f" on {MQTT_CONTROL_CONFIG['hostname']} broker")

            def connect_mqtt() -> mqtt_client:
                def on_connect(mqttclient, userdata, flags, rc):
                    if rc == 0:
                        self.exec_logger.debug(f"Successfully connected to control broker:"
                                               f" {MQTT_CONTROL_CONFIG['hostname']}")
                    else:
                        self.exec_logger.warning(f'Failed to connect to control broker. Return code : {rc}')

                client = mqtt_client.Client(f"ohmpi_{OHMPI_CONFIG['id']}_listener", clean_session=False)
                client.username_pw_set(MQTT_CONTROL_CONFIG['auth'].get('username'),
                                       MQTT_CONTROL_CONFIG['auth']['password'])
                client.on_connect = on_connect
                client.connect(MQTT_CONTROL_CONFIG['hostname'], MQTT_CONTROL_CONFIG['port'])
                return client

            try:
                self.exec_logger.debug(f"Connecting to control broker: {MQTT_CONTROL_CONFIG['hostname']}")
                self.controller = connect_mqtt()
            except Exception as e:
                self.exec_logger.debug(f'Unable to connect control broker: {e}')
                self.controller = None
            if self.controller is not None:
                self.exec_logger.debug(f"Subscribing to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']}")
                try:
                    self.controller.subscribe(MQTT_CONTROL_CONFIG['ctrl_topic'], MQTT_CONTROL_CONFIG['qos'])

                    msg = f"Subscribed to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']}" \
                          f" on {MQTT_CONTROL_CONFIG['hostname']} broker"
                    self.exec_logger.debug(msg)
                    print(colored(f'\u2611 {msg}', 'blue'))
                except Exception as e:
                    self.exec_logger.warning(f'Unable to subscribe to control topic : {e}')
                    self.controller = None
                publisher_config = MQTT_CONTROL_CONFIG.copy()
                publisher_config['topic'] = MQTT_CONTROL_CONFIG['ctrl_topic']
                publisher_config.pop('ctrl_topic')

                def on_message(client, userdata, message):
                    command = message.payload.decode('utf-8')
                    self.exec_logger.debug(f'Received command {command}')
                    self._process_commands(command)

                self.controller.on_message = on_message
            else:
                self.controller = None
                self.exec_logger.warning('No connection to control broker.'
                                         ' Use python/ipython to interact with OhmPi object...')

    @classmethod
    def get_deprecated_methods(cls):
        for i in getmembers(deprecated, isfunction):
            setattr(cls, i[0], i[1])

    @staticmethod
    def append_and_save(filename: str, last_measurement: dict, cmd_id=None):
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
                last_measurement.update(idic)
                last_measurement.update(udic)
                last_measurement.update(tdic)
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


    @staticmethod
    def _find_identical_in_line(quads):
        """Finds quadrupole where A and B are identical.
        If A and B were connected to the same electrode, we would create a short-circuit.

        Parameters
        ----------
        quads : numpy.ndarray
            List of quadrupoles of shape nquad x 4 or 1D vector of shape nquad.

        Returns
        -------
        output : numpy.ndarray 1D array of int
            List of index of rows where A and B are identical.
        """

        # if we have a 1D array (so only 1 quadrupole), make it a 2D array
        if len(quads.shape) == 1:
            quads = quads[None, :]

        output = np.where(quads[:, 0] == quads[:, 1])[0]

        return output

    def get_data(self, survey_names=None, cmd_id=None):
        """Get available data.
        
        Parameters
        ----------
        survey_names : list of str, optional
            List of filenames already available from the html interface. So
            their content won't be returned again. Only files not in the list
            will be read.
        cmd_id : str, optional
            Unique command identifier
        """
        # get all .csv file in data folder
        if survey_names is None:
            survey_names = []
        fnames = [fname for fname in os.listdir('data/') if fname[-4:] == '.csv']
        ddic = {}
        if cmd_id is None:
            cmd_id = 'unknown'
        for fname in fnames:
            if ((fname != 'readme.txt')
                    and ('_rs' not in fname)
                    and (fname.replace('.csv', '') not in survey_names)):
                try:
                    data = np.loadtxt('data/' + fname, delimiter=',',
                                      skiprows=1, usecols=(1, 2, 3, 4, 8))
                    data = data[None, :] if len(data.shape) == 1 else data
                    ddic[fname.replace('.csv', '')] = {
                        'a': data[:, 0].astype(int).tolist(),
                        'b': data[:, 1].astype(int).tolist(),
                        'm': data[:, 2].astype(int).tolist(),
                        'n': data[:, 3].astype(int).tolist(),
                        'rho': data[:, 4].tolist(),
                    }
                except Exception as e:
                    print(fname, ':', e)
        rdic = {'cmd_id': cmd_id, 'data': ddic}
        self.data_logger.info(json.dumps(rdic))
        return ddic

    def interrupt(self, cmd_id=None):
        """Interrupts the acquisition

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self.status = 'stopping'
        if self.thread is not None:
            self.thread.join()
            self.exec_logger.debug('Interrupted sequence acquisition...')
        else:
            self.exec_logger.debug('No sequence measurement thread to interrupt.')
        self.exec_logger.debug(f'Status: {self.status}')

    def load_sequence(self, filename: str, cmd_id=None):
        """Reads quadrupole sequence from file.

        Parameters
        ----------
        filename : str
            Path of the .csv or .txt file with A, B, M and N electrodes.
            Electrode index start at 1.
        cmd_id : str, optional
            Unique command identifier

        Returns
        -------
        sequence : numpy.ndarray
            Array of shape (number quadrupoles * 4).
        """
        self.exec_logger.debug(f'Loading sequence {filename}')
        sequence = np.loadtxt(filename, delimiter=" ", dtype=np.uint32)  # load quadrupole file

        if sequence is not None:
            self.exec_logger.debug(f'Sequence of {sequence.shape[0]:d} quadrupoles read.')

        # locate lines where electrode A == electrode B
        test_same_elec = self._find_identical_in_line(sequence)

        if len(test_same_elec) != 0:
            for i in range(len(test_same_elec)):
                self.exec_logger.error(f'An electrode index A == B detected at line {str(test_same_elec[i] + 1)}')
            sequence = None

        if sequence is not None:
            self.exec_logger.info(f'Sequence {filename} of {sequence.shape[0]:d} quadrupoles loaded.')
        else:
            self.exec_logger.warning(f'Unable to load sequence {filename}')
        self.sequence = sequence

    def _process_commands(self, message: str):
        """Processes commands received from the controller(s)

        Parameters
        ----------
        message : str
            message containing a command and arguments or keywords and arguments
        """
        status = False
        cmd_id = '?'
        try:
            decoded_message = json.loads(message)
            self.exec_logger.debug(f'Decoded message {decoded_message}')
            cmd_id = decoded_message.pop('cmd_id', None)
            cmd = decoded_message.pop('cmd', None)
            kwargs = decoded_message.pop('kwargs', None)
            self.exec_logger.debug(f"Calling method {cmd}({str(kwargs) if kwargs is not None else ''})")
            if cmd_id is None:
                self.exec_logger.warning('You should use a unique identifier for cmd_id')
            if cmd is not None:
                try:
                    if kwargs is None:
                        output = getattr(self, cmd)()
                    else:
                        output = getattr(self, cmd)(**kwargs)
                    status = True
                except Exception as e:
                    self.exec_logger.error(
                        f"Unable to execute {cmd}({str(kwargs) if kwargs is not None else ''}): {e}")
                    status = False
        except Exception as e:
            self.exec_logger.warning(f'Unable to decode command {message}: {e}')
            status = False
        finally:
            reply = {'cmd_id': cmd_id, 'status': status}
            reply = json.dumps(reply)
            self.exec_logger.debug(f'Execution report: {reply}')

    def quit(self, cmd_id=None):
        """Quits OhmPi

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """

        self.exec_logger.debug(f'Quitting ohmpi.py following command {cmd_id}')
        exit()

    def _read_hardware_config(self):
        """Reads hardware configuration from config.py
        """
        self.exec_logger.debug('Getting hardware config')
        self.id = OHMPI_CONFIG['id']  # ID of the OhmPi
        # self.r_shunt = OHMPI_CONFIG['R_shunt']  # reference resistance value in ohm
        # self.Imax = OHMPI_CONFIG['Imax']  # maximum current
        # self.exec_logger.debug(f'The maximum current cannot be higher than {self.Imax} mA')
        # self.coef_p2 = OHMPI_CONFIG['coef_p2']  # slope for current conversion for ads.P2, measurement in V/V
        # self.nb_samples = OHMPI_CONFIG['nb_samples']  # number of samples measured for each stack
        # self.version = OHMPI_CONFIG['version']  # hardware version
        # self.max_elec = OHMPI_CONFIG['max_elec']  # maximum number of electrodes
        # self.board_addresses = OHMPI_CONFIG['board_addresses']
        # self.board_version = OHMPI_CONFIG['board_version']
        # self.mcp_board_address = OHMPI_CONFIG['mcp_board_address']
        self.exec_logger.debug(f'OHMPI_CONFIG = {str(OHMPI_CONFIG)}')

    def remove_data(self, cmd_id=None):
        """Remove all data in the data folder

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self.exec_logger.debug(f'Removing all data following command {cmd_id}')
        rmtree('data')
        os.mkdir('data')

    def restart(self, cmd_id=None):
        """Restarts the Raspberry Pi

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """

        if self.on_pi:
            self.exec_logger.info(f'Restarting pi following command {cmd_id}...')
            os.system('reboot')
        else:
            self.exec_logger.warning('Not on Raspberry Pi, skipping reboot...')

    def run_measurement(self, quad=None, nb_stack=None, injection_duration=None,
                        autogain=True, strategy='constant', tx_volt=5., best_tx_injtime=0.1,
                        cmd_id=None):
        """Measures on a quadrupole and returns transfer resistance.

        Parameters
        ----------
        quad : iterable (list of int)
            Quadrupole to measure, just for labelling. Only switch_mux_on/off
            really create the route to the electrodes.
        nb_stack : int, optional
            Number of stacks. A stack is considered two pulses (one
            positive, one negative).
        injection_duration : int, optional
            Injection time in seconds.
        best_tx_injtime: float, optional
            ???
        autogain : bool, optional
            If True, will adapt the gain of the ADS1115 to maximize the
            resolution of the reading.
        strategy : str, optional
            (V3.0 only) If we search for best voltage (tx_volt == 0), we can choose
            vmax strategy : find the highest voltage that stays in the range
            For a constant value, just set the tx_volt.
        tx_volt : float, optional
            (V3.0 only) If specified, voltage will be imposed. If 0, we will look
            for the best voltage.
        cmd_id : str, optional
            Unique command identifier
        """
        self.exec_logger.debug('Starting measurement')
        self.exec_logger.debug('Waiting for data')

        # check arguments
        if quad is None:
            quad = [0, 0, 0, 0]
        if nb_stack is None:
            nb_stack = self.settings['nb_stack']
        if injection_duration is None:
                injection_duration = self.settings['injection_duration']
        tx_volt = float(tx_volt)
        d = {}
        if self.switch_mux_on(quad, cmd_id):
            self._hw.vab_square_wave(tx_volt, cycle_length=injection_duration*2, cycles=nb_stack)
            d = {
                "time": datetime.now().isoformat(),
                "A": quad[0],
                "B": quad[1],
                "M": quad[2],
                "N": quad[3],
                "inj time [ms]": injection_duration,  # NOTE: check this
                # "Vmn [mV]": sum_vmn / (2 * nb_stack),
                # "I [mA]": sum_i / (2 * nb_stack),
                # "R [ohm]": sum_vmn / sum_i,
                "Ps [mV]": self._hw.sp,
                "nbStack": nb_stack,
                "Tx [V]": tx_volt,
                "CPU temp [degC]": self._hw.ctl.cpu_temperature,
                "Nb samples [-]": len(self._hw.readings),  # TODO: use only samples after a delay in each pulse
                "fulldata": self._hw.readings[:, [0, -2, -1]],
                # "I_stack [mA]": i_stack_mean,
                # "I_std [mA]": i_std,
                # "I_per_stack [mA]": np.array([np.mean(i_stack[i*2:i*2+2]) for i in range(nb_stack)]),
                # "Vmn_stack [mV]": vmn_stack_mean,
                # "Vmn_std [mV]": vmn_std,
                # "Vmn_per_stack [mV]": np.array([np.diff(np.mean(vmn_stack[i*2:i*2+2], axis=1))[0] / 2 for i in range(nb_stack)]),
                # "R_stack [ohm]": r_stack_mean,
                # "R_std [ohm]": r_stack_std,
                # "R_per_stack [Ohm]": np.mean([np.diff(np.mean(vmn_stack[i*2:i*2+2], axis=1)) / 2 for i in range(nb_stack)]) / np.array([np.mean(i_stack[i*2:i*2+2]) for i in range(nb_stack)]),
                # "PS_per_stack [mV]":  np.array([np.mean(np.mean(vmn_stack[i*2:i*2+2], axis=1)) for i in range(nb_stack)]),
                # "PS_stack [mV]": ps_stack_mean,
                # "R_ab [ohm]": Rab
            }

            # to the data logger
            dd = d.copy()
            dd.pop('fulldata')  # too much for logger
            dd.update({'A': str(dd['A'])})
            dd.update({'B': str(dd['B'])})
            dd.update({'M': str(dd['M'])})
            dd.update({'N': str(dd['N'])})

            # round float to 2 decimal
            for key in dd.keys():  # Check why this is applied on keys and not values...
                if isinstance(dd[key], float):
                    dd[key] = np.round(dd[key], 3)

            dd['cmd_id'] = str(cmd_id)
            self.data_logger.info(dd)

        else:
            self.exec_logger.info(f'Skipping {quad}')
        self.switch_mux_off(quad, cmd_id)
        return d

    def run_multiple_sequences(self, cmd_id=None, sequence_delay=None, nb_meas=None, **kwargs):  # NOTE : could be renamed repeat_sequence
        """Runs multiple sequences in a separate thread for monitoring mode.
           Can be stopped by 'OhmPi.interrupt()'.
           Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        sequence_delay : int, optional
            Number of seconds at which the sequence must be started from each others.
        nb_meas : int, optional
            Number of time the sequence must be repeated.
        kwargs : dict, optional
            See help(k.run_measurement) for more info.
        """
        # self.run = True
        if sequence_delay is None:
            sequence_delay = self.settings['sequence_delay']
        sequence_delay = int(sequence_delay)
        if nb_meas is None:
            nb_meas = self.settings['nb_meas']
        self.status = 'running'
        self.exec_logger.debug(f'Status: {self.status}')
        self.exec_logger.debug(f'Measuring sequence: {self.sequence}')

        def func():
            for g in range(0, nb_meas):  # for time-lapse monitoring
                if self.status == 'stopping':
                    self.exec_logger.warning('Data acquisition interrupted')
                    break
                t0 = time.time()
                self.run_sequence(**kwargs)

                # sleeping time between sequence
                dt = sequence_delay - (time.time() - t0)
                if dt < 0:
                    dt = 0
                if nb_meas > 1:
                    time.sleep(dt)  # waiting for next measurement (time-lapse)
            self.status = 'idle'

        self.thread = Thread(target=func)
        self.thread.start()

    def run_sequence(self, cmd_id=None, **kwargs):
        """Runs sequence synchronously (=blocking on main thread).
           Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self.status = 'running'
        self.exec_logger.debug(f'Status: {self.status}')
        self.exec_logger.debug(f'Measuring sequence: {self.sequence}')
        t0 = time.time()
        self.reset_mux()
        
        # create filename with timestamp
        filename = self.settings["export_path"].replace('.csv',
                                                        f'_{datetime.now().strftime("%Y%m%dT%H%M%S")}.csv')
        self.exec_logger.debug(f'Saving to {filename}')

        # make sure all multiplexer are off
        

        # measure all quadrupole of the sequence
        if self.sequence is None:
            n = 1
        else:
            n = self.sequence.shape[0]
        for i in range(0, n):
            if self.sequence is None:
                quad = np.array([0, 0, 0, 0])
            else:
                quad = self.sequence[i, :]  # quadrupole
            if self.status == 'stopping':
                break
            # if i == 0:
            #     # call the switch_mux function to switch to the right electrodes
            #     # switch on DPS
            #     self.mcp_board = MCP23008(self.i2c, address=self.mcp_board_address)
            #     self.pin2 = self.mcp_board.get_pin(2) # dsp -
            #     self.pin2.direction = Direction.OUTPUT
            #     self.pin2.value = True
            #     self.pin3 = self.mcp_board.get_pin(3) # dsp -
            #     self.pin3.direction = Direction.OUTPUT
            #     self.pin3.value = True
            #     time.sleep (4)
            #
            #     #self.switch_dps('on')
            # time.sleep(.6)
            # self.switch_mux_on(quad)
            # run a measurement
            if self.on_pi:
                acquired_data = self.run_measurement(quad, **kwargs)
            else:  # for testing, generate random data
                sum_vmn = np.random.rand(1)[0] * 1000.
                sum_i = np.random.rand(1)[0] * 100.
                cmd_id = np.random.randint(1000)
                acquired_data = {
                    "time": datetime.now().isoformat(),
                    "A": quad[0],
                    "B": quad[1],
                    "M": quad[2],
                    "N": quad[3],
                    "inj time [ms]": self.settings['injection_duration'] * 1000.,
                    "Vmn [mV]": sum_vmn,
                    "I [mA]": sum_i,
                    "R [ohm]": sum_vmn / sum_i,
                    "Ps [mV]": np.random.randn(1)[0] * 100.,
                    "nbStack": self.settings['nb_stack'],
                    "Tx [V]": np.random.randn(1)[0] * 5.,
                    "CPU temp [degC]": np.random.randn(1)[0] * 50.,
                    "Nb samples [-]": self.nb_samples,
                }
                self.data_logger.info(acquired_data)

            # # switch mux off
            # self.switch_mux_off(quad)
            #
            # # add command_id in dataset
            acquired_data.update({'cmd_id': cmd_id})
            # log data to the data logger
            # self.data_logger.info(f'{acquired_data}')
            # save data and print in a text file
            self.append_and_save(filename, acquired_data)
            self.exec_logger.debug(f'quadrupole {i + 1:d}/{n:d}')

        # self.switch_dps('off')
        self.status = 'idle'

    def run_sequence_async(self, cmd_id=None, **kwargs):
        """Runs the sequence in a separate thread. Can be stopped by 'OhmPi.interrupt()'.
            Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """

        def func():
            self.run_sequence(**kwargs)

        self.thread = Thread(target=func)
        self.thread.start()
        self.status = 'idle'

    # TODO: we could build a smarter RS-Check by selecting adjacent electrodes based on their locations and try to
    #  isolate electrodes that are responsible for high resistances (ex: AB high, AC low, BC high
    #  -> might be a problem at B (cf what we did with WofE)
    def rs_check(self, tx_volt=12., cmd_id=None):
        """Checks contact resistances

        Parameters
        ----------
        tx_volt : float
            Voltage of the injection
        cmd_id : str, optional
            Unique command identifier
        """
        # create custom sequence where MN == AB
        # we only check the electrodes which are in the sequence (not all might be connected)
        if self.sequence is None:
            quads = np.array([[1, 2, 1, 2]], dtype=np.uint32)
        else:
            elec = np.sort(np.unique(self.sequence.flatten()))  # assumed order
            quads = np.vstack([
                elec[:-1],
                elec[1:],
                elec[:-1],
                elec[1:],
            ]).T
        # if self.idps:
        #     quads[:, 2:] = 0  # we don't open Vmn to prevent burning the MN part
        #     # as it has a smaller range of accepted voltage

        # create filename to store RS
        export_path_rs = self.settings['export_path'].replace('.csv', '') \
                         + '_' + datetime.now().strftime('%Y%m%dT%H%M%S') + '_rs.csv'

        # perform RS check
        self.status = 'running'

        self.reset_mux()

        # measure all quad of the RS sequence
        for i in range(0, quads.shape[0]):
            quad = quads[i, :]  # quadrupole
            self.switch_mux_on(quad)  # put before raising the pins (otherwise conflict i2c)
            d = self.run_measurement(quad=quad, nb_stack=1, injection_duration=0.2, tx_volt=tx_volt, autogain=False)

            if self._hw.tx.voltage_adjustable:
                voltage = self._hw.tx.voltage  # imposed voltage on dps
            else:
                voltage = d['Vmn [mV]']
            current = d['I [mA]']

            # compute resistance measured (= contact resistance)
            resist = abs(voltage / current) / 1000.
            # print(str(quad) + '> I: {:>10.3f} mA, V: {:>10.3f} mV, R: {:>10.3f} kOhm'.format(
            #    current, voltage, resist))
            msg = f'Contact resistance {str(quad):s}: I: {current * 1000.:>10.3f} mA, ' \
                  f'V: {voltage :>10.3f} mV, ' \
                  f'R: {resist :>10.3f} kOhm'

            self.exec_logger.debug(msg)

            # if contact resistance = 0 -> we have a short circuit!!
            if resist < 1e-5:
                msg = f'!!!SHORT CIRCUIT!!! {str(quad):s}: {resist:.3f} kOhm'
                self.exec_logger.warning(msg)

            # save data in a text file
            self.append_and_save(export_path_rs, {
                'A': quad[0],
                'B': quad[1],
                'RS [kOhm]': resist,
            })

            # close mux path and put pin back to GND
            self.switch_mux_off(quad)
        self.status = 'idle'

    #
    #         # TODO if interrupted, we would need to restore the values
    #         # TODO or we offer the possibility in 'run_measurement' to have rs_check each time?

    def set_sequence(self, sequence=None, cmd_id=None):
        """Sets the sequence to acquire

        Parameters
        ----------
        sequence : list, str
            sequence of quadrupoles
        cmd_id: str, optional
            Unique command identifier
        """
        try:
            self.sequence = np.array(sequence).astype(int)
            # self.sequence = np.loadtxt(StringIO(sequence)).astype('uint32')
            status = True
        except Exception as e:
            self.exec_logger.warning(f'Unable to set sequence: {e}')
            status = False

    def switch_mux_on(self, quadrupole, cmd_id=None):
        """Switches on multiplexer relays for given quadrupole.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        """
        assert len(quadrupole) == 4
        return  self._hw.switch_mux(electrodes=quadrupole, state='on')

    def switch_mux_off(self, quadrupole, cmd_id=None):
        """Switches off multiplexer relays for given quadrupole.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        """
        assert len(quadrupole) == 4
        return self._hw.switch_mux(electrodes=quadrupole, state='off')

    def test_mux(self, activation_time=1.0, mux_id=None, cmd_id=None): # TODO: add this in the MUX code
        """Interactive method to test the multiplexer boards.

        Parameters
        ----------
        activation_time : float, optional
            Time in seconds during which the relays are activated.
        mux_id : str, optional
            id of the mux_board to test
        cmd_id : str, optional
            Unique command identifier
        """
        self.reset_mux() # All mux boards should be reset even if we only want to test one otherwise we might create a shortcut
        if mux_id is None:
            self._hw.test_mux(activation_time=activation_time)
        else:
            self._hw.mux_boards[mux_id].test(activation_time=activation_time)


    def reset_mux(self, cmd_id=None):
        """Switches off all multiplexer relays.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self._hw.reset_mux()

    def update_settings(self, settings: str, cmd_id=None):
        """Updates acquisition settings from a json file or dictionary.
        Parameters can be:
            - nb_electrodes (number of electrode used, if 4, no MUX needed)
            - injection_duration (in seconds)
            - nb_meas (total number of times the sequence will be run)
            - sequence_delay (delay in second between each sequence run)
            - nb_stack (number of stack for each quadrupole measurement)
            - export_path (path where to export the data, timestamp will be added to filename)

        Parameters
        ----------
        settings : str, dict
            Path to the .json settings file or dictionary of settings.
        cmd_id : str, optional
            Unique command identifier
        """
        status = False
        if settings is not None:
            try:
                if isinstance(settings, dict):
                    self.settings.update(settings)
                else:
                    with open(settings) as json_file:
                        dic = json.load(json_file)
                    self.settings.update(dic)
                self.exec_logger.debug('Acquisition parameters updated: ' + str(self.settings))
                status = True
            except Exception as e:  # noqa
                self.exec_logger.warning('Unable to update settings.')
                status = False
        else:
            self.exec_logger.warning('Settings are missing...')
        return status

    # Properties
    @property
    def sequence(self):
        """Gets sequence"""
        if self._sequence is not None:
            assert isinstance(self._sequence, np.ndarray)
        return self._sequence

    @sequence.setter
    def sequence(self, sequence):
        """Sets sequence"""
        if sequence is not None:
            assert isinstance(sequence, np.ndarray)
        self._sequence = sequence


print(colored(r' ________________________________' + '\n' +
              r'|  _  | | | ||  \/  || ___ \_   _|' + '\n' +
              r'| | | | |_| || .  . || |_/ / | |' + '\n' +
              r'| | | |  _  || |\/| ||  __/  | |' + '\n' +
              r'\ \_/ / | | || |  | || |    _| |_' + '\n' +
              r' \___/\_| |_/\_|  |_/\_|    \___/ ', 'red'))
print('Version:', VERSION)
platform, on_pi = get_platform()

if on_pi:
    print(colored(f'\u2611 Running on {platform}', 'green'))
    # TODO: check model for compatible platforms (exclude Raspberry Pi versions that are not supported...)
    #       and emit a warning otherwise
    if not arm64_imports:
        print(colored(f'Warning: Required packages are missing.\n'
                      f'Please run ./env.sh at command prompt to update your virtual environment\n', 'yellow'))
else:
    print(colored(f'\u26A0 Not running on the Raspberry Pi platform.\nFor simulation purposes only...', 'yellow'))

current_time = datetime.now()
print(f'local date and time : {current_time.strftime("%Y-%m-%d %H:%M:%S")}')
OhmPi.get_deprecated_methods()

# for testing
if __name__ == "__main__":
    ohmpi = OhmPi(settings=OHMPI_CONFIG['settings'])
    if ohmpi.controller is not None:
        ohmpi.controller.loop_forever()