#from memory_mapper import SELECTOR, memory_mapper
from array import array
from typing import NamedTuple, List, TypeVar, Type
from enum import Enum
from ctypes import sizeof, byref, pointer, Union, Structure, c_int, c_ulong, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32
from eproms import EPROM_Type, EPROM_entry, Konami2eproms
from konami2 import konami2_cpu_device
from m6809_types import ADRMOD, exgtfr_register, FLAGS, CPUVECT, LINEDEF, line_state, IRQLINE
from konami2_types import KIRQLINE
import logging

#logging.basicConfig(filename='memory_mapper.log',level=logging.INFO)
class SELECTOR(Enum):
    NONE = 0x0 #RMRD?

    PROG = 0x1
    WORK = 0x2
    BANK = 0x4
    IOCS = 0x8

    CRAMCS = 0X10
    VRAMCS = 0x20
    OBJCS = 0x40

    #CONTROL1 = 0X80
    DSW3 = 0X80
    P1 =  0X100
    P2 = 0X200
    DSW1 = 0X400

    #CONTROL2 = 0X800
    DSW2 = 0X800
    COUNT = 0X1000
    SOUND = 0X2000
    
    D21_12 = 0x4000

    D21_15 = 0x8000
    D21_16 = 0x10000
    D21_17 = 0x20000
    D21_19 = 0x40000

    R14 = 0x80000
    R15 = 0x100000
    D20_12 = 0x200000

class memory_mapper():
    #private class members
    __AS:bool
    __BK4:bool
    __INIT:bool
    __WOCO:bool
    __RMRD:bool = False
    __coin_counter1:int=0
    __coin_counter2:int=0
    __last_coin1:int=0
    __last_coin2:int=0

    def __init__(self, cpu:konami2_cpu_device=None,  memory:Konami2eproms=None, AS:bool=False, BK4:bool=False, INIT:bool=False, WOCO:bool=False, RMRD:bool=False) -> None:
        self.memory = memory
        self.cpu = cpu
        self.__AS = AS
        self.__BK4 = BK4
        self.__INIT = INIT
        self.__WOCO = WOCO
        self.__RMRD = RMRD
        self.d18_5_val:bool = False
        self.m_cram:c_uint8 = 0
        self.m_cram_update:c_uint16 = 0
        self.m_rmrd:c_uint8 = 0
        self.m_init:c_uint8 = 0
        self.m_prog:c_uint8 = 0
        self.m_work:c_uint8 = 0
        self.m_bank:c_uint8 = 0
        self.m_videocs:c_uint8=0
        self.m_vupdate:c_uint8=0
        self.m_objcs:c_uint8=0
        self.m_readroms:c_uint8=0
        self.m_spriterombank = [0,0,0]

        #k052109 state:
        self.m_scrollctrl:c_uint8=0
        self.m_romsubbank:c_uint8=0
        self.m_has_extra_video_ram:c_uint8=0
        self.m_k052109_charrombank = [0, 0, 0, 0]
        self.m_k052109_charrombank2 = [0, 0, 0, 0]
        self.m_k052109_tileflip_en:c_uint8=0
        self.m_irq_enabled:bool = False
        logging.info('<<< K051937 INIT >>>')

        #k051937_r state:
        self.m_k051937_vblank:bool=False

    def set_AS(self, AS:bool) -> None:
        self.__AS = AS

    def set_BK4(self, BK4:bool) -> None:
        self.__BK4 = BK4

    def get_BK4(self) -> bool:
        return self.__BK4       

    def set_INIT(self, INIT:bool) -> None:
        self.__INIT = INIT        

    def set_WOCO(self, WOCO:bool) -> None:
        self.__WOCO = WOCO

    def set_RMRD(self, RMRD:bool) -> None:
        self.__RMRD = RMRD

    def read16(self, addr:c_uint16) -> c_uint16:
        return ((self.read(addr) << 8) | self.read(addr+1)) #big-endian order

    def read32(self, addr:c_uint16) -> c_uint32:
        return ((self.read(addr) << 24) | (self.read(addr+1) << 16) | (self.read(addr+2) << 8) | self.read(addr+3)) #big-endian order        

    def read(self, addr:c_uint16) -> c_uint8:
        self.m_prog = 0
        self.m_bank = 0
        self.m_work = 0
        self.m_cram = 0
        self.m_videocs = 0
        self.m_objcs = 0

        sel = self.decoder(ADDR=addr, CLKQ_risedge_tick=True)
        if(sel & SELECTOR.COUNT.value):
            #set watchdog timer
            return 0x00 #TST $5F88, BNE $9E85

        elif(sel & SELECTOR.CRAMCS.value):
        #elif(self.__WOCO and addr in range(0x000,0x3ff+1)):
            self.m_cram = 1
            #return self.memory.read_RAM_entry_data(num=1, offset=addr)
            return self.cram_read(addr=addr)

        elif(sel & SELECTOR.WORK.value):
            self.m_work = 1
            # *** READ WATCHPOINTS ***
            # if (self.cpu.m_wp_addr1 == addr):
            #     self.cpu.m_wp1 = 1
            #     self.cpu.m_wp_val1 = self.memory.read_RAM_entry_data(num=0, offset=addr)
            #     return self.cpu.m_wp_val1
            # else:
            return self.memory.read_RAM_entry_data(num=0, offset=addr)

        elif(sel & SELECTOR.BANK.value):
            # adjust address offset to 0-0x2000 window banks 0x0-0xf maps to BANK ROM (16*8KB) when BK4=False, 
            self.m_bank = 1
            return self.memory.read_rombank_data(offset=addr - 0x2000)

        elif(sel & SELECTOR.PROG.value):
            self.m_prog = 1
            if(addr in range(0x8000, 0xffff+1)):
                return self.memory.read_prog_data(offset=addr) #addr should be in range (0x8000-0xffff)
            else:
                #addr in range(0x2000-0x3fff)
                # banks 0x10-0x13 maps to PROG ROM 0x0-0x7FFF address range in chunks 0f 0x2000 bytes when BK4=True
                return self.memory.read_rombank_data(offset=addr - 0x2000)
                
        elif(sel & SELECTOR.IOCS.value):
            if(sel & SELECTOR.DSW3.value):
                return 0xFF
            elif(sel & SELECTOR.DSW2.value):
                return 0xAF #coin A 1Coin/1 Credit, coin B 1 Coin/6 Credits
            elif(sel & SELECTOR.DSW1.value):
                return 0xFF
            elif(sel & SELECTOR.P1.value):
                return 0xFF
            elif(sel & SELECTOR.P2.value):
                return 0xFF
            elif(sel & SELECTOR.COUNT.value):
                return self.count_r()

        elif(sel & SELECTOR.VRAMCS.value):
            # data = self.memory.read_RAM_entry_data(num=3, offset=addr - 0x4000)
            # print(f"<<<k052109_r {addr:04X}:{data:02X}")
            # return data
            self.m_videocs = 1
            return self.memory.read_RAM_entry_data(num=3, offset=addr - 0x4000)
            #return self.memory.read_RAM_entry_data(num=3, offset=addr - 0x4000) & 0xef #simulated error on VRAM output
            
        elif(sel & SELECTOR.OBJCS.value):
            self.m_objcs = 1
            #logging.info('<<< OBJCS SELECTOR >>>')
            if addr >= 0x7c00 and addr < 0x8000: #in range (0x7c00, 0x8000):
                return self.k051960_r(offset=addr - 0x7C00)
            else:
                return self.k051937_r(offset=addr - 0x7800)

    def read_opcode(self, addr:c_uint16) -> c_uint8:
        return self.read(addr=addr)

    def read_opcode_arg(self, addr:c_uint16) -> c_uint8:
        return self.read(addr=addr)        
        
    def write(self, addr:c_uint16, data: c_uint8) -> None:
        self.m_prog = 0
        self.m_bank = 0
        self.m_work = 0
        self.m_cram = 0
        self.m_videocs = 0
        self.m_objcs = 0

        sel = self.decoder(ADDR=addr, CLKQ_risedge_tick=True)
        
        if(sel & SELECTOR.IOCS.value):
            if(sel & SELECTOR.COUNT.value):
                self.count_w(data)
            elif(sel & SELECTOR.SOUND.value):
                #write data to sound latch
                pass

        elif(sel & SELECTOR.CRAMCS.value):
        #elif(self.__WOCO and addr in range(0x000,0x3ff+1)):
            self.m_cram=1
            self.m_cram_update=1
            self.cram_write(addr=addr, data=data)
            #self.memory.write_RAM_entry_data(num=1, offset=addr, data=data)

        elif(sel & SELECTOR.WORK.value):
            self.m_work = 1

            # *** WRITE WATCHPOINTS ***
            # if (self.cpu.m_wp_addr1 == addr):
            #     self.cpu.m_wp1 = 2
            #     self.cpu.m_wp_val1 = data

            self.memory.write_RAM_entry_data(num=0, offset=addr, data=data)

        elif(sel & SELECTOR.OBJCS.value):
            self.m_objcs = 1
            if addr >= 0x7c00 and addr < 0x8000: #in range (0x7c00, 0x8000):
                self.k051960_w(offset=addr-0x7c00, data=data)
            else:    
                self.k051937_w(offset=addr-0x7800, data=data)

        elif(sel & SELECTOR.VRAMCS.value):
            self.m_videocs = 1
            #if((addr-0x4000) < 0x3c00):
            if(addr-0x4000) in range(0x0,0x800) or (addr-0x4000) in range(0x2000,0x2800): self.m_vupdate = 1
            self.k052109_w(offset=addr-0x4000, data=data)                
        else:
             logging.error(f"### MEMORY MAPPER ERROR: UNKNOWN SELECTOR ### at PC:0x{self.cpu.m_pc.w.value:04x} Cycle:{self.cpu.m_tcount:010d}")

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
            self.memory.write_RAM_entry_data(num=1, offset=new_addr, data=data)
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
            self.memory.write_RAM_entry_data(num=4, offset=new_addr, data=data)

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
            return self.memory.read_RAM_entry_data(num=1, offset=new_addr)
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
            return self.memory.read_RAM_entry_data(num=4, offset=new_addr)

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
        return (self.memory.read_RAM_entry_data(num=1, offset=new_addr_up) << 8) + self.memory.read_RAM_entry_data(num=4, offset=new_addr_lo) 

    def k051937_w(self, offset: c_uint16, data: c_uint8) -> None:
        if (offset == 0):
            if(data&0x01):
                self.cpu.m_irq_line = False
            # elif(data&0x02):
            #     self.cpu.m_firq_line = False
            # elif(data&0x04):
            #     self.cpu.m_nmi_line = False                
            # elif(data&0x08):
            #     self.cpu.m_flip_screen = False 
            # elif(data&0x10):
            #     self.cpu.m_unknow1_line = True
            elif(data&0x20):
                #enable Sprite ROM read
                self.m_readroms = data & 0x20      
        elif(offset == 1):
            #checkered flag background palette dimming
            pass
        elif(offset >= 2 and offset < 5):
            self.m_spriterombank[offset - 2] = data    
        else:
            logging.error(f"### K051937 WRITE ERROR: UNKNOWN ADDRESS: 0x{offset:04x} DATA: 0x{data:02x} ### at PC:0x{self.cpu.m_pc.w.value:04x} Cycle:{self.cpu.m_tcount:010d}")

    def k051937_r(self, offset: c_uint16) -> c_uint8:
        if (offset == 0):
            #     return screen().vblank() ? 1 : 0; // vblank?
            # if self.m_k051937_vblank:
            #     return 1
            # else:
            #     return 0
            #logging.info(f'*** K051937 READ - VBLANK??? ***')
            return 0x0
        elif (self.m_readroms and offset >= 4 and offset < 8):
            #     return k051960_fetchromdata(offset & 3);
            logging.info(f'*** K051937 READ - FETCHROMDATA *** offset:{offset & 0x3}')
            return 0xff

        logging.error(f"### K051937 READ ERROR: UNKNOWN ADDRESS: 0x{offset:04x} ### at PC:0x{self.cpu.m_pc.w.value:04x} Cycle:{self.cpu.m_tcount:010d}")
        return 0x0

    def k052109_r(self, offset: c_uint16) -> c_uint8:
        if (not self.__RMRD):
            if ((offset & 0x1fff) >= 0x1800):
                if(offset >= 0x180c and offset < 0x1834):
                    #{   /* A y scroll */    }
                    pass
                elif (offset >= 0x1a00 and offset < 0x1c00):
                    #{   /* A x scroll */    }
                    pass
                elif (offset == 0x1d00):
                    #{   /* read for bitwise operations before writing */    }
                    pass
                elif (offset >= 0x380c and offset < 0x3834):
                    #{   /* B y scroll */    }
                    pass
                elif (offset >= 0x3a00 and offset < 0x3c00):
                    #{   /* B x scroll */    }
                    pass
                else:
                    logging.error(f"### K052109 READ ERROR: UNKNOWN ADDRESS: 0x{offset:04x} ### at PC:0x{self.cpu.m_pc.w.value:04x} Cycle:{self.cpu.m_tcount:010d}")
            return self.memory.read_RAM_entry_data(num=3, offset=offset)
        else:
            code = (offset & 0x1fff) >> 5
            color = self.m_romsubbank
            #flags = 0
            #priority = 0
            bank = self.m_k052109_charrombank[(color & 0x0c) >> 2] >> 2
            bank |= (self.m_k052109_charrombank2[(color & 0x0c) >> 2] >> 2)
            
            if self.m_has_extra_video_ram:
                code |= color << 8
            else:
                code |= ((color & 0x3f) << 8) | (bank << 14)
                color = ((color & 0xc0) >> 6)
            
            addr = (code << 5) + (offset & 0x1f)
            addr &= self.memory.rom_map[EPROM_Type.TILE].size - 1 #0x17ffff #1.5 Mbytes Aliens Tile ROM size
            offset2 = (addr & 0x3)<<3
            mask2 = 0xff
            logging.info(f'*** K052109 READ - FETCHROMDATA *** offset:{offset & 0x3}')
            return (self.memory.rom_map[EPROM_Type.TILE].rom_data[addr >>2] & (mask2 << offset2)) >> offset2

    def k052109_w(self, offset: c_uint16, data: c_uint8) -> None:
        if((offset & 0x1fff) < 0x1800): #tilemap RAM
            if (offset >= 0x4000):
                self.m_has_extra_video_ram = 1
            self.memory.write_RAM_entry_data(num=3, offset=offset, data=data)
        else: #Control registers
            self.memory.write_RAM_entry_data(num=3, offset=offset, data=data)
            # if(offset == 0x1c00):
            #     #??? unknow
            #     logging.warn('*** K052109 WRITE - PORT 0X1C00 ??? ***')
            if (offset >= 0x180c and offset < 0x1834):
                #/* A y scroll */
                pass
            elif (offset >= 0x1a00 and offset < 0x1c00):
                #/* A x scroll */
                pass
            elif (offset == 0x1c80):
                if (self.m_scrollctrl != data):
                    self.m_scrollctrl = data
            elif (offset == 0x1d00):
                if bool(data & 0x04):
                    self.m_irq_enabled = True
                if (not self.m_irq_enabled):
                    #m_irq_handler(CLEAR_LINE);
                    self.cpu.m_irq_line = False
            elif (offset == 0x1d80): # or offset == 0x3d80):
                self.m_k052109_charrombank[0] = data & 0x0f
                self.m_k052109_charrombank[1] = (data>>4) & 0x0f
            elif (offset == 0x1e00 or offset == 0x3e00):
                self.m_romsubbank = data
            elif (offset == 0x1e80):
                if self.m_k052109_tileflip_en != ((data & 0x06) >> 1):
                    self.m_k052109_tileflip_en = ((data & 0x06) >> 1)
            elif(offset == 0x1f00): # or offset == 0x3f00):
                self.m_k052109_charrombank[2] = data & 0x0f
                self.m_k052109_charrombank[3] = (data>>4) & 0x0f
            elif (offset >= 0x380c and offset < 0x3834):
                #{   /* B y scroll */    }
                pass
            elif (offset >= 0x3a00 and offset < 0x3c00):
                #{   /* B x scroll */    }
                pass                
            elif (offset == 0x3d80): #// Surprise Attack uses offset 0x3d80 in rom test
                #// mirroring this write, breaks Surprise Attack in game tilemaps
                self.m_k052109_charrombank2[0] = data & 0x0f
                self.m_k052109_charrombank2[1] = (data >> 4) & 0x0f
            elif (offset == 0x3f00): #// Surprise Attack uses offset 0x3f00 in rom test
                #// mirroring this write, breaks Surprise Attack in game tilemaps
                self.m_k052109_charrombank2[2] = data & 0x0f
                self.m_k052109_charrombank2[3] = (data >> 4) & 0x0f
            #else:
                #control registers
                #m_ram[offset] = data;
                # print(f">>>k052109_w {offset+0x4000:04X}:{data:02X}")
                #self.memory.write_RAM_entry_data(num=3, offset=offset, data=data)
                #logging.error(f"### K052109 WRITE ERROR: UNKNOWN ADDRESS: 0x{offset:04x} DATA: 0x{data:02x} ### at PC:0x{self.cpu.m_pc.w.value:04x} Cycle:{self.cpu.m_tcount:010d}")

    def k051960_w(self, offset: c_uint16, data: c_uint8) -> None:
        self.memory.write_RAM_entry_data(num=2, offset=offset, data=data) #write to Sprite RAM

    def k051960_r(self, offset: c_uint16) -> c_uint8:
        return self.memory.read_RAM_entry_data(num=2, offset=offset) #read from Sprite RAM

    def count_r(self) -> c_uint8:
        return 0x00

    def count_w(self, data: c_uint8) -> None:
        #bits 0,1 writes to 051550 OUT1, OUT2, associated to coin counters
	    #/* Count it only if the data has changed from 0 to non-zero */
        if(bool(data & 0x01) and (self.__last_coin1 == 0)):
            self.__coin_counter1+=1
            self.__last_coin1 = data & 0x01

        if(bool(data & 0x02) and (self.__last_coin2 == 0)):
            self.__coin_counter2+=1
            self.__last_coin2 = data & 0x02

        #bit 5 -> WOCO (selects WORK RAM or CRAM)
        self.__WOCO = bool((data & 0x20) >> 5)
        self.m_cram = (data & 0x20) >> 5
  
        #bit 6 -> RMRD (enable char ROM read through VIDEO RAM)
        if(bool(data & 0x40)):
            self.__RMRD = True
            self.m_rmrd = 1
        else:
            self.__RMRD = False
            self.m_rmrd = 0

        #bit 7 -> INIT        
        if(bool(data & 0x80)):
            self.__INIT = True
            self.m_init = 1
        else:
            self.__INIT = False
            self.m_init = 0

#     print(f"Selector: {s.name} = {1 if(s.value & sel) else 0}")

    def decoder(self, ADDR: c_uint16, CLKQ_risedge_tick:bool=True) -> c_uint16:
        sel:c_uint16 = SELECTOR.NONE.value

        #D21_12
        if(ADDR in range(0x0, 0x3FF+1) and self.__WOCO):
            sel |=  SELECTOR.D21_12.value

        if((ADDR in range(0x8000, 0xFFFF+1) and not(self.__AS)) or (ADDR in range(0x2000, 0x3FFF+1) and not(self.__AS) and self.__BK4)):
            sel |= SELECTOR.PROG.value            

        if(not(self.__AS) and (ADDR in range(0X400, 0X1FFF+1) 
                        #or ADDR in range(0x0800, 0x0FFF+1) 
                        #or ADDR in range(0x1000, 0x1FFF+1)
                        or (ADDR in range(0X0, 0X3FF+1) and not(self.__WOCO)) )):
            sel |= SELECTOR.WORK.value

        if(not(self.__AS) and not(self.__BK4) and ADDR in range(0x2000, 0x3FFF+1)):
            sel |= SELECTOR.BANK.value

        #D21_15
        if(not(self.__AS) and ADDR in range(0x5C00, 0x5FFF+1)):
            sel |= SELECTOR.D21_15.value
        
        #D21_16
        if(self.__INIT and ADDR in range(0x7800, 0x7FFF+1)):
            sel |= SELECTOR.D21_16.value

        #D21_17
        if(not(self.__AS) and (  (ADDR in range(0x0, 0x3FF+1) and self.__WOCO) or ADDR in range(0x4000, 0x7FFF+1))):
            sel |=  SELECTOR.D21_17.value

        #D18_5 value is a delayed value of D21_17 until get CLKQ rising edge, if AS is true is preset with False value
        self.d18_5_val = bool(sel & SELECTOR.D21_17.value) #if(CLKQ_risedge_tick) else (self.d18_5_val if(not(self.__AS)) else False)

        if((sel & SELECTOR.PROG.value) or (sel & SELECTOR.WORK.value) or (sel & SELECTOR.BANK.value)):
            sel |=SELECTOR.D21_19.value

        #R14, IOCS
        if((sel & SELECTOR.D21_15.value) and ADDR in range(0x5F80, 0x5F9F+1)):
            sel |= SELECTOR.R14.value
            sel |= SELECTOR.IOCS.value

        if((sel & SELECTOR.IOCS.value)):
            #CONTROL1 (DSW3, P1, P2, DSW1)
            #if(ADDR in range(0x5F80,0x5F83+1)): 
            #sel|=SELECTOR.CONTROL1.value
            if(ADDR == 0x5F80): sel|=SELECTOR.DSW3.value
            if(ADDR == 0x5F81): sel|=SELECTOR.P1.value
            if(ADDR == 0x5F82): sel|=SELECTOR.P2.value
            if(ADDR == 0x5F83): sel|=SELECTOR.DSW1.value

            #CONTROL2 (DSW2)
            if(ADDR in range(0x5F84,0x5F87+1)): 
                #sel|=SELECTOR.CONTROL2.value
                sel|=SELECTOR.DSW2.value              

            #COUNT
            if(ADDR in range(0x5F88,0x5F8B+1)): 
                sel|=SELECTOR.COUNT.value

            #SOUND
            if(ADDR in range(0x5F8C,0x5F8F+1)): 
                sel|=SELECTOR.SOUND.value

        if(not(self.__RMRD) and (sel & SELECTOR.D21_16.value) and self.d18_5_val and ((ADDR in range(0x7800, 0x7807+1)) or (ADDR in range(0x7C00, 0x7FFF+1)))):
            sel |= SELECTOR.R15.value 

        #CRAMCS
        if(self.d18_5_val and (sel & SELECTOR.D21_12.value)):
            sel |= SELECTOR.CRAMCS.value

        #D20_12
        if((self.d18_5_val and not(self.__RMRD) and (sel & SELECTOR.D21_16.value) and ADDR in range(0x7800, 0x7807+1)) or
           (self.d18_5_val and not(self.__RMRD) and ADDR in range(0x7C00, 0x7FFF+1)) or
           (self.d18_5_val and (sel & SELECTOR.D21_17.value) and not(sel & SELECTOR.R14.value) and not(sel & SELECTOR.R15.value))):
            sel |=SELECTOR.D20_12.value

        if(((sel & SELECTOR.D21_16.value) and self.d18_5_val and not(self.__RMRD) and ADDR in range(0x7800, 0x7807+1)) or
           (self.d18_5_val and not(self.__RMRD) and (sel & SELECTOR.D21_16.value) and ADDR in range(0x7C00, 0x7FFF+1))):
        #if not(self.__RMRD) and (ADDR in range(0x7C00, 0x7FFF+1) or ADDR in range(0x7800, 0x7807+1)):
            #logging.info('<<< OBJCS SELECTOR >>>')
            sel |= SELECTOR.OBJCS.value

        if(self.d18_5_val and (sel & SELECTOR.D21_17.value) and not(sel & SELECTOR.D21_12.value) and not(sel & SELECTOR.R14.value) and not(sel & SELECTOR.R15.value)):
            sel |= SELECTOR.VRAMCS.value

        return sel

    def printsel(self, ADDR: c_uint16, CLKQ_risedge_tick:bool) -> None:
        sel = self.decoder(ADDR=ADDR, CLKQ_risedge_tick=CLKQ_risedge_tick)
        print(f"-----------------------------")
        print(f"Address:{ADDR:04X} AS:{'T' if(self.__AS) else 'F'} BK4:{'T' if(self.__BK4) else 'F'} INIT:{'T' if(self.__INIT) else 'F'} WOCO:{'T' if(self.__WOCO) else 'F'} RMRD:{'T' if(self.__RMRD) else 'F'} CLKQris:{'T' if(CLKQ_risedge_tick) else 'F'}")
        print(f"Selector:{((sel & 0xf00000)>>20):04b} {((sel & 0xf0000)>>16):04b} {((sel & 0xf000)>>12):04b} {(sel & 0x0f00)>>8:04b} {(sel & 0xf0)>>4:04b} {(sel & 0xf):04b}")
        print(f"         {((sel & 0xf00000)>>20):01x}    {((sel & 0xf0000)>>16):01x}    {((sel & 0xf000)>>12):01x}    {(sel & 0x0f00)>>8:01x}    {(sel & 0xf0)>>4:01x}    {(sel & 0xf):01x}")
        for s in SELECTOR:
            print(f"{s.name+' ' if((s.value & sel) and (s.value < 0x4000)) else ''}", end='')
        print()


#(ADDR: c_uint16, AS:bool, BK4:bool, INIT:bool, WOCO:bool, RMRD:bool, CLKQ_risedge_tick:bool)                                          
# mm = memory_mapper()

# addr = 0xffff
# as_signal = False
# init = True
# clkqre= True
# bk4=True
# rmrd=False
# woco=False

# sel = mm.decoder(ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)
# print(f"Address {addr:04X}")
# print(f"{sel:04X}")
# for s in SELECTOR:
#     print(f"Selector: {s.name} = {1 if(s.value & sel) else 0}")

# addr = 0x03FA; as_signal = False; init = True; clkqre= True; bk4=True; rmrd=False; woco=True
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x03FA; as_signal = False; init = True; clkqre= True; bk4=True; rmrd=False; woco=False
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x2001; as_signal = False; init = True; clkqre= True; bk4=True; rmrd=False; woco=False
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x2001; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=False
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x1FFF; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=False
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x1FFF; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=True
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x5F84; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=True
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x5A00; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=True
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x7800; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=True
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x7808; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=True
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)

# addr = 0x7C60; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=False
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)
# addr = 0x7800; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=False; woco=False
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)
# addr = 0x7808; as_signal = False; init = True; clkqre= True; bk4=False; rmrd=True; woco=False
# mm.printsel(DATA=0x00, ADDR=addr, AS=as_signal, BK4=bk4, INIT=init, WOCO=woco, RMRD=rmrd, CLKQ_risedge_tick=clkqre)