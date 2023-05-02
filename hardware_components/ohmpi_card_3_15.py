import importlib
from OhmPi.config import HARDWARE_CONFIG
import adafruit_ads1x15.ads1115 as ads  # noqa
from adafruit_ads1x15.analog_in import AnalogIn  # noqa
from adafruit_ads1x15.ads1x15 import Mode  # noqa
from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
from digitalio import Direction  # noqa
import minimalmodbus  # noqa
import time
import numpy as np
import os
from OhmPi.hardware_components import TxAbstract, RxAbstract
controller_name = HARDWARE_CONFIG['controller'].pop('board_name', 'raspberry_pi')
controller_module = importlib.import_module(f'OhmPi.hardware_components.{controller_name}')

TX_CONFIG = HARDWARE_CONFIG['tx']
RX_CONFIG = HARDWARE_CONFIG['rx']

# hardware characteristics and limitations
# *** RX ***
# ADC for voltage
voltage_adc_voltage_min = 10.  # mV
voltage_adc_voltage_max = 4500.  # mV
sampling_rate = 10.  # ms
RX_CONFIG['voltage_min'] = np.min([voltage_adc_voltage_min, RX_CONFIG.pop('voltage_min', np.inf)])  # mV
RX_CONFIG['voltage_max'] = np.min([voltage_adc_voltage_max, RX_CONFIG.pop('voltage_max', np.inf)])  # mV
RX_CONFIG['sampling_rate'] = RX_CONFIG.pop('sampling_rate', sampling_rate)

# *** TX ***
# ADC for current
current_adc_voltage_min = 10.  # mV
current_adc_voltage_max = 4500. # mV
low_battery = 12. # V (conventional value as it is not measured on this board)
tx_mcp_board_address = 0x20  #
dps_voltage_max = 12.  # V
dps_default_voltage = 12.  # V
dps_switch_on_warmup = 0.  # seconds

TX_CONFIG['current_min'] = np.min([current_adc_voltage_min / (TX_CONFIG['r_shunt'] * 50), TX_CONFIG.pop('current_min', np.inf)])  # mA
TX_CONFIG['current_max'] = np.min([current_adc_voltage_max / (TX_CONFIG['r_shunt'] * 50), TX_CONFIG.pop('current_max', np.inf)])  # mA
TX_CONFIG['voltage_max'] = np.min([dps_voltage_max, TX_CONFIG.pop('voltage_max', np.inf)])  # V
TX_CONFIG['default_voltage'] = np.min([TX_CONFIG.pop('default_voltage', dps_default_voltage), TX_CONFIG['voltage_max']])  # V
TX_CONFIG['dps_switch_on_warm_up'] = TX_CONFIG.pop('dps_switch_on_warmup', dps_switch_on_warmup)
TX_CONFIG['mcp_board_address'] = TX_CONFIG.pop('mcp_board_address', tx_mcp_board_address)
TX_CONFIG['low_battery'] = TX_CONFIG.pop('low_battery', low_battery)

def _gain_auto(channel):
    """Automatically sets the gain on a channel

    Parameters
    ----------
    channel : ads.ADS1x15
        Instance of ADS where voltage is measured.

    Returns
    -------
    gain : float
        Gain to be applied on ADS1115.
    """

    gain = 2 / 3
    if (abs(channel.voltage) < 2.040) and (abs(channel.voltage) >= 1.0):
        gain = 2
    elif (abs(channel.voltage) < 1.0) and (abs(channel.voltage) >= 0.500):
        gain = 4
    elif (abs(channel.voltage) < 0.500) and (abs(channel.voltage) >= 0.250):
        gain = 8
    elif abs(channel.voltage) < 0.250:
        gain = 16
    return gain

class Tx(TxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self._voltage = kwargs.pop('voltage', TX_CONFIG['default_voltage'])
        self.voltage_adjustable = False
        self.current_adjustable = False
        if self.controller is None:
            self.controller = controller_module.Controller()

        # I2C connexion to MCP23008, for current injection
        self.mcp_board = MCP23008(self.controller.bus, address=TX_CONFIG['mcp_board_address'])

        # ADS1115 for current measurement (AB)
        self._ads_current_address = 0x48
        self._ads_current = ads.ADS1115(self.controller.bus, gain=self.adc_gain, data_rate=860,
                                        address=self._ads_current_address)
        self._ads_current.mode = Mode.CONTINUOUS

        # Relays for pulse polarity
        self.pin0 = self.mcp_board.get_pin(0)
        self.pin0.direction = Direction.OUTPUT
        self.pin1 = self.mcp_board.get_pin(1)
        self.pin1.direction = Direction.OUTPUT
        self.polarity = 0

        self.adc_gain = 2 / 3

        # DPH 5005 Digital Power Supply
        self.turn_on()
        time.sleep(TX_CONFIG['dps_switch_on_warm_up'])
        self.DPS = None

        # I2C connexion to MCP23008, for current injection
        self.pin4 = self.mcp_board.get_pin(4)  # Ohmpi_run
        self.pin4.direction = Direction.OUTPUT
        self.pin4.value = True

        self.exec_logger.info(f'TX battery: {self.tx_bat:.1f} V')
        self.turn_off()

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        assert value in [2/3, 2, 4, 8, 16]
        self._adc_gain = value
        self._ads_current = ads.ADS1115(self.controller.bus, gain=self.adc_gain, data_rate=860,
                                        address=self._ads_current_address)
        self.exec_logger.debug(f'Setting TX ADC gain to {value}')

    def adc_gain_auto(self):
        gain = _gain_auto(AnalogIn(self._ads_current, ads.P0))
        self.exec_logger.debug(f'Setting TX ADC gain automatically to {gain}')
        self.adc_gain = gain

    def current_pulse(self, **kwargs):
        TxAbstract.current_pulse(self, **kwargs)
        self.exec_logger.warning(f'Current pulse is not implemented for the {TX_CONFIG["model"]} board')

    @property
    def current(self):
        """ Gets the current IAB in Amps
        """
        iab = AnalogIn(self._ads_current, ads.P0).voltage * 1000. / (50 * TX_CONFIG['r_shunt'])  # measure current
        self.exec_logger.debug(f'Reading TX current:  {iab} mA')
        return iab

    @ current.setter
    def current(self, value):
        assert TX_CONFIG['current_min'] <= value <= TX_CONFIG['current_max']
        self.exec_logger.warning(f'Current pulse is not implemented for the {TX_CONFIG["model"]} board')

    def inject(self, state='on'):
        TxAbstract.inject(self, state=state)
        # Add specifics here...

    @property
    def polarity(self):
        return TxAbstract.polarity.fget(self)

    @polarity.setter
    def polarity(self, value):
        TxAbstract.polarity.fset(self, value)
        if value==1:
            self.pin0.value = True
            self.pin1.value = False
        elif value==-1:
            self.pin0.value = False
            self.pin1.value = True
        else:
            self.pin0.value = False
            self.pin1.value = False
        #time.sleep(0.001) # TODO: check max switching time of relays

    def turn_off(self):
        pass

    def turn_on(self):
        pass

    @property
    def tx_bat(self):
        self.soh_logger.warning(f'Cannot get battery voltage on {self.board_name}')
        self.exec_logger.debug(f'{self.board_name} cannot read battery voltage. Returning default battery voltage.')
        return TX_CONFIG['low_battery']

    def voltage_pulse(self, voltage=TX_CONFIG['default_voltage'], length=None, polarity=None):
        """ Generates a square voltage pulse

        Parameters
        ----------
        voltage: float, optional
            Voltage to apply in volts, tx_v_def is applied if omitted.
        length: float, optional
            Length of the pulse in seconds
        polarity: 1,0,-1
            Polarity of the pulse
        """

        if length is None:
            length = self.inj_time
        if polarity is None:
            polarity = self.polarity
        self.polarity = polarity
        self.voltage = voltage
        self.exec_logger.debug(f'Voltage pulse of {polarity*voltage:.3f} V for {length:.3f} s')
        self.inject(state='on')
        time.sleep(length)
        self.inject(state='off')


    @property
    def voltage(self):
        return self._voltage
    @voltage.setter
    def voltage(self, value):
        assert isinstance(value, float)
        value = np.max(TX_CONFIG['voltage_min'], np.min(value, TX_CONFIG['voltage_max']))
        super().voltage = value

class Rx(RxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        if self.controller is None:
            self.controller = controller_module.Controller()

        # ADS1115 for voltage measurement (MN)
        self._ads_voltage_address = 0x49
        self._adc_gain = 2/3
        self._ads_voltage = ads.ADS1115(self.controller.bus, gain=self._adc_gain, data_rate=860, address=self._ads_voltage_address)
        self._ads_voltage.mode = Mode.CONTINUOUS
        self._sampling_rate = kwargs.pop('sampling_rate', sampling_rate)

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        assert value in [2/3, 2, 4, 8, 16]
        self._adc_gain = value
        self._ads_voltage = ads.ADS1115(self.controller.bus, gain=self.adc_gain, data_rate=860,
                                        address=self._ads_voltage_address)
        self.exec_logger.debug(f'Setting RX ADC gain to {value}')

    def adc_gain_auto(self):
        gain_0 = _gain_auto(AnalogIn(self._ads_voltage, ads.P0))
        gain_2 = _gain_auto(AnalogIn(self._ads_voltage, ads.P2))
        gain = np.min([gain_0, gain_2])
        self.exec_logger.debug(f'Setting RX ADC gain automatically to {gain}')
        self.adc_gain = gain

    @property
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        u0 = AnalogIn(self._ads_voltage, ads.P0).voltage * 1000.
        u2 = AnalogIn(self._ads_voltage, ads.P2).voltage * 1000.
        u = np.max([u0,u2]) * (np.heaviside(u0-u2, 1.) * 2 - 1.) # gets the max between u0 & u2 and set the sign
        self.exec_logger.debug(f'Reading voltages {u0} mV and {u2} mV on RX. Returning {u} mV')
        return u