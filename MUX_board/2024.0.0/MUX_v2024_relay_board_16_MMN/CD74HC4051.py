from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction
import busio
import board
import numpy as np

CD74HC4051_addresses = {0: [0, 0, 0], 1: [1, 0, 0], 2: [0, 1, 0], 3: [1, 1, 0],
                        4: [0, 0, 1], 5: [1, 0, 1], 6: [0, 1, 1], 7: [1, 1, 1]}

mcp_table = np.genfromtxt('template_table_mux.csv')
print(mcp_table)
mux_channel = 0
mux_id = 0

def open_cd74hc4051(channel,mcp,mcp_pins,CD74HC4051_addresses):
    mux_states = CD74HC4051_addresses[channel]
    pins = np.array([None,None,None])
    for i in range(3):
        pins[i] = mcp.get_pin(mcp_pins[i])
        pins[i].direction = Direction.OUTPUT
        pins[i].value = bool(mux_states[i])

    pin_enable = mcp.get_pin(mcp_pins[3])
    pin_enable.direction = Direction.OUTPUT
    pin_enable.value = bool(True)

mcp_table_file = '/home/arnaud/codes/OhmPi/MUX_board/MUX_v2024_relay_board_16_MMN/template_table_mux.csv'
with open(mcp_table_file,'r') as myfile:
    header = myfile.readlines()[0].strip('\n').split(',')
mcp_table = np.genfromtxt('/home/arnaud/codes/OhmPi/MUX_board/MUX_v2024_relay_board_16_MMN/template_table_mux.csv',delimiter=',',skip_header=1)
mcp_table_dict = {header[k]:mcp_table.T[k] for k in range(len(header))}

mux_id_channels = np.where(mcp_table_dict['mux_id']==mux_id)
mcp_pins = mcp_table_dict['mcp_pins'][mux_id_channels][mcp_table_dict['mux_pin'][mux_id_channels].astype(int)]

i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x21)
open_cd74hc4051(mux_channel,mcp,mcp_pins,CD74HC4051_addresses)