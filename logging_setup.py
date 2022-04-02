import json
from config import EXEC_LOGGING_CONFIG, DATA_LOGGING_CONFIG, MQTT_LOGGING_CONFIG
from os import path, mkdir, statvfs
from time import gmtime
import logging
from mqtt_logger import MQTTHandler
from compressed_sized_timed_rotating_logger import CompressedSizedTimedRotatingFileHandler


def setup_loggers(mqtt=True):
    # Message logging setup
    log_path = path.join(path.dirname(__file__), 'logs')
    if not path.isdir(log_path):
        mkdir(log_path)
    exec_log_filename = path.join(log_path, 'msg_log')
    exec_logger = logging.getLogger('exec_logger')

    # SOH logging setup
    # TODO: Add state of health logging here

    # Data logging setup
    base_path = path.dirname(__file__)
    data_path = path.join(base_path, 'data')
    if not path.isdir(data_path):
        mkdir(data_path)
    data_log_filename = path.join(data_path, 'data_log')
    data_logger = logging.getLogger('data_logger')

    # Debug and logging
    debug = EXEC_LOGGING_CONFIG['debug_mode']
    if debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    # Set message logging format and level
    log_format = '%(asctime)-15s | %(process)d | %(levelname)s: %(message)s'
    logging_to_console = EXEC_LOGGING_CONFIG['logging_to_console']
    exec_handler = CompressedSizedTimedRotatingFileHandler(exec_log_filename,
                                                           max_bytes=EXEC_LOGGING_CONFIG['max_bytes'],
                                                           backup_count=EXEC_LOGGING_CONFIG['backup_count'],
                                                           when=EXEC_LOGGING_CONFIG['when'],
                                                           interval=EXEC_LOGGING_CONFIG['interval'])
    exec_formatter = logging.Formatter(log_format)
    exec_formatter.converter = gmtime
    exec_formatter.datefmt = '%Y/%m/%d %H:%M:%S UTC'
    exec_handler.setFormatter(exec_formatter)
    exec_logger.addHandler(exec_handler)
    exec_logger.setLevel(logging_level)

    if logging_to_console:
        exec_logger.addHandler(logging.StreamHandler())
    if mqtt:
        mqtt_msg_handler = MQTTHandler(MQTT_LOGGING_CONFIG['hostname'], MQTT_LOGGING_CONFIG['exec_topic'])
        mqtt_msg_handler.setLevel(logging_level)
        mqtt_msg_handler.setFormatter(exec_formatter)
        exec_logger.addHandler(mqtt_msg_handler)

    # Set data logging format and level
    log_format = '%(asctime)-15s | %(process)d | %(levelname)s: %(message)s'
    logging_to_console = DATA_LOGGING_CONFIG['logging_to_console']

    data_handler = CompressedSizedTimedRotatingFileHandler(exec_log_filename,
                                                           max_bytes=DATA_LOGGING_CONFIG['max_bytes'],
                                                           backup_count=DATA_LOGGING_CONFIG['backup_count'],
                                                           when=DATA_LOGGING_CONFIG['when'],
                                                           interval=DATA_LOGGING_CONFIG['interval'])
    data_formatter = logging.Formatter(log_format)
    data_formatter.converter = gmtime
    data_formatter.datefmt = '%Y/%m/%d %H:%M:%S UTC'
    data_handler.setFormatter(exec_formatter)
    data_logger.addHandler(data_handler)
    data_logger.setLevel(logging_level)

    if logging_to_console:
        data_logger.addHandler(logging.StreamHandler())
    if mqtt:
        mqtt_data_handler = MQTTHandler(MQTT_LOGGING_CONFIG['hostname'], MQTT_LOGGING_CONFIG['data_topic'])
        mqtt_data_handler.setLevel(logging_level)
        mqtt_data_handler.setFormatter(data_formatter)
        data_logger.addHandler(mqtt_data_handler)

    try:
        init_logging(exec_logger, data_logger, logging_level, log_path, data_log_filename)
    except Exception as err:
        print(f'ERROR: Could not initialize logging!\n{err}')
    finally:
        return exec_logger, exec_log_filename, data_logger, data_log_filename, logging_level


def init_logging(exec_logger, data_logger, logging_level, log_path, data_log_filename):
    """ This is the init sequence for the logging system """

    init_logging_status = True
    exec_logger.info('')
    exec_logger.info('****************************')
    exec_logger.info('*** NEW SESSION STARTING ***')
    exec_logger.info('****************************')
    exec_logger.info('')
    exec_logger.info('Logging level: %s' % logging_level)
    try:
        st = statvfs('.')
        available_space = st.f_bavail * st.f_frsize / 1024 / 1024
        exec_logger.info(f'Remaining disk space : {available_space:.1f} MB')
    except Exception as e:
        exec_logger.debug('Unable to get remaining disk space: {e}')
    exec_logger.info('Saving data log to ' + data_log_filename)
    exec_logger.info('OhmPi settings:')
    # TODO Add OhmPi settings
    config_dict = {'execution logging configuration': json.dumps(EXEC_LOGGING_CONFIG, indent=4),
                   'data logging configuration': json.dumps(DATA_LOGGING_CONFIG, indent=4),
                   'mqtt logging configuration': json.dumps(MQTT_LOGGING_CONFIG, indent=4)}
    for k, v in config_dict.items():
        exec_logger.info(f'{k}:\n{v}')
    exec_logger.info('')
    exec_logger.info(f'init_logging_status: {init_logging_status}')
    data_logger.info('Starting_session')
    return init_logging_status
