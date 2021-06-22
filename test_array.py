from array import array
from typing import NamedTuple, Dict, List
from enum import Enum
import os
import sys

PROG_EPROM = './eproms/875_j02.e24'
prog_rom = array('B')
tam = 0

class EPROM_entry(NamedTuple):
    rom_data: array
    size: int
    path: str

if os.path.exists(PROG_EPROM): 
    
    
    tam = os.path.getsize(PROG_EPROM)
    rom1 = EPROM_entry(rom_data = array('B'), size=tam, path=PROG_EPROM)
    with open(PROG_EPROM, 'rb') as f:
        try:
            rom1.rom_data.fromfile(f, tam)
            
        except:
            print("Error cargando fichero")
            sys.exit()
        print(rom1.rom_data)

