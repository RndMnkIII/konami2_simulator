#!/usr/bin/python
import pandas as pd
import sys
import os
from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource
from bokeh.models.tools import HoverTool

import konami2_opcodes as k2op
import konami2_disassembler as k2dis
import eproms

from typing import NamedTuple

from io import StringIO

#print(k2op.konami_opcodes[0x08].name)
#sys.exit()

# if (len(sys.argv) < 2):
# 	print("No especificaste archivo. Saliendo...")
# 	sys.exit()

# output_file('columndatasource_example.html')
	
# archivo_csv = sys.argv[1]
""" archivo_csv = '/home/javier/proyectos/viewcsv/PROG0167.csv'

if os.path.exists(archivo_csv):
	df = pd.read_csv(archivo_csv, delimiter=";", decimal=".")
else:
	sys.exit()

first_time = df['Time'].iloc[0];

df["Time"] = df["Time"].apply(lambda x: (x - first_time) * 1.0E+9) #convert to nanoseconds

df["Time"] = (df["Time"].astype(int))
df["DATA"] = (df["DATA"].astype(str))
df["ADDR"] = (df["ADDR"].astype(str))

posicion=df.index.start

last_clk_val = -1
last_as_val = -1 #df['AS'].iloc[0]
clk_negedge_cnt = 0
last_clk_time = 0
clk_period_sum = 0.0
start_cycle = 0
end_cycle = 0
tmp_pos = 0
address= 'hffff' #df['ADDR'].iloc[0]
data= 'hff' #df['DATA'].iloc[0]

opcodes_array = []

while(posicion < df.index.stop):
	curr_clk_val = df['NCLK12'].iloc[posicion]
	if(curr_clk_val == 0 and last_clk_val == 1):
		clk_negedge_cnt += 1

		curr_as_val = df['AS'].iloc[posicion]
		if(curr_as_val == 0 and last_as_val == 1):
			start_cycle=1
			end_cycle=0
			address = df['ADDR'].iloc[posicion]

		if(curr_as_val == 1 and last_as_val == 0):
			end_cycle=1
			start_cycle=0
			data = 	df['DATA'].iloc[posicion]

		if(end_cycle == 1):
			rw_status = 'R' if df['RW'].iloc[posicion] == 1  else 'W'
			prog_status = 'PROG' if df['PROG'].iloc[posicion] == 0 else ''
			#print("I={0} CLKCNT={1} ADDR={2} DATA={3} {4} {5}".format(posicion, clk_negedge_cnt, address, data, rw_status, prog_status))	
			
			opcodes_array.append(k2dis.OpcodesData(int(address[1:], 16), int(data[1:], 16) )) #convert from hex string to integer bypassing the first character
			end_cycle=0

		last_as_val = curr_as_val

		clk_period_sum += df['Time'].iloc[posicion] - last_clk_time
		#print("{0}: {1} NCKL12 negedge count - Period: {2} - median Period: {3}".format(df['Time'].iloc[posicion], clk_negedge_cnt, (df['Time'].iloc[posicion] - last_clk_time), clk_period_sum / clk_negedge_cnt))
		last_clk_time = df['Time'].iloc[posicion]
		tmp_pos = posicion
	
	last_clk_val = curr_clk_val
	posicion += 1 """

aliens3_eproms = eproms.Konami2eproms()
progROM_data = aliens3_eproms.readall_eprom(eproms.EPROM_Type.PROG)
bankROM_data = aliens3_eproms.readall_eprom(eproms.EPROM_Type.BANK)
konami2_dis = k2dis.Konami2Disassembler()
start_addr = 0x8000
end_addr = start_addr + 0x8000
pc = start_addr

offsetpc = start_addr
while (pc < end_addr):
	output = StringIO()
	offsetpc = konami2_dis.disassembler(pc=pc, stream=output, opcode_data=progROM_data)


	#Start of opcodes format string code
	lista_opcodes = []
	for i in range(pc, pc+offsetpc):
		lista_opcodes.append(progROM_data[i])

	hex_str = ' '.join(['%02X' % b for b in lista_opcodes])

	spc_lst = []
	spc_str=''
	if (len(lista_opcodes) < 4):
		for i in range (4-len(lista_opcodes)):
			spc_lst.append('   ')
		spc_str = ''.join(['%s' % b for b in spc_lst])
	hex_str = hex_str + spc_str
	#End of opcodes format string code

	print("{:04X}: {} {}".format(pc, hex_str, output.getvalue()))
	output.close()
	pc += offsetpc

print('*** BANK ROM ***\n\n')
for bk in range(0,16):

	start_addr = 0x2000 * bk
	end_addr = start_addr + 0x2000
	pc = start_addr
	offsetpc = 0

	print ('\n<<< BANK {:d} >>>\n'.format(bk))
	while (pc < end_addr):
		output = StringIO()
		offsetpc = konami2_dis.disassembler(pc=pc, stream=output, opcode_data=bankROM_data)


		#Start of opcodes format string code
		lista_opcodes = []
		for i in range(pc, pc+offsetpc):
			lista_opcodes.append(bankROM_data[i])

		hex_str = ' '.join(['%02X' % b for b in lista_opcodes])

		spc_lst = []
		spc_str=''
		if (len(lista_opcodes) < 4):
			for i in range (4-len(lista_opcodes)):
				spc_lst.append('   ')
			spc_str = ''.join(['%s' % b for b in spc_lst])
		hex_str = hex_str + spc_str
		#End of opcodes format string code

		print("{:04X}: {} {}".format(pc-start_addr+0x2000, hex_str, output.getvalue()))
		output.close()
		pc += offsetpc


#opc = konami2_dis.fetch_opcode(2, k2op.konami_opcodes, opcodes_array)
# opc = konami2_dis.fetch_opcode(addr, k2op.konami_opcodes, progROM_data)
# if (opc != None):
# 	print("{:04x}: {:02x} - {}".format(addr, progROM_data[addr], opc.name))
# else:
# 	print("Opcode 0x{:02x} not valid!".format(opcodes_array[2].data))	
