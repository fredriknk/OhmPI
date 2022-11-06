import logging
from utils import get_platform

from paho.mqtt.client import MQTTv31

_, on_pi = get_platform()
ohmpi_id = '0001'
# mqtt_broker = 'localhost'
mqtt_broker = 'localhost' if on_pi else 'mg3d-dev.umons.ac.be'

logging_suffix = ''
# OhmPi configuration
OHMPI_CONFIG = {
    'id': ohmpi_id,  # Unique identifier of the OhmPi board (string)
    'R_shunt': 2,  # Shunt resistance in Ohms
    'Imax': 4800 / 50 / 2,  # Maximum current
    'coef_p2': 2.50,  # slope for current conversion for ADS.P2, measurement in V/V
    #    'coef_p3': 2.50,  # slope for current conversion for ADS.P3, measurement in V/V
    #    'offset_p2': 0,
    #    'offset_p3': 0,
    'nb_samples': 2,  # Max value 10 # was named integer before...
    'version': 2,  # Is this still needed?
    'max_elec': 64,
    'board_addresses': {'A': 0x73, 'B': 0x72, 'M': 0x71, 'N': 0x70},
    # def. {'A': 0x76, 'B': 0x71, 'M': 0x74, 'N': 0x70}
    'settings': 'ohmpi_settings.json',
    'board_version': '22.10'
}  # TODO: add a dictionary with INA models and associated gain values

# Execution logging configuration
EXEC_LOGGING_CONFIG = {
    'logging_level': logging.INFO,
    'log_file_logging_level': logging.DEBUG,
    'logging_to_console': True,
    'file_name': f'exec{logging_suffix}.log',
    'max_bytes': 262144,
    'backup_count': 30,
    'when': 'd',
    'interval': 1
}

# Data logging configuration
DATA_LOGGING_CONFIG = {
    'logging_level': logging.INFO,
    'logging_to_console': True,
    'file_name': f'data{logging_suffix}.log',
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}

# State of Health logging configuration
SOH_LOGGING_CONFIG = {
    'logging_level' : logging.INFO,
    'logging_to_console': True,
    'file_name': 'soh.log',
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}

# MQTT logging configuration parameters
MQTT_LOGGING_CONFIG = {
    'hostname': mqtt_broker,
    'port': 1883,
    'qos': 2,
    'retain': False,
    'keepalive': 60,
    'will': None,
    'auth': {'username': 'mqtt_user', 'password': 'mqtt_password'},
    'tls': None,
    'protocol': MQTTv31,
    'transport': 'tcp',
    'client_id': f'{OHMPI_CONFIG["id"]}',
    'exec_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/exec',
    'exec_logging_level': logging.DEBUG,
    'data_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/data',
    'data_logging_level': DATA_LOGGING_CONFIG['logging_level'],
    'soh_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/soh',
    'soh_logging_level': SOH_LOGGING_CONFIG['logging_level']
}

# MQTT control configuration parameters
MQTT_CONTROL_CONFIG = {
    'hostname': mqtt_broker,
    'port': 1883,
    'qos': 2,
    'retain': False,
    'keepalive': 60,
    'will': None,
    'auth': {'username': 'mqtt_user', 'password': 'mqtt_password'},
    'tls': None,
    'protocol': MQTTv31,
    'transport': 'tcp',
    'client_id': f'{OHMPI_CONFIG["id"]}',
    'ctrl_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/ctrl'
}
