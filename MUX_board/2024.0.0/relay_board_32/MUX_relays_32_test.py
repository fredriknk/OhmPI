from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction
import busio
# import board
import numpy as np
import time

def set_mux_addressing_table(addressing_logic_table='addresses_table_4roles.csv',mux_settings=''):
    # with open(mux_table, 'r') as myfile:
    #     header = myfile.readlines()[0].strip('\n').split(',')
    # mcp_table = np.genfromtxt(mux_table,dtype=str,
    #                           delimiter=',', skip_header=1,)
    # # mux_addressing_table = {header[k]: mcp_table.T[k] for k in range(len(header))}

    with open(addressing_logic_table, 'r') as myfile:
        header = myfile.readlines()[0].strip('\n').split(',')
    addressing_logic_table = np.genfromtxt(addressing_logic_table,dtype=str,
                              delimiter=',', skip_header=1,)

    addressing_logic_table = {header[k]: addressing_logic_table.T[k] for k in range(len(header))}
    print(addressing_logic_table)
    addressing_logic_table['Electrode_board_id'] = addressing_logic_table['Electrode_board_id'].astype('uint16')
    addressing_logic_table['MCP_board_id'] = addressing_logic_table['MCP_board_id'].astype('uint16')
    addressing_logic_table['GPIO'] = addressing_logic_table['GPIO'].astype('uint16')

    # return addressing_logic_table

# def set_mux_addr(mux_settings):
    with open(mux_settings, 'r') as myfile:
        header = myfile.readlines()[0].strip('\n').split(',')
    mux_addr = np.genfromtxt(mux_settings,dtype=str, delimiter=',', skip_header=1,)
    mux_addr = {header[k]: np.atleast_1d(mux_addr.T[k]) for k in range(len(header))}

    keys = ['TCA_address', 'TCA_channel', 'MCP_address', 'Electrode_id', 'MCP_GPIO', 'Role']
    mux_addressing_table = {keys[k]:np.array([]) for k in range(len(keys))}
    print(mux_addr)
   # mux_addressing_table['MCP_address'] = mux_addressing_table['MCP_address'].astype(hex)

    for i in range(len(mux_addr['TCA_address'])):
        vhex = np.vectorize(hex)
        mux_addressing_table['TCA_address'] = np.append(mux_addressing_table['TCA_address'],
                                                        np.repeat(mux_addr['TCA_address'][i],
                                                        addressing_logic_table['Electrode_board_id'].shape[0]))
        mux_addressing_table['TCA_channel'] = np.append(mux_addressing_table['TCA_channel'],
                                                        np.repeat(mux_addr['TCA_channel'][i],
                                                                  addressing_logic_table['Electrode_board_id'].shape[
                                                                      0]))
        mux_addressing_table['MCP_address'] = np.append(mux_addressing_table['MCP_address'],
                                                        vhex(int(mux_addr['MCP_address'][i],16)+
                                                             addressing_logic_table['MCP_board_id']))
        mux_addressing_table['MCP_GPIO'] = np.append(mux_addressing_table['MCP_GPIO'],
                                                     addressing_logic_table['GPIO']).astype(np.uint16)
        mux_addressing_table['Electrode_id'] = np.append(mux_addressing_table['Electrode_id'],
                                                         addressing_logic_table['Electrode_board_id'] +
                                                         int(mux_addr['Electrode_id_min'][i])).astype(np.uint16)
        mux_addressing_table['Role'] = np.append(mux_addressing_table['Role'],
                                                 addressing_logic_table['Role'])

    return mux_addressing_table

def set_relay_state(mcp_addr,mcp_pin,state=True):
    i2c = busio.I2C(board.SCL, board.SDA)
    print(mcp_addr)
    mcp = MCP23017(i2c, address=mcp_addr)
    pin_enable = mcp.get_pin(mcp_pin)
    pin_enable.direction = Direction.OUTPUT
    pin_enable.value = state

addressing_logic_table='addresses_table_4roles.csv'
mux_table = 'MUX_settings.csv'
mux_addressing_table = set_mux_addressing_table(addressing_logic_table,mux_table)
print("table" , mux_addressing_table)
header = ','.join([k for k in mux_addressing_table.keys()])
values = [[(v[i]) for v in mux_addressing_table.values()] for i in range(len(mux_addressing_table['MCP_address']))]
with open("compiled_mux_addressing_table.csv", "w") as file:
    file.write(header+"\n")
with open("compiled_mux_addressing_table.csv", "a") as file:
    for lines in values:
        file.writelines(','.join(str(l) for l in lines)+"\n")

# print('rr',[[(v[i]) for v in mux_addressing_table.values()] for i in range(len(mux_addressing_table['MCP_address']))])

#
# a_list = np.arange(1,16,1)
# b_list = np.arange(2,17,1)
#
# electrodes = np.array([a_list,b_list]).T
# # print(np.where((mux_addressing_table['Electrode_board_id']==1) & (mux_addressing_table['Role']=='X')))
# for i,relays in enumerate(electrodes):
#     for r in relays:
#         idx = np.where((mux_addressing_table['Electrode_id']== r) & (mux_addressing_table['Role']=='X'))[0]
#         mcp_addr = hex(int(mux_addressing_table['MCP_address'][idx][0],16))
#         print(mcp_addr[0],mux_addressing_table['MCP_address'])
#         time.sleep(.5)
#         set_relay_state(mcp_addr, r, True)
#     #
#     # for r in relays:
#     #     idx = np.where((mux_addressing_table['Electrode_id']== r) & (mux_addressing_table['Role']=='X'))[0]
#     #     mcp_addr = hex(int(mux_addressing_table['MCP_address'][idx][0],16))
#     #     print(r,idx)
#     #     time.sleep(.5)
#     #     set_relay_state(mcp_addr, r, False)
#     #
#     #
#     #
#     # for r in relays:
#     #     set_relay_state(mcp_addr,r,True)
#     #
