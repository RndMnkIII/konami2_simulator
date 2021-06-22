#konami2.py
#from konami2 import konami2_cpu_device
from array import array
from typing import NamedTuple, List, TypeVar, Type, Sequence
from enum import Enum
from ctypes import addressof, sizeof, byref, pointer, Union, Structure, c_int, c_ulong, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32
import sys

if (sys.byteorder == 'little'):
    from  m6809_regs_lite import Tuint8, Tint8, Tuint16, Tint16, Tuint32, Tint32, PAIR, PAIR16, M6809Q
else:
    from  m6809_regs_big import Tuint8, Tint8, Tuint16, Tint16, Tuint32, Tint32, PAIR, PAIR16, M6809Q
    #assert False, "No es sistema BigEndian"

from m6809 import m6809_base_device
from m6809_types import ADRMOD, exgtfr_register, FLAGS, CPUVECT, LINEDEF, line_state, IRQLINE
from konami2_types import KIRQLINE
from eproms import EPROM_Type, EPROM_entry, Konami2eproms
import konami2_opcodes as k2op
from konami2_disassembler import OpcodesData, Konami2Disassembler
from konami2_exec import Konami2StateMachine


import logging
from datetime import datetime
from io import StringIO

from timeit import default_timer as timer

from m6809_execi import device_execute_interface, device_input
# class MyParentClass():
# def __init__(self, x, y):
# pass

# class SubClass(MyParentClass):
# def __init__(self, x, y):
# super().__init__(x, y)

#def __init__(self, clock: int) -> None:
logging.basicConfig(filename='konami2_5.log',level=logging.INFO)

class konami2_cpu_device (Konami2StateMachine, m6809_base_device):
#class konami2_cpu_device (m6809_base_device):    
    T = TypeVar('T',Tuint8, Tuint16, Tuint32, Tint8, Tint16, Tint32)

    def __init__(self, clock: int) -> None:
        super().__init__(clock)
        from memory_mapper import SELECTOR, memory_mapper
        self.m_mapper: memory_mapper = None #for setlines() callback
        self.m_memory: Konami2eproms = None #for setlines() callback setbank entry
        self.m_bank:c_uint8
        self.rti_exec:bool
        self.rts_exec:bool
        self.subr_called:bool
        self.m_jmp_called:bool
        self.lst_pc:c_uint16
        self.lst_pc2:c_uint16

        #for use as watchpoints at memory_mapper.py
        self.m_wp_addr1:c_uint16
        self.m_wp1: c_uint8
        self.m_wp_val1: c_uint8
        self.m_wp_addr2:c_uint16
        self.m_wp2: c_uint8
        self.m_wp_val2: c_uint8
        self.m_wp_addr3:c_uint16
        self.m_wp3:  c_uint8
        self.m_wp_val3: c_uint8

        #dict for store instructions coverage
        self.m_kon2_inst_cover = {}

        #dict for instruction table
        self.m_inst_tbl =  {0x08: self.func_08, 0x09: self.func_09, 0x0a: self.func_0a, 0x0b: self.func_0b, 0x0c: self.func_0c, 0x0d: self.func_0d, 0x0e: self.func_0e, 0x0f: self.func_0f, 
                            0x10: self.func_10, 0x11: self.func_11, 0x12: self.func_12, 0x13: self.func_13, 0x14: self.func_14, 0x15: self.func_15, 0x16: self.func_16, 0x17: self.func_17, 0x18: self.func_18, 0x19: self.func_19, 0x1a: self.func_1a, 0x1b: self.func_1b, 0x1c: self.func_1c, 0x1d: self.func_1d, 0x1e: self.func_1e, 0x1f: self.func_1f, 
                            0x20: self.func_20, 0x21: self.func_21, 0x22: self.func_22, 0x23: self.func_23, 0x24: self.func_24, 0x25: self.func_25, 0x26: self.func_26, 0x27: self.func_27, 0x28: self.func_28, 0x29: self.func_29, 0x2a: self.func_2a, 0x2b: self.func_2b, 0x2c: self.func_2c, 0x2d: self.func_2d, 0x2e: self.func_2e, 0x2f: self.func_2f, 
                            0x30: self.func_30, 0x31: self.func_31, 0x32: self.func_32, 0x33: self.func_33, 0x34: self.func_34, 0x35: self.func_35, 0x36: self.func_36, 0x37: self.func_37, 0x38: self.func_38, 0x39: self.func_39, 0x3a: self.func_3a, 0x3b: self.func_3b, 0x3c: self.func_3c, 0x3d: self.func_3d, 0x3e: self.func_3e, 0x3f: self.func_3f, 
                            0x40: self.func_40, 0x41: self.func_41, 0x42: self.func_42, 0x43: self.func_43, 0x44: self.func_44, 0x45: self.func_45, 0x46: self.func_46, 0x47: self.func_47, 0x48: self.func_48, 0x49: self.func_49, 0x4a: self.func_4a, 0x4b: self.func_4b, 0x4c: self.func_4c, 0x4d: self.func_4d, 0x4e: self.func_4e, 0x4f: self.func_4f, 
                            0x50: self.func_50, 0x51: self.func_51, 0x52: self.func_52, 0x53: self.func_53, 0x54: self.func_54, 0x55: self.func_55, 0x56: self.func_56, 0x57: self.func_57, 0x58: self.func_58, 0x59: self.func_59, 0x5a: self.func_5a, 0x5b: self.func_5b, 0x5c: self.func_5c, 
                            0x60: self.func_60, 0x61: self.func_61, 0x62: self.func_62, 0x63: self.func_63, 0x64: self.func_64, 0x65: self.func_65, 0x66: self.func_66, 0x67: self.func_67, 0x68: self.func_68, 0x69: self.func_69, 0x6a: self.func_6a, 0x6b: self.func_6b, 0x6c: self.func_6c, 0x6d: self.func_6d, 0x6e: self.func_6e, 0x6f: self.func_6f, 
                            0x70: self.func_70, 0x71: self.func_71, 0x72: self.func_72, 0x73: self.func_73, 0x74: self.func_74, 0x75: self.func_75, 0x76: self.func_76, 0x77: self.func_77, 0x78: self.func_78, 0x79: self.func_79, 0x7a: self.func_7a, 0x7b: self.func_7b, 0x7c: self.func_7c, 0x7d: self.func_7d, 0x7e: self.func_7e, 0x7f: self.func_7f, 
                            0x80: self.func_80, 0x81: self.func_81, 0x82: self.func_82, 0x83: self.func_83, 0x84: self.func_84, 0x85: self.func_85, 0x86: self.func_86, 0x87: self.func_87, 0x88: self.func_88, 0x89: self.func_89, 0x8a: self.func_8a, 0x8b: self.func_8b, 0x8c: self.func_8c, 0x8d: self.func_8d, 0x8e: self.func_8e, 0x8f: self.func_8f, 
                            0x90: self.func_90, 0x91: self.func_91, 0x92: self.func_92, 0x93: self.func_93, 0x94: self.func_94, 0x95: self.func_95, 0x96: self.func_96, 0x97: self.func_97, 0x98: self.func_98, 0x99: self.func_99, 0x9a: self.func_9a, 0x9b: self.func_9b, 0x9c: self.func_9c, 0x9d: self.func_9d, 0x9e: self.func_9e, 0x9f: self.func_9f, 
                            0xa0: self.func_a0, 0xa1: self.func_a1, 0xa2: self.func_a2, 0xa3: self.func_a3, 0xa4: self.func_a4, 0xa5: self.func_a5, 0xa6: self.func_a6, 0xa7: self.func_a7, 0xa8: self.func_a8, 0xa9: self.func_a9, 0xaa: self.func_aa, 0xab: self.func_ab, 0xac: self.func_ac, 0xad: self.func_ad, 0xae: self.func_ae, 
                            0xb0: self.func_b0, 0xb1: self.func_b1, 0xb2: self.func_b2, 0xb3: self.func_b3, 0xb4: self.func_b4, 0xb5: self.func_b5, 0xb6: self.func_b6, 0xb7: self.func_b7, 0xb8: self.func_b8, 0xb9: self.func_b9, 0xba: self.func_ba, 0xbb: self.func_bb, 0xbc: self.func_bc, 0xbd: self.func_bd, 0xbe: self.func_be, 0xbf: self.func_bf, 
                            0xc0: self.func_c0, 0xc1: self.func_c1, 0xc2: self.func_c2, 0xc3: self.func_c3, 0xc4: self.func_c4, 0xc5: self.func_c5, 0xc6: self.func_c6, 0xc7: self.func_c7, 0xc8: self.func_c8, 0xc9: self.func_c9, 0xca: self.func_ca, 0xcb: self.func_cb, 0xcc: self.func_cc, 0xcd: self.func_cd, 0xce: self.func_ce, 0xcf: self.func_cf, 
                            0xd0: self.func_d0}
        # m_set_lines(*this)

    def set_mapper(self, mapper) -> None:
        self.m_mapper = mapper

    def set_memory(self, memory: Konami2eproms) -> None:
        self.m_memory = memory

    #configuration
	#auto line() { return m_set_lines.bind(); }
    def line(self) -> None:
        #m_set_lines.bind()
        #used to bank switch BANK ROM
        #aliens.cpp -> m_rombank->set_entry(data & 0x1f);
        pass

	#incidentals
	#devcb_write8 m_set_lines;

    def device_start(self) -> None:
        super().device_start()
        # print("$$$ CALLED KONAMI-2 INHERITED CLASS $$$")
        # // resolve callbacks
	    # m_set_lines.resolve();
        self.m_bank=0
        self.rti_exec=False
        self.rts_exec=False
        self.subr_called=False
        self.m_jmp_called=False
        self.lst_pc=0x0000
        self.lst_pc2=0X0000

        #for use as watchpoints at memory_mapper.py
        self.m_wp_addr1=0xffff
        self.m_wp1=0 #0 No access, 1 Read, 2 Write
        self.m_wp_val1=0 #value used for read/write from/to memory address
        self.m_wp_addr2=0xffff
        self.m_wp2=0 #0 No access, 1 Read, 2 Write
        self.m_wp_val2=0 #value used for read/write from/to memory address
        self.m_wp_addr3=0xffff
        self.m_wp3=0 #0 No access, 1 Read, 2 Write
        self.m_wp_val3=0 #value used for read/write from/to memory address

    def device_reset(self) -> None:
        super().device_reset()
        self.m_bank=0
        self.rti_exec=False
        self.rts_exec=False
        self.subr_called=False
        self.lst_pc=0X0000
        self.lst_pc2=0X0000

        #for use as watchpoints at memory_mapper.py
        self.m_wp_addr1=0xffff
        self.m_wp1=0 #0 No access, 1 Read, 2 Write
        self.m_wp_val1=0 #value used for read/write from/to memory address
        self.m_wp_addr2=0xffff
        self.m_wp2=0 #0 No access, 1 Read, 2 Write
        self.m_wp_val2=0 #value used for read/write from/to memory address
        self.m_wp_addr3=0xffff
        self.m_wp3=0 #0 No access, 1 Read, 2 Write
        self.m_wp_val3=0 #value used for read/write from/to memory address

        self.m_kon2_inst_cover = {}

    def create_disassembler(self) -> Konami2Disassembler:
        return Konami2Disassembler()

    def read_operand2(self) -> c_uint8:
        return super().read_operand2()

    def read_operand(self, ordinal: c_int16) -> c_uint8:
        if(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_EA.value):
            return self.read_memory(self.m_ea.w.value + ordinal)
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_IMMEDIATE.value):
            return self.read_opcode_arg()
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_REGISTER_D.value):
            return self.m_q.r.r8.b.value if (ordinal & 0x0001) else self.m_q.r.r8.a.value
        else:
            logging.critical(f"Konami2_read_operand(ordinal): Unexpected PC: {self.m_pc.w.value:04X}Addr.M: {self.m_addressing_mode:02x} - {datetime.now()}")
            return 0x00

    def write_operand2(self, data: c_uint8) -> None:
        super().write_operand2(data)

    def write_operand(self, ordinal: c_int16, data: c_uint8) -> None:
        if(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_EA.value):
            self.write_memory(self.m_ea.w.value + ordinal, data)
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_IMMEDIATE.value):
            pass
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_REGISTER_D.value):
            if(ordinal & 0x00001):
                self.m_q.r.r8.b.value = data
            else:
                self.m_q.r.r8.a.value = data
        else:
            logging.critical("Konami2_write_operand(ordinal,data): Unexpected addressing mode:{02x} at:0x{04x}- {}".format(self.m_addressing_mode, self.m_pc.value, datetime.now()))

    def ireg(self) -> Tuint16:
        if((self.m_opcode & 0x70) == 0x20):
            return self.m_x.w
        elif((self.m_opcode & 0x70) == 0x30):
            return self.m_y.w
        elif((self.m_opcode & 0x70) == 0x50):
            return self.m_u.w
        elif((self.m_opcode & 0x70) == 0x30):
            return self.m_s.w
        elif((self.m_opcode & 0x70) == 0x70):
            return self.m_pc.w
        else:
            logging.critical("Konami2_ireg(): Should not get here m_opcode:{02x} at:0x{04x}- {}".format(self.m_opcode, self.m_pc.value, datetime.now()))

    # //-------------------------------------------------
    # //  read_exgtfr_register
    # //-------------------------------------------------
    def read_exgtfr_register(self, reg: c_uint8) -> exgtfr_register:
        result = exgtfr_register()
        result.word_value.value = 0x00FF
        #print("KONAMI2: read_exgtfr_register")

        if  ((reg & 0x07) == 0X0): result.word_value.value = self.m_q.r.r8.a.value  #A
        elif((reg & 0x07) == 0X1): result.word_value.value = self.m_q.r.r8.b.value  #B
        elif((reg & 0x07) == 0X2): result.word_value.value = self.m_x.w.value  #X
        elif((reg & 0x07) == 0X3): result.word_value.value = self.m_y.w.value  #Y
        elif((reg & 0x07) == 0X4): result.word_value.value = self.m_s.w.value  #S
        elif((reg & 0x07) == 0X5): result.word_value.value = self.m_u.w.value  #U
        else:
            logging.critical("Konami2_read_exgtfr_register(): Should not get here: reg:0x{02x} at:0x{04x}- {}".format(reg, self.m_pc.value, datetime.now()))
        result.byte_value.value = (result.word_value.value & 0xFF)
        return result

    # //-------------------------------------------------
    # //  write_exgtfr_register
    # //-------------------------------------------------
    def write_exgtfr_register(self, reg: c_uint8, value: exgtfr_register) -> None:
        #print("KONAMI2: write_exgtfr_register")
        if  ((reg & 0x07) == 0X0): self.m_q.r.r8.a.value = value.byte_value.value  #A
        elif((reg & 0x07) == 0X1): self.m_q.r.r8.b.value = value.byte_value.value  #B
        elif((reg & 0x07) == 0X2): self.m_x.w.value = value.word_value.value  #X
        elif((reg & 0x07) == 0X3): self.m_y.w.value = value.word_value.value  #Y
        elif((reg & 0x07) == 0X4): self.m_s.w.value = value.word_value.value  #S
        elif((reg & 0x07) == 0X5): self.m_u.w.value = value.word_value.value  #U
        else:
            logging.critical("Konami2_write_exgtfr_register(): Should not get here: reg {02x} at:0x{04x}- {}".format(reg, self.m_pc.value, datetime.now()))
    # //-------------------------------------------------
    # //  safe_shift_right
    # //-------------------------------------------------
    def safe_shift_right(self, value: T, shift: c_uint32) -> T:
        param_class = type(value)
        result = param_class()

        if(shift < (sizeof(result)*8)):
            result.value = value.value >> shift
        elif(value.value < 0):
            result.value = -1
        else:
            result.value = 0

        return result

    # //-------------------------------------------------
    # //  safe_shift_right_unsigned
    # //-------------------------------------------------
    def safe_shift_right_unsigned(self, value: T, shift: c_uint32) -> T:
        param_class = type(value)
        result = param_class()

        if(shift < (sizeof(value)*8)):
            result.value = value.value >> shift
        else:
            result.value = 0

        return result

    # //-------------------------------------------------
    # //  safe_shift_left
    # //-------------------------------------------------
    def safe_shift_left(self, value: T, shift: c_uint32) -> T:
        param_class = type(value)
        result = param_class()

        if(shift < (sizeof(value)*8)):
            result.value = value.value << shift
        else:
            result.value = 0

        return result

    # //-------------------------------------------------
    # //  lmul
    # //-------------------------------------------------
    def lmul(self) -> None:
        result = PAIR()

        #Do the multiply
        result.d.value = self.m_x.w.value * self.m_y.w.value

        #Set the result registers
        self.m_x.w.value = result.w.h.value
        self.m_y.w.value = result.w.l.value

        #set Z flag
        self.set_flags(FLAGS.CC_Z.value, result.d)

        #set C flag
        if (result.d.value & 0x8000):
            self.m_cc |= FLAGS.CC_C.value
        else:
            self.m_cc &= (FLAGS.CC_C.value ^ 0xFF) #m_cc &= ~CC_C;

    # //-------------------------------------------------
    # //  divx
    # //-------------------------------------------------
    def divx(self) -> None:
        result = Tuint16()
        remainder = Tuint8()

        if(self.m_q.r.r8.b.value != 0):
            result.value = self.m_x.w.value // self.m_q.r.r8.b.value #Floor division returns int value
            remainder.value = self.m_x.w.value % self.m_q.r.r8.b.value
        else:
            #divide by zero: ??? TEST ON REAL HARDWARE AND SEE
            result.value = 0
            remainder.value = 0

        #set results and Z flag
        self.m_x.w.value = self.set_flags(FLAGS.CC_Z.value, result).value
        self.m_q.r.r8.b.value = remainder.value

        #set C flag
        if (result.value & 0x0080):
            self.m_cc |= FLAGS.CC_C.value
        else:
            self.m_cc &= (FLAGS.CC_C.value ^ 0xFF) #m_cc &= ~CC_C;

    # //-------------------------------------------------
    # //  set_lines
    # //-------------------------------------------------
    def set_lines(self, data: c_uint8) -> None:
        #	if (!m_set_lines.isnull()) m_set_lines((offs_t)0, data);
        self.m_bank = 0x1f & data
        self.m_memory.set_rombank(numentry=self.m_bank)
        self.m_mapper.set_BK4(bool(0x10 & data))

    # //-------------------------------------------------
    # //  execute_one - try to execute a single instruction
    # //-------------------------------------------------
    # call the method execute_one() from mixing inherited class Konami2StateMachine

    # ------- FROM HERE CUT AND PASTE IN konami2_exec.yp ----------
    def MAIN(self) -> None:
        # print ('Exec label .MAIN')
        self.lst_pc2 = self.m_pc.w.value

        pending_int:c_uint16 = self.get_pending_interrupt()
        if(pending_int == CPUVECT.VECTOR_NMI.value):
            self.NMI()
            return
        elif(pending_int == CPUVECT.VECTOR_FIRQ.value):
            self.FIRQ()
            return
        elif(pending_int == CPUVECT.VECTOR_IRQ.value):
            self.IRQ()
            return

        #debugger hook
        self.m_ppc = self.m_pc

        #opcode fetch
        self.m_opcode = self.read_opcode()

        #check instruction coverage
        # if self.m_opcode not in self.m_kon2_inst_cover:
        #     self.m_kon2_inst_cover[self.m_opcode] = 1
        # else:
        #     self.m_kon2_inst_cover[self.m_opcode] += 1

        #self.state_1()
        self.m_inst_tbl[self.m_opcode]()

    def NMI(self) -> None:
        self.m_nmi_asserted = False
        self.m_cc |= FLAGS.CC_E.value
        self.set_regop16(self.m_s)
        self.m_temp.w.value = self.entire_state_registers()
        self.push_state(49)
        self.PUSH_REGISTERS()

    def state_49(self) -> None:
        self.m_cc |= FLAGS.CC_I.value | FLAGS.CC_F.value
        self.set_ea(CPUVECT.VECTOR_NMI.value)
        self.eat(1)
        #standard_irq_callback(INPUT_LINE_NMI);
        self.INTERRUPT_VECTOR()

    def FIRQ(self) -> None:
        if(self.firq_saves_entire_state()):
            self.m_cc |= FLAGS.CC_E.value
            self.m_temp.w.value = self.entire_state_registers()
        else:
            self.m_cc &= (FLAGS.CC_E.value ^ 0xFF)
            self.m_temp.w.value = self.partial_state_registers()

        self.set_regop16(self.m_s)
        self.push_state(50)
        self.PUSH_REGISTERS()

    def state_50(self) -> None:
        self.m_cc |= (FLAGS.CC_I.value | FLAGS.CC_F.value)
        self.set_ea(CPUVECT.VECTOR_FIRQ.value)
        self.eat(1)
        #standard_irq_callback(IRQLINE.M6809_FIRQ_LINE)
        self.INTERRUPT_VECTOR()

    def IRQ(self) -> None:
        self.m_cc |= FLAGS.CC_E.value
        self.set_regop16(self.m_s)
        self.m_temp.w.value = self.entire_state_registers()
        self.push_state(51)
        self.PUSH_REGISTERS()

    def state_51(self) -> None:
        self.m_cc |= FLAGS.CC_I.value
        self.set_ea(CPUVECT.VECTOR_IRQ.value)
        self.eat(1)
        #standard_irq_callback(IRQLINE.M6809_IRQ_LINE)
        self.INTERRUPT_VECTOR()

    def INTERRUPT_VECTOR(self) -> None:
        self.eat(4)
        self.m_pc.b.h.value = self.read_operand(0)
        self.m_pc.b.l.value = self.read_operand(1)

    def INDEXED(self) -> None:
        #print ("\tINDEXED:")

        self.m_opcode = self.read_opcode_arg()

        sw_value:c_uint8 = self.m_opcode & 0xF7

        if( sw_value == 0x07):
            #extended addressing mode
            self.m_temp.b.h.value = self.read_opcode_arg()
            self.m_temp.b.l.value = self.read_opcode_arg()
            #BREAK

        elif(sw_value in (0x20, 0x30, 0x50, 0x60, 0x70)):
            #auto increment
            self.m_temp.w = self.ireg()
            self.ireg().value += 1
            self.eat(2)
            #BREAK

        elif(sw_value in (0x21, 0x31, 0x51, 0x61, 0x71)):
            #double auto increment
            self.m_temp.w = self.ireg()
            self.ireg().value += 2
            self.eat(3)
            #BREAK

        elif(sw_value in (0x22, 0x32, 0x52, 0x62, 0x72)):
            #auto decrement
            self.m_temp.w = self.ireg()
            self.ireg().value -= 1
            self.eat(2)
            #BREAK

        elif(sw_value in (0x23, 0x33, 0x53, 0x63, 0x73)):
            #double auto decrement
            self.m_temp.w = self.ireg()
            self.ireg().value -= 2
            self.eat(3)
            #BREAK

        elif(sw_value in (0x24, 0x34, 0x54, 0x64, 0x74)):
            #postbyte offset
            self.m_ea.w = self.ireg() #need t do this now because ireg() might be PC
            self.m_temp.b.l.value = self.read_opcode_arg()

            #m_temp.w = m_ea.w + (int8_t) m_temp.b.l;
            self.m_temp.w.value = self.m_ea.w.value + self.m_temp.sb.l.value

            self.eat(1)
            #BREAK

        elif(sw_value in (0x25, 0x35, 0x55, 0x65, 0x75)):
            #postword offset
            self.m_ea.w = self.ireg() #need t do this now because ireg() might be PC
            self.m_temp.b.h.value = self.read_opcode_arg()
            self.m_temp.b.l.value = self.read_opcode_arg()

            #m_temp.w = m_ea.w + (int16_t) m_temp.w;
            self.m_temp.w.value = self.m_ea.w.value + self.m_temp.sw.value

            self.eat(2)
            #BREAK

        elif(sw_value in (0x26, 0x36, 0x56, 0x66, 0x76)):
            #postword offset
            self.m_temp.w = self.ireg()
            #BREAK

        elif(sw_value == 0xC4):
            #direct addressing mode
            self.m_temp.b.h.value = self.m_dp.value
            self.m_temp.b.l.value = self.read_opcode_arg()
            #BREAK

        elif(sw_value in (0xA0, 0xB0, 0xD0, 0xE0, 0xF0)):
            #relative to register A
            self.m_temp.w.value = self.ireg().value + self.m_q.r.sr8.a.value
            self.eat(1)
            #BREAK

        elif(sw_value in (0xA1, 0xB1, 0xD1, 0xE1, 0xF1)):
            #relative to register B
            self.m_temp.w.value = self.ireg().value + self.m_q.r.sr8.b.value #SIGNED VALUE
            self.eat(1)
            #BREAK

        elif(sw_value in (0xA7, 0xB7, 0xD7, 0xE7, 0xF7)):
            #relative to register D
            self.m_temp.w.value = self.ireg().value + self.m_q.r.sr16.d.value
            self.eat(4)
            #BREAK

        else:
            logging.error("KONAMI2 execute_one():Unknown/Invalid postbyte at PC: {:04X}: {:02X}- {}".format(self.m_pc.w.value - 1, sw_value, datetime.now()))
            self.m_temp.w.value = 0
            #BREAK

        if(self.m_opcode  & 0x08):
            #indirect mode
            self.set_ea(self.m_temp.w.value)
            self.m_temp.b.h.value = self.read_operand(0)
            self.m_temp.b.l.value = self.read_operand(1)
            self.nop()

        self.set_ea(self.m_temp.w.value)

    def state_1(self) -> None:
        self.m_inst_tbl[self.m_opcode]()
        # logging.critical('Konami2: execute_one() Unsuporrted Opcode:{:02X} at {:04X} bank: {:02X} - {}'.format(self.m_opcode, self.m_pc.w.value, self.m_bank,  datetime.now()))
        # self.m_pc.w.value+=1

    #LEAX
    def func_08(self) -> None:
        self.set_regop16(self.m_x)
        self.push_state(2)
        self.INDEXED()
        return
    #LEAY
    def func_09(self) -> None:
        self.set_regop16(self.m_y)
        self.push_state(2)
        self.INDEXED()
        return            
    #LEAU
    def func_0a(self) -> None:        
        self.set_regop16(self.m_u)
        self.push_state(3)
        self.INDEXED()
        return
    #LEAS
    def func_0b(self) -> None:        
        self.set_regop16(self.m_s)
        self.push_state(3)
        self.INDEXED()
        return

    #Stack operation
    #PUSHS
    def func_0c(self) -> None:        
        self.PSHS()
        return
    #PUSHU            
    def func_0d(self) -> None:            
        self.PSHU()
        return
    #PULLS
    def func_0e(self) -> None:            
        self.PULS()
        return
    #PULLU
    def func_0f(self) -> None:            
        self.PULU()
        return

    # LD8 opcodes
    #LDA IMM
    def func_10(self) -> None:    
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.LD8()
        return
    #LDB IMM
    def func_11(self) -> None:            
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.LD8()
        return
    #LDA IND
    def func_12(self) -> None:            
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(4)
        self.INDEXED()
        return
    #LDB IND
    def func_13(self) -> None:            
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(4)
        self.INDEXED()
        return

    #ADD8 opcodes
    #ADDA
    def func_14(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.ADD8()
        return
    #ADDB
    def func_15(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.ADD8()
        return
    #ADDA
    def func_16(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(5)
        self.INDEXED()
        return
    #ADDB
    def func_17(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(5)
        self.INDEXED()
        return

    #ADC8 opcodes
    #ADCA
    def func_18(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.ADC8()
        return
    #ADCB
    def func_19(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.ADC8()
        return
    #ADCA
    def func_1a(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(6)
        self.INDEXED()
        return
    #ADCB
    def func_1b(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(6)
        self.INDEXED()
        return

    #SUB8 opcodes
    #SUBA
    def func_1c(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.SUB8()
        return
    #SUBB
    def func_1d(self) -> None:            
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.SUB8()
        return
    #SUBA
    def func_1e(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(7)
        self.INDEXED()
        return
    #SUBB
    def func_1f(self) -> None:            
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(7)
        self.INDEXED()
        return

    #SBC8 opcodes
    def func_20(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.SBC8()
        return
    def func_21(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.SBC8()
        return
    def func_22(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(8)
        self.INDEXED()
        return
    def func_23(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(8)
        self.INDEXED()
        return

    #AND8 opcodes
    def func_24(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.AND8()
        return
    def func_25(self) -> None:            
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.AND8()
        return
    def func_26(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(9)
        self.INDEXED()
        return
    def func_27(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(9)
        self.INDEXED()
        return

    #BIT8 opcodes
    def func_28(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.BIT8()
        return
    def func_29(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.BIT8()
        return
    def func_2a(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(10)
        self.INDEXED()
        return
    def func_2b(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(10)
        self.INDEXED()
        return

    #EOR8 opcodes
    def func_2c(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.EOR8()
        return
    def func_2d(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.EOR8()
        return
    def func_2e(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(11)
        self.INDEXED()
        return
    def func_2f(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(11)
        self.INDEXED()
        return

    #OR8 opcodes
    def func_30(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.OR8()
        return
    def func_31(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.OR8()
        return
    def func_32(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(12)
        self.INDEXED()
        return
    def func_33(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(12)
        self.INDEXED()
        return

    #CMP8 opcodes
    def func_34(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.set_imm()
        self.CMP8()
        return
    def func_35(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.set_imm()
        self.CMP8()
        return
    def func_36(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(13)
        self.INDEXED()
        return
    def func_37(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(13)
        self.INDEXED()
        return

    #SETLINE opcodes
    def func_38(self) -> None:
        self.set_imm()
        self.set_lines(self.read_operand2())
        #self.SETLINE()
        return
    def func_39(self) -> None:
        self.push_state(14)
        self.INDEXED()
        return

    #ST8 opcodes
    #STA
    def func_3a(self) -> None:
        self.set_regop8(self.m_q.r.r8.a)
        self.push_state(15)
        self.INDEXED()
        return
    #STB
    def func_3b(self) -> None:
        self.set_regop8(self.m_q.r.r8.b)
        self.push_state(15)
        self.INDEXED()
        return

    #ANDCC
    def func_3c(self) -> None:
        self.set_imm()
        self.ANDCC()
        return

    #ORCC
    def func_3d(self) -> None:
        self.set_imm()
        self.ORCC()
        return

    #EXG
    def func_3e(self) -> None:
        self.EXG()
        return

    #TFR
    def func_3f(self) -> None:
        self.TFR()
        return

    #LD16 opcodes
    #LDD
    def func_40(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.set_imm()
        self.LD16()
        return
    def func_41(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.push_state(16)
        self.INDEXED()
        return
    #LDX
    def func_42(self) -> None:
        self.set_regop16(self.m_x)
        self.set_imm()
        self.LD16()
        return
    def func_43(self) -> None:
        self.set_regop16(self.m_x)
        self.push_state(16)
        self.INDEXED()
        return
    #LDY
    def func_44(self) -> None:            
        self.set_regop16(self.m_y)
        self.set_imm()
        self.LD16()
        return
    def func_45(self) -> None:
        self.set_regop16(self.m_y)
        self.push_state(16)
        self.INDEXED()
        return
    #LDU
    def func_46(self) -> None:            
        self.set_regop16(self.m_u)
        self.set_imm()
        self.LD16()
        return
    def func_47(self) -> None:
        self.set_regop16(self.m_u)
        self.push_state(16)
        self.INDEXED()
        return
    #LDS
    def func_48(self) -> None:
        self.set_regop16(self.m_s)
        self.set_imm()
        self.LD16()
        return
    def func_49(self) -> None:
        self.set_regop16(self.m_s)
        self.push_state(16)
        self.INDEXED()
        return

    #CMP16 opcodes
    #CMPD
    def func_4a(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.set_imm()
        self.CMP16()
        return
    def func_4b(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.push_state(17)
        self.INDEXED()
        return
    #CMPX
    def func_4c(self) -> None:
        self.set_regop16(self.m_x)
        self.set_imm()
        self.CMP16()
        return
    def func_4d(self) -> None:
        self.set_regop16(self.m_x)
        self.push_state(17)
        self.INDEXED()
        return
    #CMPY
    def func_4e(self) -> None:
        self.set_regop16(self.m_y)
        self.set_imm()
        self.CMP16()
        return
    def func_4f(self) -> None:
        self.set_regop16(self.m_y)
        self.push_state(17)
        self.INDEXED()
        return
    #CMPU
    def func_50(self) -> None:
        self.set_regop16(self.m_u)
        self.set_imm()
        self.CMP16()
        return
    def func_51(self) -> None:
        self.set_regop16(self.m_u)
        self.push_state(17)
        self.INDEXED()
        return
    #CMPS
    def func_52(self) -> None:
        self.set_regop16(self.m_s)
        self.set_imm()
        self.CMP16()
        return
    def func_53(self) -> None:
        self.set_regop16(self.m_s)
        self.push_state(17)
        self.INDEXED()
        return

    #ADD16 opcodes
    #ADDD
    def func_54(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.set_imm()
        self.ADD16()
        return
    def func_55(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.push_state(18)
        self.INDEXED()
        return

    #SUB16 opcodes
    #SUBD
    def func_56(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.set_imm()
        self.SUB16()
        return
    def func_57(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.push_state(19)
        self.INDEXED()
        return

    #ST16 opcodes
    #STD
    def func_58(self) -> None:
        self.set_regop16(self.m_q.p.d)
        self.push_state(20)
        self.INDEXED()
        return
    #STX
    def func_59(self) -> None:
        self.set_regop16(self.m_x)
        self.push_state(20)
        self.INDEXED()
        return
    #STY
    def func_5a(self) -> None:
        self.set_regop16(self.m_y)
        self.push_state(20)
        self.INDEXED()
        return
    #STU
    def func_5b(self) -> None:
        self.set_regop16(self.m_u)
        self.push_state(20)
        self.INDEXED()
        return
    #STS
    def func_5c(self) -> None:
        self.set_regop16(self.m_s)
        self.push_state(20)
        self.INDEXED()
        return

    #BRANCH true cond.
    #BRA
    def func_60(self) -> None:
        self.set_cond(True)
        self.BRANCH()
        return
    #BHI
    def func_61(self) -> None:
        self.set_cond(self.cond_hi())
        self.BRANCH()
        return
    #BCC
    def func_62(self) -> None:
        self.set_cond(self.cond_cc())
        self.BRANCH()
        return
    #BNE
    def func_63(self) -> None:
        self.set_cond(self.cond_ne())
        self.BRANCH()
        return #BNE, Branch Not Equal, after compare or substract, if the register don't match memory operand, causes a branch if the Z bit is clear.
    #BVC
    def func_64(self) -> None:
        self.set_cond(self.cond_vc())
        self.BRANCH()
        return
    #BPL
    def func_65(self) -> None:
        self.set_cond(self.cond_pl())
        self.BRANCH()
        return
    #BGE
    def func_66(self) -> None:
        self.set_cond(self.cond_ge())
        self.BRANCH()
        return
    #BGT
    def func_67(self) -> None:
        self.set_cond(self.cond_gt())
        self.BRANCH()
        return

    #LBRANCH true cond.
    #LBRA
    def func_68(self) -> None:
        self.set_cond(True)
        self.LBRANCH()
        return
    #LBHI
    def func_69(self) -> None:
        self.set_cond(self.cond_hi())
        self.LBRANCH()
        return
    #LBCC
    def func_6a(self) -> None:
        self.set_cond(self.cond_cc())
        self.LBRANCH()
        return
    #LBNE
    def func_6b(self) -> None:
        self.set_cond(self.cond_ne())
        self.LBRANCH()
        return
    #LBVC
    def func_6c(self) -> None:
        self.set_cond(self.cond_vc())
        self.LBRANCH()
        return
    #LBPL
    def func_6d(self) -> None:
        self.set_cond(self.cond_pl())
        self.LBRANCH()
        return
    #LBGE
    def func_6e(self) -> None:
        self.set_cond(self.cond_ge())
        self.LBRANCH()
        return
    #LBGT
    def func_6f(self) -> None:
        self.set_cond(self.cond_gt())
        self.LBRANCH()
        return

    #BRANCH false cond.
    #BRN
    def func_70(self) -> None:
        self.set_cond(False)
        self.BRANCH()
        return
    #BLS
    def func_71(self) -> None:
        self.set_cond( not self.cond_hi())
        self.BRANCH()
        return
    #BCS
    def func_72(self) -> None:
        self.set_cond( not self.cond_cc())
        self.BRANCH()
        return
    #BEQ
    def func_73(self) -> None:
        self.set_cond( not self.cond_ne())
        self.BRANCH()
        return
    #BVS
    def func_74(self) -> None:
        self.set_cond( not self.cond_vc())
        self.BRANCH()
        return
    #BMI
    def func_75(self) -> None:
        self.set_cond( not self.cond_pl())
        self.BRANCH()
        return #BMI Branch on Minus, check if N is set.
    #BLT
    def func_76(self) -> None:
        self.set_cond( not self.cond_ge())
        self.BRANCH()
        return
    #BLE
    def func_77(self) -> None:
        self.set_cond( not self.cond_gt())
        self.BRANCH()
        return

    #LBRANCH false cond.
    #LBRN
    def func_78(self) -> None:
        self.set_cond(False)
        self.LBRANCH()
        return
    #LBLS
    def func_79(self) -> None:
        self.set_cond( not self.cond_hi())
        self.LBRANCH()
        return
    #LBCS
    def func_7a(self) -> None:
        self.set_cond( not self.cond_cc())
        self.LBRANCH()
        return
    #LBEQ
    def func_7b(self) -> None:
        self.set_cond( not self.cond_ne())
        self.LBRANCH()
        return
    #LBVS
    def func_7c(self) -> None:
        self.set_cond( not self.cond_vc())
        self.LBRANCH()
        return
    #LBMI
    def func_7d(self) -> None:
        self.set_cond( not self.cond_pl())
        self.LBRANCH()
        return
    #LBLT
    def func_7e(self) -> None:
        self.set_cond( not self.cond_ge())
        self.LBRANCH()
        return
    #LBLE
    def func_7f(self) -> None:
        self.set_cond( not self.cond_gt())
        self.LBRANCH()
        return

    #CLR8
    def func_80(self) -> None:
        self.set_a()
        self.CLR8()
        return
    def func_81(self) -> None:
        self.set_b()
        self.CLR8()
        return
    def func_82(self) -> None:
        self.push_state(21)
        self.INDEXED()
        return

    #COM8
    def func_83(self) -> None:
        self.set_a()
        self.COM8()
        return
    def func_84(self) -> None:
        self.set_b()
        self.COM8()
        return
    def func_85(self) -> None:
        self.push_state(22)
        self.INDEXED()
        return

    #NEG8
    def func_86(self) -> None:
        self.set_a()
        self.NEG8()
        return
    def func_87(self) -> None:
        self.set_b()
        self.NEG8()
        return
    def func_88(self) -> None:
        self.push_state(23)
        self.INDEXED()
        return

    #INC8
    def func_89(self) -> None:
        self.set_a()
        self.INC8()
        return
    def func_8a(self) -> None:
        self.set_b()
        self.INC8()
        return
    def func_8b(self) -> None:
        self.push_state(24)
        self.INDEXED()
        return

    #DEC8
    def func_8c(self) -> None:
        self.set_a()
        self.DEC8()
        return
    def func_8d(self) -> None:
        self.set_b()
        self.DEC8()
        return
    def func_8e(self) -> None:
        self.push_state(25)
        self.INDEXED()
        return

    #RTS
    def func_8f(self) -> None:
        self.RTS()
        return

    #TST8
    def func_90(self) -> None:
        self.set_a()
        self.TST8()
        return
    def func_91(self) -> None:
        self.set_b()
        self.TST8()
        return
    def func_92(self) -> None:
        self.push_state(26)
        self.INDEXED()
        return

    #LSR8
    def func_93(self) -> None:
        self.set_a()
        self.LSR8()
        return
    def func_94(self) -> None:
        self.set_b()
        self.LSR8()
        return
    def func_95(self) -> None:
        self.push_state(27)
        self.INDEXED()
        return

    #ROR8
    #RORA
    def func_96(self) -> None:
        self.set_a()
        self.ROR8()
        return
    #RORB
    def func_97(self) -> None:
        self.set_b()
        self.ROR8()
        return
    #ROR
    def func_98(self) -> None:
        self.push_state(28)
        self.INDEXED()
        return

    #ASR8
    def func_99(self) -> None:
        self.set_a()
        self.ASR8()
        return
    def func_9a(self) -> None:
        self.set_b()
        self.ASR8()
        return
    def func_9b(self) -> None:
        self.push_state(29)
        self.INDEXED()
        return

    #ASL8
    def func_9c(self) -> None:
        self.set_a()
        self.ASL8()
        return
    def func_9d(self) -> None:
        self.set_b()
        self.ASL8()
        return
    def func_9e(self) -> None:
        self.push_state(30)
        self.INDEXED()
        return

    #RTI
    def func_9f(self) -> None:
        self.RTI()
        return

    #ROL8
    def func_a0(self) -> None:
        self.set_a()
        self.ROL8()
        return
    def func_a1(self) -> None:
        self.set_b()
        self.ROL8()
        return
    def func_a2(self) -> None:
        self.push_state(31)
        self.INDEXED()
        return

    #LSR16
    #LSRW
    def func_a3(self) -> None:
        self.push_state(32)
        self.INDEXED()
        return

    #ROR16
    #RORW
    def func_a4(self) -> None:
        self.push_state(33)
        self.INDEXED()
        return

    #ASR16
    #ASRW
    def func_a5(self) -> None:
        self.push_state(34)
        self.INDEXED()
        return

    #ASL16
    #ASLW
    def func_a6(self) -> None:
        self.push_state(35)
        self.INDEXED()
        return

    #ROL16
    #ROLW
    def func_a7(self) -> None:
        self.push_state(36)
        self.INDEXED()
        return

    #JMP
    def func_a8(self) -> None:
        self.push_state(37)
        self.INDEXED()
        return

    #JSR
    def func_a9(self) -> None:
        self.push_state(38)
        self.INDEXED()
        return

    #BSR
    def func_aa(self) -> None:
        self.BSR()
        return

    #LBSR
    def func_ab(self) -> None:
        self.LBSR()
        return

    #DECBJNZ
    def func_ac(self) -> None:
        self.DECBJNZ()
        return

    #DECXJNZ
    def func_ad(self) -> None:
        self.DECXJNZ()
        return

    #NOP
    def func_ae(self) -> None:
        self.NOP()
        return

    #ABX
    def func_b0(self) -> None:
        self.ABX()
        return

    #DAA
    def func_b1(self) -> None:
        self.DAA()
        return

    #SEX
    def func_b2(self) -> None:
        self.SEX()
        return

    #MUL
    def func_b3(self) -> None:
        self.MUL()
        return

    #LMUL
    def func_b4(self) -> None:
        self.LMUL()
        return

    #DIVX
    def func_b5(self) -> None:
        self.DIVX()
        return

    #BMOVE
    def func_b6(self) -> None:
        self.BMOVE()
        return

    #MOVE
    def func_b7(self) -> None:
        self.MOVE()
        return

    #LSRD
    def func_b8(self) -> None:
        self.set_imm()
        self.LSRD()
        return
    def func_b9(self) -> None:
        self.push_state(39)
        self.INDEXED()
        return

    #RORD
    def func_ba(self) -> None:
        self.set_imm()
        self.RORD()
        return
    def func_bb(self) -> None:
        self.push_state(40)
        self.INDEXED()
        return

    #ASRD
    def func_bc(self) -> None:
        self.set_imm()
        self.ASRD()
        return
    def func_bd(self) -> None:
        self.push_state(41)
        self.INDEXED()
        return

    #ASLD
    def func_be(self) -> None:
        self.set_imm()
        self.ASLD()
        return
    def func_bf(self) -> None:
        self.push_state(42)
        self.INDEXED()
        return

    #ROLD
    def func_c0(self) -> None:
        self.set_imm()
        self.ROLD()
        return
    def func_c1(self) -> None:
        self.push_state(43)
        self.INDEXED()
        return

    #CLR16
    #CLRD
    def func_c2(self) -> None:
        self.set_d()
        self.CLR16()
        return
    #CLRW
    def func_c3(self) -> None:
        self.push_state(44)
        self.INDEXED()
        return

    #NEG16
    #NEGD
    def func_c4(self) -> None:
        self.set_d()
        self.NEG16()
        return
    #NEGW
    def func_c5(self) -> None:
        self.push_state(45)
        self.INDEXED()
        return

    #INC16
    #INCD
    def func_c6(self) -> None:
        self.set_d()
        self.INC16()
        return
    #INCW
    def func_c7(self) -> None:
        self.push_state(46)
        self.INDEXED()
        return

    #DEC16
    #DECD
    def func_c8(self) -> None:
        self.set_d()
        self.DEC16()
        return
    #DECW
    def func_c9(self) -> None:
        self.push_state(47)
        self.INDEXED()
        return

    #TST16
    #TSTD
    def func_ca(self) -> None:
        self.set_d()
        self.TST16()
        return
    #TSTW
    def func_cb(self) -> None:
        self.push_state(48)
        self.INDEXED()
        return

    #ABS8
    #ABSA
    def func_cc(self) -> None:
        self.set_a()
        self.ABS8()
        return
    #ABSB
    def func_cd(self) -> None:
        self.set_b()
        self.ABS8()
        return

    #ABS16
    #ABSD
    def func_ce(self) -> None:
        self.set_d()
        self.ABS16()
        return

    #BSET
    def func_cf(self) -> None:
        self.BSET()
        return

    #BSET2
    def func_d0(self) -> None:
        self.BSET2()
        return

    def BSET2(self) -> None:
        #BSET2 does not appear to be interruptable
        while(self.m_u.w.value != 0):
            self.eat(1)
            self.write_memory(self.m_x.w.value, self.m_q.r.r8.a.value)
            self.m_x.w.value +=1
            self.write_memory(self.m_x.w.value, self.m_q.r.r8.b.value)
            self.m_x.w.value +=1
            self.m_u.w.value -=1

    def BSET(self) -> None:
        #BSET does not appear to be interruptable
        while(self.m_u.w.value != 0):
            self.eat(1)
            self.write_memory(self.m_x.w.value, self.m_q.r.r8.a.value)
            self.m_x.w.value +=1
            self.m_u.w.value -=1

    def ABS16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        parameter = Tint16(self.m_temp.sw.value if(self.m_temp.sw.value >= 0) else -self.m_temp.sw.value)
        self.m_temp.w.value = self.set_flags2(FLAGS.CC_NZVC.value, Tuint16(0), self.m_temp.w, parameter.value).value
        self.eat(1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    def ABS8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        parameter = Tint8(self.m_temp.sb.l.value if(self.m_temp.sb.l.value >= 0) else -self.m_temp.sb.l.value)
        self.m_temp.b.l.value = self.set_flags2(FLAGS.CC_NZVC.value, Tuint8(0), self.m_temp.b.l, parameter.value).value
        self.eat(1)
        self.write_operand2(self.m_temp.b.l.value)

    def TST16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.set_flags(FLAGS.CC_NZV.value, self.m_temp.w)
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.eat(0 if (self.is_register_addressing_mode()) else 1)

    def DEC16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.m_temp.w.value = self.set_flags2(FLAGS.CC_NZVC.value, self.m_temp.w, Tuint16(1), self.m_temp.w.value-1).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    def INC16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.m_temp.w.value = self.set_flags2(FLAGS.CC_NZVC.value, self.m_temp.w, Tuint16(1), self.m_temp.w.value+1).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    def NEG16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.m_temp.w.value = self.set_flags2(FLAGS.CC_NZVC.value, Tuint16(0), self.m_temp.w, -self.m_temp.w.value).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    def CLR16(self) -> None:
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.m_cc &= (FLAGS.CC_NZVC.value ^ 0xFF) #m_cc &= ~CC_NZVC;
        self.m_cc |= FLAGS.CC_Z.value
        self.write_operand(0, 0x00)
        self.write_operand(1, 0x00)

    def ROLD(self) -> None:
        self.m_temp.b.l.value =self.read_operand2()
        while(self.m_temp.b.l.value > 0):
            self.m_temp.b.l.value -= 1
            self.m_temp.w.value = self.set_flags(FLAGS.CC_NZ.value, self.rotate_left(self.m_temp.w)).value
        self.eat(1)

    def ASLD(self) -> None:
        self.m_temp.b.l.value =self.read_operand2()

        if(self.m_temp.b.l.value != 0x00):
            #set C condition code, this converted to python from
            #if (m_q.r.d & safe_shift_left(1, m_temp.b.l))
            if(self.m_q.r.r16.d.value & self.safe_shift_right(Tuint32(0x10000), self.m_temp.b.l.value).value):
                self.m_cc |= FLAGS.CC_C.value
            else:
                self.m_cc &= (FLAGS.CC_C.value ^ 0xFF) #m_cc &= ~CC_C;
            self.m_q.r.r16.d.value = self.set_flags(FLAGS.CC_NZ.value, self.safe_shift_left(Tint16(self.m_q.r.r16.d.value), self.m_temp.b.l.value)).value
        self.eat(1)

    def ASRD(self) -> None:
        self.m_temp.b.l.value =self.read_operand2()

        if(self.m_temp.b.l.value != 0x00):
            #set C condition code, this converted to python from
            #if (m_q.r.d & safe_shift_left(1, m_temp.b.l))
            if(self.m_q.r.r16.d.value & self.safe_shift_left(Tuint16(1), self.m_temp.b.l.value).value):
                self.m_cc |= FLAGS.CC_C.value
            else:
                self.m_cc &= (FLAGS.CC_C.value ^ 0xFF) #m_cc &= ~CC_C;
            self.m_q.r.r16.d.value = self.set_flags(FLAGS.CC_NZ.value, self.safe_shift_right_unsigned(Tint16(self.m_q.r.r16.d.value), self.m_temp.b.l.value)).value
        self.eat(1)

    def RORD(self) -> None:
        self.m_temp.b.l.value =self.read_operand2()
        while(self.m_temp.b.l.value > 0):
            self.m_temp.b.l.value -= 1
            self.m_temp.w.value = self.set_flags(FLAGS.CC_NZ.value, self.rotate_right(self.m_temp.w)).value
        self.eat(1)

    def LSRD(self) -> None:
        self.m_temp.b.l.value =self.read_operand2()

        if(self.m_temp.b.l.value != 0x00):
            #set C condition code, this converted to python from
            #if (m_q.r.d & safe_shift_left(1, m_temp.b.l))
            if(self.m_q.r.r16.d.value & self.safe_shift_left(Tuint16(1), self.m_temp.b.l.value).value):
                self.m_cc |= FLAGS.CC_C.value
            else:
                self.m_cc &= (FLAGS.CC_C.value ^ 0xFF) #m_cc &= ~CC_C;
            self.m_q.r.r16.d.value = self.set_flags(FLAGS.CC_NZ.value, self.safe_shift_right_unsigned(self.m_q.r.r16.d, self.m_temp.b.l.value)).value
        self.eat(1)

    def MOVE(self) -> None:
        self.m_temp.b.l.value = self.read_memory(self.m_y.w.value)
        self.m_y.w.value +=1
        self.write_memory(self.m_x.w.value, self.m_temp.b.l.value)
        self.m_x.w.value +=1
        self.m_u.w.value -=1

    def BMOVE(self) -> None:
        #BMOVE is interruptable??? DEBUG THIS IN REAL HARDWARE
        while(self.m_u.w.value != 0):
            self.m_temp.b.l.value = self.read_memory(self.m_y.w.value)
            self.m_y.w.value +=1
            self.write_memory(self.m_x.w.value, self.m_temp.b.l.value)
            self.m_x.w.value +=1
            self.m_u.w.value -=1

    def DIVX(self) -> None:
        self.divx()
        self.eat(10)

    def LMUL(self) -> None:
        self.lmul()
        self.eat(21)

    def MUL(self) -> None:
        self.mul()
        self.eat(9 if (self.hd6309_native_mode()) else 10)

    def SEX(self) -> None:
        self.m_q.r.r16.d.value = self.set_flags(FLAGS.CC_NZ.value, Tint8(self.m_q.r.r8.b.value)).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)

    def DAA(self) -> None:
        self.daa()
        self.eat(0 if (self.hd6309_native_mode()) else 1)

    def ABX(self) -> None:
        self.m_x.w.value += self.m_q.r.r8.b.value
        self.eat(0 if (self.hd6309_native_mode()) else 2)

    def NOP(self) -> None:
        self.eat(0 if (self.hd6309_native_mode()) else 1)

    def DECXJNZ(self) -> None:
        self.m_x.w.value = self.set_flags2(FLAGS.CC_NZV.value, self.m_x.w, Tuint16(1), self.m_x.w.value - 1).value
        self.eat(1)
        self.set_cond(self.cond_ne())
        self.BRANCH()

    def DECBJNZ(self) -> None:
        self.m_q.r.r8.b.value = self.set_flags2(FLAGS.CC_NZV.value, self.m_q.r.r8.b, Tuint8(1), self.m_q.r.r8.b.value - 1).value
        self.eat(1)
        self.set_cond(self.cond_ne())
        self.BRANCH()

    def LBSR(self) -> None:
        self.m_temp.b.h.value = self.read_opcode_arg()
        self.m_temp.b.l.value = self.read_opcode_arg()
        self.m_ea.w.value = self.m_pc.w.value + self.m_temp.sw.value
        self.eat(2 if (self.hd6309_native_mode()) else 4)
        self.SUBROUTINE()

    def BSR(self) -> None:
        self.m_temp.b.l.value = self.read_opcode_arg()
        self.m_ea.w.value = self.m_pc.w.value + self.m_temp.sb.l.value
        self.eat(2 if (self.hd6309_native_mode()) else 3)
        self.SUBROUTINE()

    def JSR(self) -> None:
        self.eat(2)
        self.SUBROUTINE()

    def SUBROUTINE(self) -> None:
        self.m_s.w.value -=1
        self.write_memory(self.m_s.w.value, self.m_pc.b.l.value)
        self.m_s.w.value -=1
        self.write_memory(self.m_s.w.value, self.m_pc.b.h.value)
        self.m_pc.w.value = self.m_ea.w.value
        self.subr_called = True
        self.lst_pc = self.m_pc.w.value


    def JMP(self) -> None:
        self.m_jmp_called = True
        self.m_pc.w.value = self.m_ea.w.value

    def ROL16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        #rotate_left() returns c_uint32 value, not a reference
        self.m_temp.w.value = self.rotate_left(self.m_temp.w)
        self.m_temp.w.value = self.set_flags2(FLAGS.CC_NZV.value, self.m_temp.w).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    def ASL16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.m_temp.w.value = self.set_flags2(FLAGS.CC_NZVC.value, self.m_temp.w, self.m_temp.w, self.m_temp.w.value << 1).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    #DEBUG UNSIGNED TO SIGNED AND OPERATION CONVERSION
    def ASR16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.m_cc &= (FLAGS.CC_NZC.value ^ 0xFF) #m_cc &= ~CC_NZC;
        self.m_cc |= FLAGS.CC_C.value if (self.m_temp.w.value & 0x1) else 0
        self.m_temp.sw.value = self.m_temp.sw.value >> 1 #((int8_t) m_temp.b.l) >> 1
        self.m_temp.sw.value = self.set_flags(FLAGS.CC_NZ.value, self.m_temp.sw).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    def ROR16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.m_temp.w.value = self.rotate_right(self.m_temp.w).value
        self.m_temp.w.value = self.set_flags(FLAGS.CC_NZ.value, self.m_temp.w).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    def LSR16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.m_cc &= (FLAGS.CC_C.value ^ 0xFF) #m_cc &= ~CC_C;
        self.m_cc |= FLAGS.CC_C.value if (self.m_temp.w.value & 0x1) else 0
        self.m_temp.w.value >>= 1
        self.m_temp.w.value = self.set_flags(FLAGS.CC_NZ.value, self.m_temp.w).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand(0, self.m_temp.b.h.value)
        self.write_operand(1, self.m_temp.b.l.value)

    def ROL8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        #rotate_left() returns c_uint32 value, not a reference
        self.m_temp.b.l.value = self.set_flags2(FLAGS.CC_NZV.value, self.m_temp.b.l, self.m_temp.b.l, self.rotate_left(self.m_temp.b.l).value).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    def RTI(self) -> None:
        self.rti_exec=True
        self.lst_pc = self.m_pc.w.value
        self.set_regop16(self.m_s)
        self.m_temp.w.value = 0x0001 #RTS is equivalent to "PULS CC"
        self.push_state(118)
        self.PULL_REGISTERS()

    def state_118(self) -> None:
        #m_temp.w = ((m_cc & CC_E) ? entire_state_registers() : partial_state_registers()) & ~0x01
        self.m_temp.w.value = (self.entire_state_registers() if(self.m_cc & FLAGS.CC_E.value) else self.partial_state_registers()) & (0x01 ^ 0xFFFF)
        self.PULL_REGISTERS()
        #self.lst_pc2 = self.m_pc.w.value

    def ASL8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.m_temp.b.l.value = self.set_flags2(FLAGS.CC_NZVC.value, self.m_temp.b.l, self.m_temp.b.l, self.m_temp.b.l.value << 1).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    #DEBUG UNSIGNED TO SIGNED AND OPERATION CONVERSION
    def ASR8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.m_cc &= (FLAGS.CC_NZC.value ^ 0xFF) #m_cc &= ~CC_NZC;
        self.m_cc |= FLAGS.CC_C.value if (self.m_temp.b.l.value & 0x1) else 0
        self.m_temp.sb.l.value = self.m_temp.sb.l.value >> 1 #((int8_t) m_temp.b.l) >> 1
        self.m_temp.sb.l.value = self.set_flags(FLAGS.CC_NZ.value, self.m_temp.sb.l).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    def ROR8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.m_temp.b.l.value = self.rotate_right(self.m_temp.b.l).value
        self.m_temp.b.l.value = self.set_flags(FLAGS.CC_NZ.value, self.m_temp.b.l).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    def LSR8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.m_cc &= (FLAGS.CC_C.value ^ 0xFF) #m_cc &= ~CC_C;
        self.m_cc |= FLAGS.CC_C.value if (self.m_temp.b.l.value & 0x1) else 0
        self.m_temp.b.l.value >>= 1
        self.m_temp.b.l.value = self.set_flags(FLAGS.CC_NZ.value, self.m_temp.b.l).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    def TST8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.set_flags(FLAGS.CC_NZV.value, self.m_temp.b.l)
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.eat(0 if (self.is_register_addressing_mode()) else 1)

    def RTS(self) -> None:
        self.rts_exec=True
        self.lst_pc = self.m_pc.w.value - 1
        self.m_temp.w.value = 0x0080 #RTS is equivalent to "PULS PC"
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.set_regop16(self.m_s)
        self.PULL_REGISTERS()
        self.lst_pc2 = self.m_pc.w.value

    def DEC8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.m_temp.b.l.value = self.set_flags2(FLAGS.CC_NZV.value, self.m_temp.b.l, Tuint8(1),self.m_temp.b.l.value - 1).value
        self.eat(0 if (self.hd6309_native_mode() and self.is_register_addressing_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    def INC8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.m_temp.b.l.value = self.set_flags2(FLAGS.CC_NZV.value, self.m_temp.b.l, Tuint8(1), self.m_temp.b.l.value + 1).value
        self.eat(0 if (self.hd6309_native_mode() and self.is_register_addressing_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    def NEG8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.m_temp.b.l.value = self.set_flags2(FLAGS.CC_NZVC.value, self.m_temp.b.l, self.m_temp.b.l, -self.m_temp.b.l.value).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    def COM8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.m_cc &= (FLAGS.CC_V.value ^ 0xFF) #m_cc &= ~CC_V;
        self.m_cc |= FLAGS.CC_C.value
        self.m_temp.b.l.value ^= 0xFF #~m_temp.b.l
        self.m_temp.b.l.value = self.set_flags(FLAGS.CC_NZ.value, self.m_temp.b.l).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)
        self.write_operand2(self.m_temp.b.l.value)

    def CLR8(self) -> None:
        self.read_operand2()
        self.m_cc &= (FLAGS.CC_NZVC.value ^ 0xFF) #m_cc &= ~CC_NZVC;
        self.m_cc |= FLAGS.CC_Z.value
        self.eat(0 if (self.hd6309_native_mode() and self.is_register_addressing_mode()) else 1)
        self.write_operand2(0)

    #DEBUG UNSIGNED TO SIGNED AND OPERATION CONVERSION
    def LBRANCH(self) -> None:
        self.m_temp.b.h.value = self.read_opcode_arg()
        self.m_temp.b.l.value = self.read_opcode_arg()
        self.eat(1)
        if(self.branch_taken()):
            self.m_pc.w.value += self.m_temp.sw.value  #add unsigned value to PC? reading the text below I think that is a SIGNED VALUE (-32768 to 32767) 
            #For short branches, the byte following the branch instruction opcode is treated as an 8-bit signed offset to be used
            # to calculate the effective address of the next instruction if the branch is taken. This is called a short relative 
            # branch and the range is limited to plus 127 or minus 128 bytes from the following opcode.
            #For long branches, the two bytes after the opcode are used to calculate the effective address. This is called a 
            # long relative branch and the range is plus 32,767 or minus 32,768 bytes from the following opcode or the full 
            # 64K address space of memory that the processor can address at one time.
            self.eat(0 if (self.hd6309_native_mode()) else 1)

    #DEBUG UNSIGNED TO SIGNED AND OPERATION CONVERSION
    def BRANCH(self) -> None:
        self.m_temp.b.l.value = self.read_opcode_arg()
        self.eat(1)
        if(self.branch_taken()):
            self.m_pc.w.value += self.m_temp.sb.l.value  #add signed or complement a2 value to PC

    def ST16(self) -> None:
        self.write_operand(0, self.regop16().b.h.value)
        self.write_operand(1, self.regop16().b.l.value)
        self.set_flags(FLAGS.CC_NZV.value, self.regop16().w)

    def SUB16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.regop16().w.value =  self.set_flags2(FLAGS.CC_NZVC.value, self.regop16().w, self.m_temp.w, self.regop16().w.value - self.m_temp.w.value).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)

    def ADD16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.regop16().w.value =  self.set_flags2(FLAGS.CC_NZVC.value, self.regop16().w, self.m_temp.w, self.regop16().w.value + self.m_temp.w.value).value
        self.eat(0 if (self.hd6309_native_mode()) else 1)

    def CMP16(self) -> None:
        self.m_temp.b.h.value = self.read_operand(0)
        self.m_temp.b.l.value = self.read_operand(1)
        self.set_flags2(FLAGS.CC_NZVC.value, self.regop16().w, self.m_temp.w, self.regop16().w.value - self.m_temp.w.value)
        self.eat(0 if (self.hd6309_native_mode()) else 1)

    def LD16(self) -> None:
        self.regop16().b.h.value = self.read_operand(0)
        self.regop16().b.l.value = self.read_operand(1)
        self.set_flags(FLAGS.CC_NZV.value, self.regop16().w)

        if(addressof(self.regop16()) == addressof(self.m_s)):
            self.m_lds_encountered = True

    def EXG(self) -> None:
        param = self.read_opcode_arg()
        reg1:exgtfr_register = self.read_exgtfr_register(param >> 0)
        reg2:exgtfr_register = self.read_exgtfr_register(param >> 4)
        self.write_exgtfr_register(param >> 0, reg2)
        self.write_exgtfr_register(param >> 4, reg1)
        self.eat(3 if (self.hd6309_native_mode()) else 6)

    def TFR(self) -> None:
        param = self.read_opcode_arg()
        #print(f"param & 0x07 (read_exgtfr):{param & 0x07:02X}")
        reg:exgtfr_register = self.read_exgtfr_register(param >> 0)
        #print(f"param >> 4 & 0x07(write_exgtfr):{(param>>4) & 0x07:02X}")
        #print(f"reg WORD:{reg.word_value.value:04X}")
        #print(f"reg BYTE:{reg.byte_value.value:02X}")
        self.write_exgtfr_register(param >> 4, reg)
        self.eat(2 if (self.hd6309_native_mode()) else 4)
        #sys.exit()

    def ORCC(self) -> None:
        self.m_cc |= self.read_operand2()
        self.eat( 0 if (self.hd6309_native_mode()) else 1)

    def ANDCC(self) -> None:
        self.m_cc &= self.read_operand2()
        self.eat(1)

    def ST8(self) -> None:
        self.write_ea(self.set_flags(FLAGS.CC_NZV.value, self.regop8()).value)

    def SETLINE(self) -> None:
        self.set_lines(self.read_operand2())

    def CMP8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.set_flags2(FLAGS.CC_NZVC.value, self.regop8(), self.m_temp.b.l, self.regop8().value - self.m_temp.b.l.value)

    def OR8(self) -> None:
        self.m_cc &= (FLAGS.CC_V.value ^ 0xFF)
        self.regop8().value =  self.set_flags2(FLAGS.CC_NZ.value, Tuint8(0), self.regop8(), self.regop8().value | self.read_operand2()).value

    def EOR8(self) -> None:
        self.m_cc &= (FLAGS.CC_V.value ^ 0xFF)
        self.regop8().value =  self.set_flags2(FLAGS.CC_NZ.value, Tuint8(0), self.regop8(), self.regop8().value ^ self.read_operand2()).value

    def BIT8(self) -> None:
        self.m_cc &= (FLAGS.CC_V.value ^ 0xFF)
        self.set_flags2(FLAGS.CC_NZ.value, Tuint8(0), self.regop8(), self.regop8().value & self.read_operand2())

    def AND8(self) -> None:
        self.m_cc &= (FLAGS.CC_V.value ^ 0xFF)
        self.regop8().value =  self.set_flags2(FLAGS.CC_NZ.value, Tuint8(0), self.regop8(), self.regop8().value & self.read_operand2()).value

    def SBC8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        carry = 1 if(self.m_cc & FLAGS.CC_C.value) else 0
        self.regop8().value =  self.set_flags2(FLAGS.CC_NZVC.value, self.regop8(), self.m_temp.b.l, self.regop8().value - self.m_temp.b.l.value - carry).value

    def SUB8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        self.regop8().value =  self.set_flags2(FLAGS.CC_NZVC.value, self.regop8(), self.m_temp.b.l, self.regop8().value - self.m_temp.b.l.value).value

    def ADC8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        mask = FLAGS.CC_HNZVC.value if(self.add8_sets_h()) else FLAGS.CC_NZVC.value
        carry = 1 if(self.m_cc & FLAGS.CC_C.value) else 0
        self.regop8().value =  self.set_flags2(mask, self.regop8(), self.m_temp.b.l, self.regop8().value + self.m_temp.b.l.value + carry).value

    def ADD8(self) -> None:
        self.m_temp.b.l.value = self.read_operand2()
        mask = FLAGS.CC_HNZVC.value if(self.add8_sets_h()) else FLAGS.CC_NZVC.value
        self.regop8().value =  self.set_flags2(mask, self.regop8(), self.m_temp.b.l, self.regop8().value + self.m_temp.b.l.value).value

    def LD8(self) -> None:
        self.regop8().value = self.read_operand2()
        self.set_flags(FLAGS.CC_NZV.value, self.regop8())

    def PULS(self) -> None:
        self.m_temp.w.value = self.read_opcode_arg()
        self.eat(1 if self.hd6309_native_mode() else 2)
        self.set_regop16(self.m_s)
        self.PULL_REGISTERS()

    def PULU(self) -> None:
        self.m_temp.w.value = self.read_opcode_arg()
        self.eat(1 if self.hd6309_native_mode() else 2)
        self.set_regop16(self.m_u)
        self.PULL_REGISTERS()

    def PULL_REGISTERS(self) -> None:
        if(self.m_temp.w.value & 0x01):
            self.m_cc = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.nop()

        if(self.m_temp.w.value & 0x02):
            self.m_q.r.r8.a.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.nop()

        if(self.m_temp.w.value & 0x04):
            self.m_q.r.r8.b.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.nop()

        if(self.m_temp.w.value & 0x08):
            self.m_dp.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.nop()

        if(self.m_temp.w.value & 0x10):
            self.m_x.b.h.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.m_x.b.l.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.nop()

        if(self.m_temp.w.value & 0x20):
            self.m_y.b.h.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.m_y.b.l.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.nop()

        if(self.m_temp.w.value & 0x40):
            pullreg:PAIR16 = self.m_u if(addressof(self.regop16()) == addressof(self.m_s)) else self.m_s
            pullreg.b.h.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            pullreg.b.l.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.nop()

        if(self.m_temp.w.value & 0x80):
            self.m_pc.b.h.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.m_pc.b.l.value = self.read_memory(self.regop16().w.value)
            self.regop16().w.value = self.regop16().w.value + 1
            self.nop()

        self.eat(1)

    def PSHS(self) -> None:
        self.m_temp.w.value = self.read_opcode_arg()
        self.eat(2 if self.hd6309_native_mode() else 3)
        self.set_regop16(self.m_s)
        self.PUSH_REGISTERS()

    def PSHU(self) -> None:
        self.m_temp.w.value = self.read_opcode_arg()
        self.eat(2 if self.hd6309_native_mode() else 3)
        self.set_regop16(self.m_u)
        self.PUSH_REGISTERS()

    def PUSH_REGISTERS(self) -> None:
        if(self.m_temp.w.value & 0x80):
            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_pc.b.l.value)

            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_pc.b.h.value)

            self.nop()

        if(self.m_temp.w.value & 0x40):
            self.regop16().w.value -=1
            pushval = self.m_u.b.l.value if (addressof(self.regop16()) == addressof(self.m_s)) else self.m_s.b.l.value
            self.write_memory(self.regop16().w.value, pushval)

            self.regop16().w.value -=1
            pushval = self.m_u.b.h.value if (addressof(self.regop16()) == addressof(self.m_s)) else self.m_s.b.h.value
            self.write_memory(self.regop16().w.value, pushval)

            self.nop()

        if(self.m_temp.w.value & 0x20):
            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_y.b.l.value)

            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_y.b.h.value)

            self.nop()

        if(self.m_temp.w.value & 0x10):
            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_x.b.l.value)

            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_x.b.h.value)

            self.nop()

        if(self.m_temp.w.value & 0x08):
            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_dp.value)

            self.nop()

        if(self.m_temp.w.value & 0x04):
            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_q.r.r8.b.value)

            self.nop()

        if(self.m_temp.w.value & 0x02):
            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_q.r.r8.a.value)

            self.nop()

        if(self.m_temp.w.value & 0x01):
            self.regop16().w.value -=1
            self.write_memory(self.regop16().w.value, self.m_cc)

            self.nop()  

    def LEA_xy(self) -> None:
        self.regop16().w.value = self.set_flags(FLAGS.CC_Z.value, self.m_ea.w).value
        self.eat(1)

    def LEA_us(self) -> None:
        if(addressof(self.regop16()) == addressof(self.m_ea.w)):
            self.m_lds_encountered = True
        self.regop16().w.value = self.m_ea.w.value
        self.eat(1)

    #CPU states jump table
    cpu_state_table_jump = {
        0: MAIN, 1: state_1,
        2: LEA_xy, 3: LEA_us, 4: LD8, 5: ADD8, 6: ADC8, 7: SUB8,
        8: SBC8, 9: AND8, 10: BIT8, 11: EOR8, 12: OR8,
        13: CMP8, 14: SETLINE, 15: ST8,
        16: LD16, 17: CMP16, 18: ADD16, 19: SUB16, 20: ST16,
        21: CLR8, 22: COM8, 23: NEG8, 24: INC8, 25: DEC8, 26: TST8, 27: LSR8, 28: ROR8, 29: ASR8, 30: ASL8, 31: ROL8,
        32: LSR16, 33: ROR16, 34: ASR16, 35: ASL16, 36: ROL16, 37: JMP, 38: JSR,
        39: LSRD, 40: RORD , 41: ASRD, 42: ASLD, 43: ROLD,
        44: CLR16, 45: NEG16, 46: INC16, 47: DEC16, 48: TST16,
        49: state_49, 50: state_50, 51: state_51,
        118: state_118
        }

# if __name__ == "__main__":
#     modo_dbg = True #False

#     if(sys.gettrace() is not None):
#         #print('*** Modo depuracion ***')
#         modo_dbg = True

#     logging.info('*** LOGGING STARTED FROM konami2.py *** :{}'.format(datetime.now()))
#     #logging.critical('^^^^^ critical ^^^^^ :{}'.format(datetime.now()))

#     mirommap =  Konami2eproms(modo_dbg=modo_dbg)
#     memory_mapper()
    # romdata = array('B', [0x10, 0x20, 0x30, 0x40])
    # romdata = mirommap.readall_eprom(EPROM_Type.PROG)
    # kon2 = konami2_cpu_device(clock=12000000)
    # konami2_dis = kon2.create_disassembler()
    # kon2.device_start(AS_PROGRAM=romdata)
    # kon2.device_reset()
    # print(f"0x{0x7800:04X}: 0x{kon2.m_mintf.read(0x7800):02X} ")

    # start = timer()
    # while (kon2.m_pc.w.value < 0x804f):
        # print(kon2.m_state)
        # print(kon2.m_icount)
        # if not kon2.m_state:
        #     output = StringIO()
        #     offsetpc = konami2_dis.disassembler(pc=kon2.m_pc.w.value, stream=output, opcode_data=romdata)
        #     print("----------------------------")
        #     # print("Executed instruction:")
        #     # print()
        #     print("{:04X}: {}".format(kon2.m_pc.w.value, output.getvalue()))
        #     output.close()

        # kon2.execute_one()

        # if not kon2.m_state:
        #     # print("----------------------------")
        #     # print("Konami-2 Registers Status:")
        #     # print()
        #     print(f"A: 0x{kon2.m_q.r.r8.a.value:02X} B: 0x{kon2.m_q.r.r8.b.value:02X} D: 0x{kon2.m_q.r.r16.d.value:04X}")
        #     print(f"X: 0x{kon2.m_x.w.value:04X} Y: 0x{kon2.m_y.w.value:04X}")
        #     print(f"S: 0x{kon2.m_s.w.value:04X} U: 0x{kon2.m_u.w.value:04X}")
        #     print(f".            EFHINZVC")
        #     print(f"DP: 0x{kon2.m_dp.value:02X} CC: {kon2.m_cc:08b} PC: 0x{kon2.m_pc.w.value:04X}")
        #     # print("----------------------------")
        #     # print()
        # else:
        #     print(">>> INDEXED opcode")

    # end = timer()
    # print(f"# of cycles: {-kon2.m_icount} Total time: {end-start:.2f}s")
    # print(f"Cycle Period: {(end-start)/(-kon2.m_icount)*1000000000:.2f}ns")
    #kon2.DAA()

    # print(f"0x{0x7C00:04X}: 0x{kon2.m_mintf.read(0x7C00):02X} ")
    # print(f"0x{0x5D80:04X}: 0x{kon2.m_mintf.read(0x5D80):02X} ")
    # print(f"0x{0x5F00:04X}: 0x{kon2.m_mintf.read(0x5F00):02X} ")
    # print(f"0x{0x7800:04X}: 0x{kon2.m_mintf.read(0x7800):02X} ")



    # print('*** Konami-2 lmul() Normal Case ***')
    # CC_start = kon2.m_cc
    # kon2.m_x.w.value=0x80
    # kon2.m_y.w.value=0x01
    # print(f"X:{kon2.m_x.w.value:04X} Y:{kon2.m_y.w.value:04X} Flags (EFHINZVC)={kon2.m_cc:08b}")
    # kon2.lmul()
    # print(f"X:{kon2.m_x.w.value:04X} Y:{kon2.m_y.w.value:04X} Flags (EFHINZVC)={kon2.m_cc:08b}\n")

    # print('*** Konami-2 lmul() Normal Case ***')
    # kon2.m_cc = CC_start
    # kon2.m_x.w.value=0x80
    # kon2.m_y.w.value=0x02
    # print(f"X:{kon2.m_x.w.value:04X} Y:{kon2.m_y.w.value:04X} Flags (EFHINZVC)={kon2.m_cc:08b}")
    # kon2.lmul()
    # print(f"X:{kon2.m_x.w.value:04X} Y:{kon2.m_y.w.value:04X} Flags (EFHINZVC)={kon2.m_cc:08b}\n")

    # print('*** Konami-2 lmul() Zero Flag Case ***')
    # kon2.m_cc = CC_start
    # kon2.m_x.w.value=0x80
    # kon2.m_y.w.value=0x00
    # print(f"X:{kon2.m_x.w.value:04X} Y:{kon2.m_y.w.value:04X} Flags (EFHINZVC)={kon2.m_cc:08b}")
    # kon2.lmul()
    # print(f"X:{kon2.m_x.w.value:04X} Y:{kon2.m_y.w.value:04X} Flags (EFHINZVC)={kon2.m_cc:08b}\n")

    # print('*** Konami-2 lmul() Carry Flag Case ***')
    # kon2.m_cc = CC_start
    # kon2.m_x.w.value=0x8000
    # kon2.m_y.w.value=0x0001
    # print(f"X:{kon2.m_x.w.value:04X} Y:{kon2.m_y.w.value:04X} Flags (EFHINZVC)={kon2.m_cc:08b}")
    # kon2.lmul()
    # print(f"X:{kon2.m_x.w.value:04X} Y:{kon2.m_y.w.value:04X} Flags (EFHINZVC)={kon2.m_cc:08b}\n")

    # print('*** Konami-2 PUSH STACK ***')
    # kon2.m_x.w.value=0x2000
    # kon2.set_regop16(kon2.m_x.w)
    # print(f"Adr. Regop16(): {addressof(kon2.regop16()):08X}")
    # print(f"Adr. m_x: {addressof(kon2.m_x):08X}")
    # kon2.m_temp2.w = kon2.regop16()
    # print(f"m_temp2: {kon2.m_temp2.w.value:04X}")
    # kon2.m_temp2.w.value -=1
    # kon2.regop16().value = kon2.m_temp2.w.value
    # print(f"regop16(): {kon2.regop16().value:04X}")
    # print(f"m_x.w: {kon2.m_x.w.value:04X}")



