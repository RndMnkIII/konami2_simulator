from array import array
from typing import NamedTuple, Dict, List
from ctypes import c_uint8, c_uint16
from enum import Enum
import os
import sys
import numpy as np
import curses
import time
#from eproms import EPROM_Type, EPROM_entry, Konami2eproms

class EPROM_Type(Enum):
    PROG = 1
    BANK = 2
    TILE = 3
    SPRITE = 4
    AUDIO = 5
    PROM = 6

class EPROM_entry(NamedTuple):
    rom_data: array
    size:int = 0
    path:str = ''
    path2:str = ''
    path3:str = ''
    path4:str = ''

class Konami2eproms:

    #default locations for eproms
    __load_status = True 
    rom_map = {}
    rom_bank = []
    ram_bank = []
    __rom_bank_num_entries:c_uint8 = 0
    __m_curr_romentry:c_uint8 = 0
    #banked_rom

    def __init__(self, modo_dbg: bool) -> None:
        #load the EPROMS
        if (modo_dbg == True):
            #progf = '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875_w3_2.e24'
            #bankf = '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875_w3_1.c24'
            self.progf =   '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875_w3_2.e24'
            self.bankf =   '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875_w3_1.c24'

            self.tile0 =   '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875b11.k13'
            self.tile1 =   '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875b12.k19'
            self.tile2 =   '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875b07.j13'
            self.tile3 =   '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875b08.j19'

            self.sprite0 = '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875b10.k08'
            self.sprite1 = '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875b09.k02'
            self.sprite2 = '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875b06.j08'
            self.sprite3 = '/storage/emulated/0/qpython/projects3/konami2_simulator/eproms/875b05.j02'

            self.audio   = './eproms/875b04.e05'
            self.prom    = './eproms/821a08.h14'
        else:
            self.progf =   './eproms/875_w3_2.e24'
            self.bankf =   './eproms/875_w3_1.c24'

            self.tile0 =   './eproms/875b11.k13'
            #self.tile0 =   './eproms/parodius/955d07.k19'
            self.tile1 =   './eproms/875b12.k19'
            #self.tile1 =   './eproms/parodius/955d08.k24'

            self.tile2 =   './eproms/875b07.j13'
            self.tile3 =   './eproms/875b08.j19'

            self.sprite0 = './eproms/875b10.k08'
            self.sprite1 = './eproms/875b09.k02'
            self.sprite2 = './eproms/875b06.j08'
            self.sprite3 = './eproms/875b05.j02'

            self.audio   = './eproms/875b04.e05'
            self.prom    = './eproms/821a08.h14'            
        
        if os.path.exists(self.progf):
            self.rom_map[EPROM_Type.PROG] = EPROM_entry(rom_data=array('B'), size=os.path.getsize(self.progf), path=self.progf)
            try:
                with open(self.progf, 'rb') as f:
                    self.rom_map[EPROM_Type.PROG].rom_data.fromfile(f, self.rom_map[EPROM_Type.PROG].size)
            except :
                self.__load_status = False

        if os.path.exists(self.bankf):
            self.rom_map[EPROM_Type.BANK] = EPROM_entry(rom_data=array('B'), size=os.path.getsize(self.bankf), path=self.bankf)
            try:
                with open(self.bankf, 'rb') as f:
                    self.rom_map[EPROM_Type.BANK].rom_data.fromfile(f, self.rom_map[EPROM_Type.BANK].size)
            except :
                self.__load_status = False

        #Audio ROM MASK4MA is readed in BYTE mode, O15 is used as Address pin 0 (AS0). Only O0-O7 are used as data oputput
        if os.path.exists(self.audio):
            self.rom_map[EPROM_Type.AUDIO] = EPROM_entry(rom_data=array('B'), size=os.path.getsize(self.audio), path=self.audio)
            try:
                with open(self.audio, 'rb') as f:
                    self.rom_map[EPROM_Type.AUDIO].rom_data.fromfile(f, self.rom_map[EPROM_Type.AUDIO].size)
            except :
                self.__load_status = False

        #PROM only generates 4bit value for a given address, and in Aliens arcade only 2 LSBits are used
        if os.path.exists(self.prom):
            self.rom_map[EPROM_Type.PROM] = EPROM_entry(rom_data=array('B'), size=os.path.getsize(self.prom), path=self.prom)
            try:
                with open(self.prom, 'rb') as f:
                    self.rom_map[EPROM_Type.PROM].rom_data.fromfile(f, self.rom_map[EPROM_Type.PROM].size)
            except :
                self.__load_status = False

        #Tile ROMs MASK4MA is readed in WORD mode (big-endian order), O0-O15 are used as data outut. The address A0=1 means +2byte increment in address space
        #The Tile ROMs are read in simultaneously in pairs, resulting in an 32 bit data value read in a single bus cycle.
        if (os.path.exists(self.tile0) and os.path.exists(self.tile1) and os.path.exists(self.tile2) and os.path.exists(self.tile3)):

            self.rom_map[EPROM_Type.TILE] = EPROM_entry(rom_data=array('I'), 
            size=(os.path.getsize(self.tile0)+os.path.getsize(self.tile1)+os.path.getsize(self.tile2)+os.path.getsize(self.tile3)),
            path=self.tile0, path2=self.tile1, path3=self.tile2, path4=self.tile3)
            try: 
                fpos = 0
                ftilesize=os.path.getsize(self.tile0)
                with open(self.tile0, 'rb') as ftile0, open(self.tile1, 'rb') as ftile1:
                    while (fpos < ftilesize):
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(int.from_bytes(ftile0.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(int.from_bytes(ftile0.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(int.from_bytes(ftile1.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(int.from_bytes(ftile1.read(1), byteorder='big'))
                        # fpos+=2
                        # hiword = ftile1.read(2)
                        # hival = int.from_bytes(hiword, byteorder='big')
                        # hivalshifted = hival << 16
                        # loword = ftile0.read(2)
                        # loval = int.from_bytes(loword, byteorder='big')
                        # lovalmasked = loval & 0xFFFF
                        # valor =  hivalshifted | lovalmasked
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(valor)

                        valor = (int.from_bytes(ftile0.read(2), byteorder='big') << 16) | (int.from_bytes(ftile1.read(2), byteorder='big') & 0xFFFF)
                        self.rom_map[EPROM_Type.TILE].rom_data.append(valor)
                        fpos+=2

                fpos = 0
                ftilesize=os.path.getsize(self.tile2)
                with open(self.tile2, 'rb') as ftile2, open(self.tile3, 'rb') as ftile3:
                    while (fpos < ftilesize):
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(int.from_bytes(ftile2.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(int.from_bytes(ftile2.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(int.from_bytes(ftile3.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.TILE].rom_data.append(int.from_bytes(ftile3.read(1), byteorder='big'))
                        # fpos+=2 
                        valor = (int.from_bytes(ftile2.read(2), byteorder='big') << 16) | (int.from_bytes(ftile3.read(2), byteorder='big') & 0xFFFF)
                        self.rom_map[EPROM_Type.TILE].rom_data.append(valor)
                        fpos+=2

            except Exception as e:
                print(e)
                self.__load_status = False  

        #Sprite ROMs MASK4MA is readed in WORD mode (big-endian order), O0-O15 are used as data outut. The address A0=1 means +2byte increment in address space
        #The Sprite ROMs are read in simultaneously in pairs, resulting in an 32 bit data value read in a single bus cycle.
        if (os.path.exists(self.sprite0) and os.path.exists(self.sprite1) and os.path.exists(self.sprite2) and os.path.exists(self.sprite3)):
            
            # self.rom_map[EPROM_Type.SPRITE] = EPROM_entry(rom_data=array('B'), 
            # size=(os.path.getsize(self.sprite0)+os.path.getsize(self.sprite1)+os.path.getsize(self.sprite2)+os.path.getsize(self.sprite3)),
            # path=self.sprite0, path2=self.sprite1, path3=self.sprite2, path4=self.sprite3)

            # Array of unsigned long items, view item size with array.itemsize attribute: I uint L ulong B ubyte
            self.rom_map[EPROM_Type.SPRITE] = EPROM_entry(rom_data=array('I'), 
            size=(os.path.getsize(self.sprite0)+os.path.getsize(self.sprite1)+os.path.getsize(self.sprite2)+os.path.getsize(self.sprite3)),
            path=self.sprite0, path2=self.sprite1, path3=self.sprite2, path4=self.sprite3)         

            try: 
                fpos = 0
                fspritesize=os.path.getsize(self.sprite0)
                with open(self.sprite0, 'rb') as fsprite0, open(self.sprite1, 'rb') as fsprite1:
                    while (fpos < fspritesize):
                        # self.rom_map[EPROM_Type.SPRITE].rom_data.append(int.from_bytes(fsprite0.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.SPRITE].rom_data.append(int.from_bytes(fsprite0.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.SPRITE].rom_data.append(int.from_bytes(fsprite1.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.SPRITE].rom_data.append(int.from_bytes(fsprite1.read(1), byteorder='big'))
                        # fpos+=2
                         # Array of unsigned long items, view item size with array.itemsize attribute:
                        valor = (int.from_bytes(fsprite0.read(2), byteorder='big') << 16) | (int.from_bytes(fsprite1.read(2), byteorder='big') & 0xFFFF)
                        self.rom_map[EPROM_Type.SPRITE].rom_data.append(valor)
                        fpos+=2


                fpos = 0
                fspritesize=os.path.getsize(self.sprite2)
                with open(self.sprite2, 'rb') as fsprite2, open(self.sprite3, 'rb') as fsprite3:
                    while (fpos < fspritesize):
                        # self.rom_map[EPROM_Type.SPRITE].rom_data.append(int.from_bytes(fsprite2.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.SPRITE].rom_data.append(int.from_bytes(fsprite2.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.SPRITE].rom_data.append(int.from_bytes(fsprite3.read(1), byteorder='big'))
                        # self.rom_map[EPROM_Type.SPRITE].rom_data.append(int.from_bytes(fsprite3.read(1), byteorder='big'))
                        # fpos+=2
                        valor = (int.from_bytes(fsprite2.read(2), byteorder='big') << 16) |  (int.from_bytes(fsprite3.read(2), byteorder='big') & 0xFFFF)
                        self.rom_map[EPROM_Type.SPRITE].rom_data.append(valor)
                        fpos+=2

            except Exception as e:
                print(e)
                self.__load_status = False     

        self.rom_bank = self.create_rombank()
        self.__rom_bank_num_entries = len(self.rom_bank)
        self.__m_curr_romentry = 0

    def get_rombank(self)-> array:
        return self.rom_bank[self.__m_curr_romentry]
    
    def read_rombank_data(self, offset: c_uint16) -> c_uint8:
        return self.rom_bank[self.__m_curr_romentry][offset]

    def get_rombank_entry(self, num:c_uint8) -> array:
        return self.rom_bank[num & 0x1F]

    def read_rombank_entry_data(self, num:c_uint8, offset:c_uint16) -> c_uint8:
        return self.rom_bank[num & 0x1F][offset]        

    def get_rombank_numentries(self) -> c_uint8:
        return self.__rom_bank_num_entries

    def set_rombank(self, numentry: c_uint8) -> None:
        self.__m_curr_romentry = 0x1F & numentry

    def read_prog_data(self, offset: c_uint16) -> c_uint8:
        return self.rom_map[EPROM_Type.PROG].rom_data[offset]

    def load_status(self) -> bool:
        return self.__load_status

    def read_eprom(self, eprom_type : EPROM_Type, addr : int) -> int:
        if (self.__load_status == True):
            if(addr in range(0, self.rom_map[eprom_type].size)):
                return self.rom_map[eprom_type].rom_data[addr]
        else:
            return -1

    def readall_eprom(self, eprom_type : EPROM_Type) -> array:
        if (self.__load_status == True):
            return self.rom_map[eprom_type].rom_data
        else:
            return None

    def create_rombank(self) -> List[array]:
        rom_bnk = []
        NUM_ENTRIES_BANKROM = 16
        STRIDE = 0x2000
        for entry in range(0, NUM_ENTRIES_BANKROM):
            rom_bnk.append(self.readall_eprom(EPROM_Type.BANK)[entry * STRIDE: (entry+1)*STRIDE])

        rom_bnk.append(self.readall_eprom(EPROM_Type.PROG)[0x0:0x2000])
        rom_bnk.append(self.readall_eprom(EPROM_Type.PROG)[0x2000:0x4000])
        rom_bnk.append(self.readall_eprom(EPROM_Type.PROG)[0x4000:0x6000])
        rom_bnk.append(self.readall_eprom(EPROM_Type.PROG)[0x6000:0x8000])  

        return rom_bnk

    def create_RAM_entry(self, size: c_uint16) -> None:
        ram_entry = array('B', [0 for _ in range(size)])
        self.ram_bank.append(ram_entry)

    def get_RAM_entry(self, num:c_uint8) -> array:
        return self.ram_bank[num]
    
    def read_RAM_entry_data(self, num:c_uint8, offset: c_uint16) -> c_uint8:
        return self.ram_bank[num][offset]

    def read_RAM_entry_data16(self, num:c_uint8, offset: c_uint16) -> c_uint16:
        return (self.ram_bank[num][offset] << 8) + self.ram_bank[num][offset+1]        

    def write_RAM_entry_data(self, num:c_uint8, offset: c_uint16, data: c_uint8) -> None:
        self.ram_bank[num][offset] = data

    ###Define only for eproms.py debug ###
    def cram_write(self, addr: c_uint16, data: c_uint8) -> None:
        bank = addr & 0x1 #A0=0 even addr, data store in e15 (upper),else A0=1 odd addr stored in e14
        new_addr:c_uint16 = 0
        if (bank==0):
            new_addr |= (addr & 0x2)        #A1 -> A1 
            new_addr |= ((addr & 0x4)<<2)   #A2 -> A4
            new_addr |= ((addr & 0x8)>>1)   #A3 -> A2
            new_addr |= ((addr & 0x10)>>1)   #A4 -> A3
            new_addr |= ((addr & 0x20)<<3)   #A5 -> A8
            new_addr |= ((addr & 0x40)<<1)   #A6 -> A7
            new_addr |= ((addr & 0x80)>>1)   #A7 -> A6
            new_addr |= ((addr & 0x100)>>8)   #A8 -> A0
            new_addr |= ((addr & 0x200)>>4)   #A9 -> A5
            self.write_RAM_entry_data(num=1, offset=new_addr, data=data)
        else:
            new_addr |= (addr & 0x2)        #A1 -> A1 
            new_addr |= ((addr & 0x4)<<2)   #A2 -> A4
            new_addr |= ((addr & 0x8)>>1)   #A3 -> A2
            new_addr |= ((addr & 0x10)>>1)   #A4 -> A3
            new_addr |= ((addr & 0x20)<<2)   #A5 -> A7
            new_addr |= ((addr & 0x40)<<2)   #A6 -> A8
            new_addr |= ((addr & 0x80)>>1)   #A7 -> A6
            new_addr |= ((addr & 0x100)>>8)   #A8 -> A0
            new_addr |= ((addr & 0x200)>>4)   #A9 -> A5
            self.write_RAM_entry_data(num=4, offset=new_addr, data=data)

    def cram_read(self, addr: c_uint16) -> c_uint8:        
        bank = addr & 0x1 #A0=0 even addr, data store in e15 (upper),else A0=1 odd addr stored in e14
        new_addr:c_uint16 = 0
        if (bank==0): #TOP BANK
            new_addr |= (addr & 0x2)        #A1 -> A1 
            new_addr |= ((addr & 0x4)<<2)   #A2 -> A4
            new_addr |= ((addr & 0x8)>>1)   #A3 -> A2
            new_addr |= ((addr & 0x10)>>1)   #A4 -> A3
            new_addr |= ((addr & 0x20)<<3)   #A5 -> A8
            new_addr |= ((addr & 0x40)<<1)   #A6 -> A7
            new_addr |= ((addr & 0x80)>>1)   #A7 -> A6
            new_addr |= ((addr & 0x100)>>8)   #A8 -> A0
            new_addr |= ((addr & 0x200)>>4)   #A9 -> A5
            return self.read_RAM_entry_data(num=1, offset=new_addr)
        else:   #BOTTOM BANK
            new_addr |= (addr & 0x2)        #A1 -> A1 
            new_addr |= ((addr & 0x4)<<2)   #A2 -> A4
            new_addr |= ((addr & 0x8)>>1)   #A3 -> A2
            new_addr |= ((addr & 0x10)>>1)   #A4 -> A3
            new_addr |= ((addr & 0x20)<<2)   #A5 -> A7
            new_addr |= ((addr & 0x40)<<2)   #A6 -> A8
            new_addr |= ((addr & 0x80)>>1)   #A7 -> A6
            new_addr |= ((addr & 0x100)>>8)   #A8 -> A0
            new_addr |= ((addr & 0x200)>>4)   #A9 -> A5
            return self.read_RAM_entry_data(num=4, offset=new_addr)

    def cram_read16(self, addr: c_uint16) -> c_uint16:
        new_addr_up:c_uint16 = 0
        new_addr_lo:c_uint16 = 0
        #UPPER BANK  
        new_addr_up |= (addr & 0x2)        #A1 -> A1 
        new_addr_up |= ((addr & 0x4)<<2)   #A2 -> A4
        new_addr_up |= ((addr & 0x8)>>1)   #A3 -> A2
        new_addr_up |= ((addr & 0x10)>>1)   #A4 -> A3
        new_addr_up |= ((addr & 0x20)<<3)   #A5 -> A8
        new_addr_up |= ((addr & 0x40)<<1)   #A6 -> A7
        new_addr_up |= ((addr & 0x80)>>1)   #A7 -> A6
        new_addr_up |= ((addr & 0x100)>>8)   #A8 -> A0
        new_addr_up |= ((addr & 0x200)>>4)   #A9 -> A5
        #LOWER BANK
        new_addr_lo |= (addr & 0x2)        #A1 -> A1 
        new_addr_lo |= ((addr & 0x4)<<2)   #A2 -> A4
        new_addr_lo |= ((addr & 0x8)>>1)   #A3 -> A2
        new_addr_lo |= ((addr & 0x10)>>1)   #A4 -> A3
        new_addr_lo |= ((addr & 0x20)<<2)   #A5 -> A7
        new_addr_lo |= ((addr & 0x40)<<2)   #A6 -> A8
        new_addr_lo |= ((addr & 0x80)>>1)   #A7 -> A6
        new_addr_lo |= ((addr & 0x100)>>8)   #A8 -> A0
        new_addr_lo |= ((addr & 0x200)>>4)   #A9 -> A5
        return (self.read_RAM_entry_data(num=1, offset=new_addr_up) << 8) | self.read_RAM_entry_data(num=4, offset=new_addr_lo) 

if __name__ == "__main__":
    modo_dbg = False 

    if(sys.gettrace() != None):
        #print('*** Modo depuracion ***')
        modo_dbg = True

    mirommap =  Konami2eproms(modo_dbg=modo_dbg)

    mirommap.create_RAM_entry(0x2000) #Work RAM
    mirommap.create_RAM_entry(0x200) #Color RAM TOP E15 W15-W8
    mirommap.create_RAM_entry(0x400) #SPRITE RAM
    mirommap.create_RAM_entry(0x4000) #TILEMAP RAM
    mirommap.create_RAM_entry(0x200) #Color RAM BOTTON E14 W7-W0

#     for value in range (0,0x10000):
#         print(f"Testing 0x{value:04x}")
#         for pos in range(0,0x400, 2):
#             mirommap.cram_write(pos, value>>8)
#             mirommap.cram_write(pos+1, value & 0xff)
#         for pos in range(0,0x400, 2):    
#             readval = (mirommap.cram_read(pos) << 8) |  mirommap.cram_read(pos+1)
#             readval2 =  mirommap.cram_read16(pos)
#             if (readval != value):
#                 print(f"No coindice value: 0x{value:04x} con read value: 0x {readval:04x}")
#                 sys.exit()
#             if (readval2 != value):
#                 print(f"No coindice value: 0x{value:04x} con read value (cram16): 0x {readval2:04x}")
#                 sys.exit()


    # mirommap.cram_write(0x0,0x55)
    # mirommap.cram_write(0x1,0xaa)
    # mirommap.cram_write(0x2,0xff)
    # mirommap.cram_write(0x3,0xbb)
    # mirommap.cram_write(0xfffc,0x22)
    # mirommap.cram_write(0xfffd,0x77)
    # mirommap.cram_write(0xfffe,0xee)
    # mirommap.cram_write(0xffff,0xcc)
    # print(f"{mirommap.cram_read(0x0):02X}")
    # print(f"{mirommap.cram_read(0x1):02X}")
    # print(f"{mirommap.cram_read16(0x0):04X}")
    # print(f"{mirommap.cram_read16(0x2):04X}")
    # print(f"{mirommap.cram_read(0xfffc):02X}")
    # print(f"{mirommap.cram_read(0xfffd):02X}")
    # print(f"{mirommap.cram_read16(0xfffc):04X}")
    # print(f"{mirommap.cram_read16(0xfffe):04X}")
    #sys.exit()

    # CHAR_ROM= (" ABCDEFGHIJ█▒░◇◈")

    #     # #curses init
    # stdscr = curses.initscr()
    # curses.noecho()
    # curses.cbreak()
    # stdscr.keypad(True)
    
    # # Start colors in curses
    # curses.start_color()
    # curses.init_color(30, 700 ,0 ,700) #RGB (0-1000) RANGE VALUE) VIOLET
    # curses.init_color(31, 700 ,700 ,700) #RGB (0-1000) RANGE VALUE) LIGHT GRAY 30%
    # curses.init_color(29, 500 ,500 ,500) #RGB (0-1000) RANGE VALUE) LIGHT GRAY 30%
    # curses.init_color(28, 300 ,300 ,300) #RGB (0-1000) RANGE VALUE) LIGHT GRAY 30%
    # curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLACK)
    # curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_WHITE)
    # curses.init_pair(3, curses.COLOR_GREEN, 31)
    # curses.init_pair(4, 30 ,curses.COLOR_WHITE)
    # curses.init_pair(5, curses.COLOR_CYAN, 31)
    # curses.init_pair(6, 30, curses.COLOR_WHITE)
    # curses.init_pair(7, curses.COLOR_BLUE, 31)
    # curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_BLACK)
    # curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLACK)
    # curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_BLACK)
    # curses.init_pair(11, 30, curses.COLOR_BLACK)
    # curses.init_pair(12, 31, curses.COLOR_BLACK)
    # curses.init_pair(13, 29, curses.COLOR_BLACK)
    # curses.init_pair(14, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    # curses.init_pair(15, curses.COLOR_RED, curses.COLOR_BLACK)
    # curses.init_pair(16, 31, curses.COLOR_BLACK)
    # time.sleep(2)
    # for i in range(0,16):
    #     curses.init_color(i+16, i*66,i*66 ,i*66) #RGB (0-1000) RANGE VALUE) VIOLET
    #     curses.init_pair(i+16, i+16, curses.COLOR_BLACK)

    # # curses.resize_term(60,310)
    # curses.resize_term(130, 600)

    # # # Clear and refresh the screen for a blank canvas
    # stdscr.clear()

    # tile_rom_pixels = np.empty(8, dtype=np.uint32)
    # #for i in range(0x0,0xf*8):
    # for z in range(0, 3072):
    #     for i in range(0,8):
    #         for j in range(0,256,8):
    #             valor = mirommap.rom_map[EPROM_Type.TILE].rom_data[z*0x80+i+j]
    #             #print(f"{valor:08X}")
    #             tile_rom_pixels[0] = ((valor & 0x80000000) >> 31) | ((valor & 0x800000) >> 22) | ((valor & 0x8000) >> 13) | ((valor & 0x80) >> 4) 
    #             tile_rom_pixels[1] = ((valor & 0x40000000) >> 30) | ((valor & 0x400000) >> 21) | ((valor & 0x4000) >> 12) | ((valor & 0x40) >> 3) 
    #             tile_rom_pixels[2] = ((valor & 0x20000000) >> 29) | ((valor & 0x200000) >> 20) | ((valor & 0x2000) >> 11) | ((valor & 0x20) >> 2) 
    #             tile_rom_pixels[3] = ((valor & 0x10000000) >> 28) | ((valor & 0x100000) >> 19) | ((valor & 0x1000) >> 10) | ((valor & 0x10) >> 1) 
    #             tile_rom_pixels[4] = ((valor & 0x08000000) >> 27) | ((valor & 0x080000) >> 18) | ((valor & 0x0800) >> 9) | (valor & 0x08) 
    #             tile_rom_pixels[5] = ((valor & 0x04000000) >> 26) | ((valor & 0x040000) >> 17) | ((valor & 0x0400) >> 8) | ((valor & 0x04) << 1) 
    #             tile_rom_pixels[6] = ((valor & 0x02000000) >> 25) | ((valor & 0x020000) >> 16) | ((valor & 0x0200) >> 7) | ((valor & 0x02) << 2) 
    #             tile_rom_pixels[7] = ((valor & 0x01000000) >> 24) | ((valor & 0x010000) >> 15) | ((valor & 0x0100) >> 6) | ((valor & 0x01) << 3)
    #             stdscr.addstr(i+(z%15)*8, j, "█", curses.color_pair(tile_rom_pixels[0]+16))
    #             stdscr.addstr(i+(z%15)*8, j+1, "█", curses.color_pair(tile_rom_pixels[1]+16))
    #             stdscr.addstr(i+(z%15)*8, j+2, "█", curses.color_pair(tile_rom_pixels[2]+16))
    #             stdscr.addstr(i+(z%15)*8, j+3, "█", curses.color_pair(tile_rom_pixels[3]+16))
    #             stdscr.addstr(i+(z%15)*8, j+4, "█", curses.color_pair(tile_rom_pixels[4]+16))
    #             stdscr.addstr(i+(z%15)*8, j+5, "█", curses.color_pair(tile_rom_pixels[5]+16))
    #             stdscr.addstr(i+(z%15)*8, j+6, "█", curses.color_pair(tile_rom_pixels[6]+16))
    #             stdscr.addstr(i+(z%15)*8, j+7, "█", curses.color_pair(tile_rom_pixels[7]+16))
    #     if(z%15 == 14):
    #         stdscr.refresh()
    #         time.sleep(1)
    # curses.nocbreak()
    # stdscr.keypad(False)
    # curses.echo()
    # curses.endwin()
        # print(f"{CHAR_ROM[tile_rom_pixels[0]]}", end='')
        # print(f"{CHAR_ROM[tile_rom_pixels[1]]}", end='')
        # print(f"{CHAR_ROM[tile_rom_pixels[2]]}", end='')
        # print(f"{CHAR_ROM[tile_rom_pixels[3]]}", end='')
        # print(f"{CHAR_ROM[tile_rom_pixels[4]]}", end='')
        # print(f"{CHAR_ROM[tile_rom_pixels[5]]}", end='')
        # print(f"{CHAR_ROM[tile_rom_pixels[6]]}", end='')
        # print(f"{CHAR_ROM[tile_rom_pixels[7]]}")


#     #for addrc in range (0xfff0, 0x10000): 
#     #    print('{:04x}: {:02x}'.format( addrc, mirommap.read_eprom(EPROM_Type.PROG, addrc)))
#     #print(mirommap.readall_eprom(EPROM_Type.PROG))
#     # print(type(mirommap.rom_map[EPROM_Type.PROG]))
#     # print(mirommap.rom_map[EPROM_Type.PROG].size)

#     print("*** ROM Bank ***")
#     print(f"Rombank.get_rombank_data: {mirommap.read_rombank_data(0):02X}")
#     print(f"Rombank: {mirommap.rom_bank[0][0]:02X}")
#     print()
#     print(mirommap.rom_map[EPROM_Type.PROG].size)
#     print(mirommap.rom_map[EPROM_Type.BANK].size)
#     print()
#     print("*** RAM Bank ***")
#     mirommap.create_RAM_entry(0x2000)
#     mirommap.create_RAM_entry(0x400) #CRAM
#     mirommap.write_RAM_entry_data(0, 0x0, 0xfa)
#     print(f"RAM bank: {mirommap.read_RAM_entry_data(0, 0x0):02X}")
#     print()
    print("*** Tile ***")
    print(mirommap.rom_map[EPROM_Type.TILE].size)
    print(mirommap.rom_map[EPROM_Type.TILE].rom_data.itemsize)
    print(len(mirommap.rom_map[EPROM_Type.TILE].rom_data))
    print(f"0:{mirommap.rom_map[EPROM_Type.TILE].rom_data[0]:08X}")
    print(f"1:{mirommap.rom_map[EPROM_Type.TILE].rom_data[1]:08X}")
    print(f"2:{mirommap.rom_map[EPROM_Type.TILE].rom_data[2]:08X}")
    print(f"3:{mirommap.rom_map[EPROM_Type.TILE].rom_data[3]:08X}")
    print(f"3:{mirommap.rom_map[EPROM_Type.TILE].rom_data[0x451]:08X}")
#     print()
#     print("*** Sprite ***")
#     print(mirommap.rom_map[EPROM_Type.SPRITE].size)
#     print(mirommap.rom_map[EPROM_Type.SPRITE].rom_data.itemsize)
#     print(len(mirommap.rom_map[EPROM_Type.SPRITE].rom_data))
#     print(f"{mirommap.rom_map[EPROM_Type.SPRITE].rom_data[0]:08X}")
#     print()
#     print("*** Audio ***")
#     print(mirommap.rom_map[EPROM_Type.AUDIO].size)
#     print(mirommap.rom_map[EPROM_Type.AUDIO].rom_data.itemsize)
#     print(len(mirommap.rom_map[EPROM_Type.AUDIO].rom_data))
#     print()
#     print(mirommap.rom_map[EPROM_Type.PROM].size)


