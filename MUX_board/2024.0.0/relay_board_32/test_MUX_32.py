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
#mux_addressing_table_file = os.path.join("MUX_board",mux_board_version,"relay_board_32",mux_addressing_table_file)

electrode_nr = ["1","4","2","3"]
role = ["A","B","M","N"]
# state = on


with open(mux_addressing_table_file, 'r') as myfile:
    header = myfile.readlines()[0].strip('\n').split(',')
mux_addressing_table = np.genfromtxt(mux_addressing_table_file, dtype=str,
                                     delimiter=',', skip_header=1, )
mux_addressing_table = {header[k]: mux_addressing_table.T[k] for k in range(len(header))}
print(mux_addressing_table)

def set_relay_state(mcp, mcp_pin, state=True):
    pin_enable = mcp.get_pin(mcp_pin)
    pin_enable.direction = Direction.OUTPUT
    pin_enable.value = state

i2c = busio.I2C(board.SCL, board.SDA)
mcp_list = np.array([])
tca_addr = np.array([])
tca_channel = np.array([])
mcp_gpio = np.array([])
mcp_addr = np.array([])
for i in range(len(electrode_nr)):
    idx = np.where((mux_addressing_table['Electrode_id'] == electrode_nr[i]) & (mux_addressing_table['Role'] == role[i]))[0]
    print(idx)
    tca_addr = np.append(tca_addr,mux_addressing_table['TCA_address'][idx][0])
    tca_channel = np.append(tca_channel,mux_addressing_table['TCA_channel'][idx][0])
    mcp_addr = np.append(mcp_addr,int(mux_addressing_table['MCP_address'][idx][0], 16))
    mcp_gpio = np.append(mcp_gpio,int(mux_addressing_table['MCP_GPIO'][idx][0]))
    if tca_addr[i] == 'None':
         tca = i2c
    else:
         tca = adafruit_tca9548a.TCA9548A(i2c, tca_addr[i])
    mcp_list = np.append(mcp_list,MCP23017(tca, address=int(mcp_addr[i])))
    
mux_list = np.column_stack([tca_addr,tca_channel,mcp_addr])
mcp_to_address, mcp_idx, mcp_counts = np.unique(mux_list, return_index=True, return_counts=True,  axis=0)
print(mcp_to_address,mcp_idx)
for j,mcp in enumerate(mcp_to_address):
    for i,mux in enumerate(mux_list):
        if np.array_equal(mux,mcp):
            print(mcp_list[mcp_idx[j]].get_pin(int(mcp_gpio[i])))
            mcp_tmp = mcp_list[mcp_idx[j]]
            set_relay_state(mcp_tmp,int(mcp_gpio[i]), True)

time.sleep(10)
for j,mcp in enumerate(mcp_to_address):
    for i,mux in enumerate(mux_list):
        if np.array_equal(mux,mcp):
            set_relay_state(mcp_tmp,int(mcp_gpio[i]), False)
        
