from adafruit_mcp230xx.mcp23017 import MCP23017
import adafruit_tca9548a
from digitalio import Direction
import busio
import board
import numpy as np
import time
import os

mux_board_version = '2024.0.0'
mux_addressing_table_file = "compiled_mux_addressing_table.csv"
mux_addressing_table_file = os.path.join(mux_board_version,"relay_board_32",mux_addressing_table_file)

electrode_nr = 1
role = "A"
# state = on

with open(mux_addressing_table_file, 'r') as myfile:
    header = myfile.readlines()[0].strip('\n').split(',')
mux_addressing_table = np.genfromtxt(mux_addressing_table_file, dtype=str,
                                     delimiter=',', skip_header=1, )
mux_addressing_table = {header[k]: mux_addressing_table.T[k] for k in range(len(header))}


def set_relay_state(mcp, mcp_pin, state=True):
    pin_enable = mcp.get_pin(mcp_pin)
    pin_enable.direction = Direction.OUTPUT
    pin_enable.value = state

i2c = busio.I2C(board.SCL, board.SDA)
idx = np.where((mux_addressing_table['Electrode_id'] == electrode_nr) & (mux_addressing_table['Role'] == role))[0]
tca_addr = mux_addressing_table['TCA_address'][idx][0]
tca_channel = mux_addressing_table['TCA_channel'][idx][0]
mcp_gpio = mux_addressing_table['MCP_GPIO'][idx][0]
if tca_addr is None:
    tca = i2c
else:
    tca = adafruit_tca9548a.TCA9548A(i2c, role)
#tca = adafruit_tca9548a.TCA9548A(i2c, hex(int(tca_addr, 16)))[tca_channel]
tca = i2c
mcp_addr = hex(int(mux_addressing_table['MCP_address'][idx][0], 16))
MCP23017(tca, address=mcp_addr)

set_relay_state(mcp_addr,mcp_gpio, True)
time.sleep(2)
set_relay_state(mcp_addr,mcp_gpio, True)