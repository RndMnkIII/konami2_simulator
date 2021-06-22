#TODO omitted class address_space (emumem.h) objects: m_program_config,  m_sprogram_config

from array import array
from typing import NamedTuple, List, TypeVar, Type
from enum import Enum
from ctypes import sizeof, byref, pointer, Union, Structure, c_int, c_ulong, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32
import sys

#Generics
from typing import TypeVar, Sequence

if (sys.byteorder == 'little'):
    from  m6809_regs_lite import Tuint8, Tint8, Tuint16, Tint16, Tuint32, Tint32,  PAIR16, M6809Q
else:
    from  m6809_regs_big import Tuint8, Tint8, Tuint16, Tint16, Tuint32, Tint32,  PAIR16, M6809Q
    #assert False, "No es sistema BigEndian"

from m6809_types import ADRMOD, exgtfr_register, FLAGS, CPUVECT, LINEDEF, line_state, IRQLINE
from eproms import EPROM_Type, EPROM_entry, Konami2eproms
from konami2_disassembler import OpcodesData, Konami2Disassembler
from m6809_execi import device_execute_interface, device_input


import logging

#I have a litte-endian machine, but target is big-endian

# Set to 1 to log interrupts
LOG_INTERRUPTS = 0
# logging.basicConfig(filename='m6809.log',level=logging.INFO)

class m6809_base_device:

    def __init__(self, clock: int) -> None:
        from memory_mapper import SELECTOR, memory_mapper
        # Memory interface
        self.m_mintf:memory_mapper = None
        self.clock = clock

        # CPU Registers
        self.m_pc = PAIR16()
        self.m_ppc = PAIR16()
        self.m_q = M6809Q()
        self.m_x = PAIR16()
        self.m_y = PAIR16()
        self.m_u = PAIR16()
        self.m_s = PAIR16()
        self.m_dp = Tuint8()
        self.m_cc:c_uint8
        self.m_temp = PAIR16()
        self.m_temp2 = PAIR16()
        self.m_opcode:c_uint8 = 0

        # Other internal state
        self.m_reg8 = Tuint8()
        self.m_reg16 = PAIR16()
        self.m_reg : int
        self.m_nmi_line : bool
        self.m_nmi_asserted : bool
        self.m_firq_line : bool
        self.m_irq_line : bool
        self.m_lds_encountered : bool
        self.m_icount : int
        self.m_tcount : c_ulong
        self.m_addressing_mode : int
        self.m_ea = PAIR16()

        #other state
        m_state : List[c_uint8]
        m_cond : bool

        #incidentals
        m_clock_divider : int

        #execute interface 
        m_dei = device_execute_interface()

        logging.info("m6809: __init()__: Initializated m6809_base_device")
    # Callbacks
    # devcb_write_line  m_lic_func; // LIC pin on the 6809E

    #Eat cycles
    def eat(self, cycles: int) -> None:
        self.m_icount += cycles
        self.m_tcount += cycles
    #void eat_remaining();
    
    def device_start(self) -> None:
        # print("&&& CALLED m6809 BASE CLASS &&&")
        if(self.m_mintf is None):
            self.m_mintf =self.m_mapper
        #self.m_mintf.m_program = AS_PROGRAM

        #m_lic_func.resolve_safe();

        #initialize variables
        self.m_cc = 0
        self.m_pc.w.value =0
        self.m_s.w.value = 0
        self.m_u.w.value = 0
        self.m_q.q.value =  0
        self.m_x.w.value = 0
        self.m_y.w.value = 0
        self.m_dp.value = 0
        self.m_reg  = 0
        self.m_reg8.value = 0
        self.m_reg16.w.value = 0

        self.m_icount = 0
        self.m_tcount = 0

    def device_reset(self) -> None:
        self.m_nmi_line = False
        self.m_nmi_asserted = False
        self.m_firq_line = False
        self.m_irq_line = False
        self.m_lds_encountered = False

        self.m_dp.value = 0

        self.m_cc |= FLAGS.CC_I.value
        self.m_cc |= FLAGS.CC_F.value

        self.m_pc.b.h.value = self.read_memory(CPUVECT.VECTOR_RESET_FFFE.value + 0)
        self.m_pc.b.l.value = self.read_memory(CPUVECT.VECTOR_RESET_FFFE.value + 1)
        
        #needed to clear because the two read_memory cycles
        # before dont need to be counted
        self.m_tcount = 0
        self.m_icount = 0
        
        self.reset_state()

    #void m6809_base_device::device_pre_save()
    #void m6809_base_device::device_post_load()
    #device_memory_interface::space_config_vector m6809_base_device::memory_space_config() const
    #void m6809_base_device::state_import(const device_state_entry &entry)
    #void m6809_base_device::state_string_export(const device_state_entry &entry, std::string &str) const
    #std::unique_ptr<util::disasm_interface> m6809_base_device::create_disassembler()

    def create_disassembler(self) -> Konami2Disassembler:
        pass

    # //**************************************************************************
    # //  CORE EXECUTION LOOP
    # //**************************************************************************

    # //-------------------------------------------------
    # //  execute_clocks_to_cycles - convert the raw
    # //  clock into cycles per second
    # //-------------------------------------------------
    def execute_clocks_to_cycles(self, clocks : c_ulong) -> c_ulong:
        return (clocks + self.m_clock_divider -1) / self.m_clock_divider

    # //-------------------------------------------------
    # //  execute_cycles_to_clocks - convert a cycle
    # //  count back to raw clocks
    # //-------------------------------------------------
    def execute_cycles_to_clocks(self, cycles: c_ulong) -> c_ulong:
        return cycles * self.m_clock_divider

    # //-------------------------------------------------
    # //  execute_min_cycles - return minimum number of
    # //  cycles it takes for one instruction to execute
    # //-------------------------------------------------
    def execute_min_cycles(self) -> c_uint32:
        return 1

    # //-------------------------------------------------
    # //  execute_max_cycles - return maximum number of
    # //  cycles it takes for one instruction to execute
    # //-------------------------------------------------
    def execute_max_cycles(self) -> c_uint32:
        return 19


    # //-------------------------------------------------
    # //  execute_input_lines - return the number of
    # //  input/interrupt lines
    # //-------------------------------------------------
    def execute_input_lines(self) -> c_uint32:
        return 3

    # //-------------------------------------------------
    # //  execute_set_input - act on a changed input/
    # //  interrupt line
    # //-------------------------------------------------
    def execute_set_input(self, inputnum: c_int, state: c_int) -> None:

        if (bool(LOG_INTERRUPTS)):
            #logerror("%s: inputnum=%s state=%d totalcycles=%d\n", machine().describe_context(), inputnum_string(inputnum), state, (int) attotime_to_clocks(machine().time()));
            pass
            
        if (inputnum == LINEDEF.INPUT_LINE_NMI.value):
            #NMI is edge triggered
            self.m_nmi_asserted = self.m_nmi_asserted or ((state != line_state.CLEAR_LINE.value) or  not(self.m_nmi_line) or  self.m_lds_encountered)
            self.m_nmi_line = bool(state != line_state.CLEAR_LINE.value)
            #BREAK
        elif(inputnum == IRQLINE.M6809_FIRQ_LINE.value):
            self.m_firq_line = bool(state != line_state.CLEAR_LINE.value)
            #BREAK
        elif(inputnum == IRQLINE.M6809_IRQ_LINE.value):
            self.m_irq_line = bool(state != line_state.CLEAR_LINE.value)
            #BREAK

    # //-------------------------------------------------
    # //  inputnum_string
    # //-------------------------------------------------
    def inputnum_string(self, inputnum: c_int) -> str:
        if(inputnum == LINEDEF.INPUT_LINE_NMI.value):
            return "NMI"
        elif(inputnum == IRQLINE.M6809_FIRQ_LINE.value):
            return "FIRQ"
        elif(inputnum == IRQLINE.M6809_IRQ_LINE.value):
            return "IRQ"
        else:
            return "???"

    # //-------------------------------------------------
    # //  read_exgtfr_register
    # //-------------------------------------------------
    def read_exgtfr_register(self, reg: c_uint8) -> exgtfr_register:
        result = exgtfr_register()
        result.byte_value.value = 0xFF
        result.word_value.value = 0x00FF

        if  ((reg & 0x0F) == 0X0): result.word_value.value = self.m_q.r.r16.d.value  #D
        elif((reg & 0x0F) == 0X1): result.word_value.value = self.m_x.w.value  #X
        elif((reg & 0x0F) == 0X2): result.word_value.value = self.m_y.w.value  #Y
        elif((reg & 0x0F) == 0X3): result.word_value.value = self.m_u.w.value  #U
        elif((reg & 0x0F) == 0X4): result.word_value.value = self.m_s.w.value  #S
        elif((reg & 0x0F) == 0X5): result.word_value.value = self.m_pc.w.value  #PC
        elif((reg & 0x0F) == 0X8): result.byte_value.value = self.m_q.r.r8.a.value  #A
        elif((reg & 0x0F) == 0X9): result.byte_value.value = self.m_q.r.r8.b.value  #B
        elif((reg & 0x0F) == 0XA): result.byte_value.value = self.m_cc #CC
        elif((reg & 0x0F) == 0XB): result.byte_value.value = self.m_dp.value #DP

        return result

    # //-------------------------------------------------
    # //  write_exgtfr_register
    # //-------------------------------------------------
    def write_exgtfr_register(self, reg: c_uint8, value: exgtfr_register) -> None:
        if  ((reg & 0x0F) == 0X0): self.m_q.r.r16.d.value =  value.word_value.value #D
        elif((reg & 0x0F) == 0X1): self.m_x.w.value =  value.word_value.value #X
        elif((reg & 0x0F) == 0X2): self.m_y.w.value =  value.word_value.value #Y
        elif((reg & 0x0F) == 0X3): self.m_u.w.value =  value.word_value.value #U
        elif((reg & 0x0F) == 0X4): self.m_s.w.value =  value.word_value.value #S
        elif((reg & 0x0F) == 0X5): self.m_pc.w.value =  value.word_value.value #PC
        elif((reg & 0x0F) == 0X8): self.m_q.r.r8.a.value = value.byte_value.value #A
        elif((reg & 0x0F) == 0X9): self.m_q.r.r8.b.value = value.byte_value.value  #B
        elif((reg & 0x0F) == 0XA): self.m_cc = value.byte_value.value #CC
        elif((reg & 0x0F) == 0XB): self.m_dp.value = value.byte_value.value #DP

    ######################################################
    class memory_interface:

        #The memory_interface inner class in simplified to only use a byte array as
        #memory device
        m_program : array
        m_sprogram : array

        def read (self, adr: c_uint16) -> c_uint8:
            return self.m_program[adr]

        def read_opcode(self, adr: c_uint16) -> c_uint8:
            return self.m_program[adr]

        def read_opcode_arg(self, adr: c_uint16) -> c_uint8:
            return self.m_program[adr]

        def write (self, adr: c_uint16, val: c_uint8) -> None:
            self.m_program[adr] = val

    def execute_run(self) -> None:
        pass

    def is_6809(self) -> bool:
        return True

    #Read a byte from given memory location    
    def read_memory(self, address : c_uint16) -> c_uint8:
        self.eat(1)
        return self.m_mintf.read(address)

    def write_memory(self, address:c_uint16, data: c_uint8) -> None:
        self.eat(1)
        self.m_mintf.write(address, data) 

    def read_opcode2(self, address : c_uint16) -> c_uint8:
        self.eat(1)
        return self.m_mintf.read(address)

    def read_opcode_arg2(self, address : c_uint16) -> c_uint8:
        self.eat(1) 
        return self.m_mintf.read(address)

    #read_opcode() and bump the program counter        
    def read_opcode(self) -> c_uint8:
        valor = self.read_opcode2(self.m_pc.w.value)
        self.m_pc.w.value += 1
        return valor

    def read_opcode_arg(self) -> c_uint8:
        valor = self.read_opcode_arg2(self.m_pc.w.value)
        self.m_pc.w.value += 1
        return valor

    # state stack
    def push_state(self, state : c_uint8) -> None:
        self.m_state.append(state)

    def pop_state(self) -> c_uint8:
        if not self.m_state:
            return 0
        return self.m_state.pop()

    def reset_state(self) -> None:
        self.m_state = [] 

    #effective address reading/writing
    def read_ea(self) -> c_uint8:
        return self.read_memory(self.m_ea.w.value)

    def write_ea(self, data: c_uint8) -> None:
        self.write_memory(self.m_ea.w.value, data)

    def set_ea(self, ea: c_uint16) -> None:
        self.m_ea.w.value = ea
        self.m_addressing_mode = ADRMOD.ADDRESSING_MODE_EA.value

    def set_ea_h(self, ea_h: c_uint8) -> None:
        self.m_ea.b.h.value = ea_h

    def set_ea_l(self, ea_l: c_uint8) -> None:
        self.m_ea.b.l.value = ea_l
        self.m_addressing_mode = ADRMOD.ADDRESSING_MODE_EA.value

    # operand reading/writing
	# uint8_t read_operand();
    def read_operand2(self) -> c_uint8:
        if(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_EA.value):
            return self.read_memory(self.m_ea.w.value)
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_IMMEDIATE.value):
            return self.read_opcode_arg()
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_REGISTER_A.value):
            return self.m_q.r.r8.a.value
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_REGISTER_B.value): 
            return self.m_q.r.r8.b.value   
        else:
            logging.critical("read_operand2(): Unexpected")
            return 0x00

	# uint8_t read_operand(int ordinal);
    def read_operand(self, ordinal: c_int16) -> c_uint8:
        if(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_EA.value):
            return self.read_memory(self.m_ea.w.value + ordinal)
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_IMMEDIATE.value):
            return self.read_opcode_arg()
        else:
            logging.critical("read_operand(ordinal): Unexpected")
            return 0x00

	# void write_operand(uint8_t data);
    def write_operand2(self, data:c_uint8) -> None:
        if(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_EA.value):
            self.write_memory(self.m_ea.w.value, data)
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_IMMEDIATE.value):
            pass
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_REGISTER_A.value):
            self.m_q.r.r8.a.value = data
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_REGISTER_B.value): 
            self.m_q.r.r8.b.value = data
        else:
            logging.critical("write_operand(data): Unexpected")

	# void write_operand(int ordinal, uint8_t data);
    def write_operand(self, ordinal: c_int16, data: c_uint8) -> None:
        if(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_EA.value):
            self.write_memory(self.m_ea.w.value + ordinal, data)
        elif(self.m_addressing_mode == ADRMOD.ADDRESSING_MODE_IMMEDIATE.value):
            pass
        else:
            logging.critical("write_operand(ordinal, data): Unexpected")

    #// instructions

    # //-------------------------------------------------
    # //  daa - decimal arithmetic adjustment instruction
    # //-------------------------------------------------
	# void daa();
    def daa(self) -> None:
        t = c_uint16(0)
        cf = c_uint16(0)
        msn = c_uint8( self.m_q.r.r8.a.value & 0xF0)
        lsn = c_uint8( self.m_q.r.r8.a.value & 0x0F)

        #compute the carry
        if ((lsn.value > 0x09) or bool(self.m_cc & FLAGS.CC_H.value)):
            cf.value |= 0x06
        if ((msn.value > 0x80) and (lsn.value > 0x09)):
            cf.value |= 0x60
        if ((msn.value > 0x90) or bool(self.m_cc & FLAGS.CC_C.value)):
            cf.value |= 0x60

        #calculate the result
        t.value = self.m_q.r.r8.a.value + cf.value

        self.m_cc &= (FLAGS.CC_V.value ^ 0xFF) #m_cc &= ~CC_V;
        if(bool(t.value & 0x0100)):
            self.m_cc |= FLAGS.CC_C.value
        
        tobj = Tuint8()
        tobj.value = t.value & 0xFF
        #put it back into A
        self.m_q.r.r8.a.value = self.set_flags( mask=FLAGS.CC_NZ.value, r=tobj).value

	# void mul();
    def mul(self) -> None:
        result = Tuint16(self.m_q.r.r8.a.value * self.m_q.r.r8.b.value)
        #set result and Z flag
        self.m_q.r.r16.d.value = self.set_flags(FLAGS.CC_Z.value, result).value
        #set C flag
        if(self.m_q.r.r16.d.value & 0x0080):
            self.m_cc |= FLAGS.CC_C.value
        else:
            self.m_cc &= (FLAGS.CC_C.value ^ 0XFF) #m_cc &= ~CC_C;

	# // miscellaneous
	# void nop()                                      { }
    def nop(self) -> None:
        pass
        #self.eat(0)

	# template<class T> T rotate_right(T value);
	# template<class T> uint32_t rotate_left(T value);
	# void set_a()                                    { m_addressing_mode = ADDRESSING_MODE_REGISTER_A; }
    def set_a(self) -> None:
        self.m_addressing_mode = ADRMOD.ADDRESSING_MODE_REGISTER_A.value

	# void set_b()                                    { m_addressing_mode = ADDRESSING_MODE_REGISTER_B; }
    def set_b(self) -> None:
        self.m_addressing_mode = ADRMOD.ADDRESSING_MODE_REGISTER_B.value

	# void set_d()                                    { m_addressing_mode = ADDRESSING_MODE_REGISTER_D; }
    def set_d(self) -> None:
        self.m_addressing_mode = ADRMOD.ADDRESSING_MODE_REGISTER_D.value

	# void set_imm()                                  { m_addressing_mode = ADDRESSING_MODE_IMMEDIATE; }
    def set_imm(self) -> None:
        self.m_addressing_mode = ADRMOD.ADDRESSING_MODE_IMMEDIATE.value

	# void set_regop8(uint8_t &reg)                     { m_reg8 = &reg; m_reg16 = nullptr; }
    def set_regop8(self, reg : Tuint8) -> None:
        self.m_reg8 = reg
        self.m_reg16 = None

	# void set_regop16(PAIR16 &reg)                   { m_reg16 = &reg; m_reg8 = nullptr; }
    def set_regop16(self, reg : PAIR16) -> None:
        self.m_reg8 = None
        self.m_reg16 = reg

	# uint8_t &regop8()                                 { assert(m_reg8 != nullptr); return *m_reg8; }
    def regop8(self) -> Tuint8:
        assert (self.m_reg8 is not None), "regop8(): m_reg8 should not be None"
        return self.m_reg8

	# PAIR16 &regop16()                               { assert(m_reg16 != nullptr); return *m_reg16; }
    def regop16(self) -> PAIR16:
        assert (self.m_reg16 is not None), "regop16(): m_reg16 should not be None"
        return self.m_reg16

	# bool is_register_register_op_16_bit()           { return m_reg16 != nullptr; }
    def is_register_register_op_16_bit(self) -> bool:
        return (m_reg16 is not None)

	# bool add8_sets_h()                              { return true; }
    def add8_sets_h(self) -> bool:
        return True

	# bool hd6309_native_mode()                       { return false; }
    def hd6309_native_mode(self) -> bool:
        return False

	# // index reg
	# uint16_t &ireg();
    def ireg(self) -> Tuint16:
        if((self.m_opcode & 0x60) == 0x00):
            return self.m_x.w
        elif((self.m_opcode & 0x60) == 0x20):
            return self.m_y.w
        elif((self.m_opcode & 0x60) == 0x40):
            return self.m_u.w
        elif((self.m_opcode & 0x60) == 0x60):
            return self.m_s.w               
        else:
            logging.critical("m6809_ireg(): Unexpected")
            return self.m_x.w

	# // flags
    T = TypeVar('T',Tuint8, Tuint16, Tuint32, Tint8, Tint16, Tint32)

    def set_flags2(self, mask: c_uint8, a: T, b: T, r: c_uint32) -> T:
        return self.__set_flags(member_class=type(a), mask=mask, a=a, b=b, r=r)

    def set_flags(self, mask: c_uint8, r: T) -> T:
        param_class = type(r)
        a = param_class()
        a.value = 0
        return self.__set_flags(member_class=type(r), mask=mask, a=a, b=r, r=r.value)

    def __set_flags(self, member_class: Type[T], mask: c_uint8, a: T, b: T, r:c_uint32) -> T:
        hi_bit = member_class()
        hi_bit.value =  (1 << (sizeof(b)*8-1))

        self.m_cc = self.m_cc & (mask ^ 0xFF) #equivalent to m_cc &= ~mask;
        if(mask & FLAGS.CC_H.value):
            self.m_cc |= FLAGS.CC_H.value if ((a.value ^ b.value ^ r) & 0x10) else 0
        if(mask & FLAGS.CC_N.value):
            self.m_cc |= FLAGS.CC_N.value if (r & hi_bit.value) else 0
        if(mask & FLAGS.CC_Z.value):
            self.m_cc |= FLAGS.CC_Z.value if (r == 0) else 0
        if(mask & FLAGS.CC_V.value):
            self.m_cc |= FLAGS.CC_V.value if ((a.value ^ b.value ^ r ^ (r>>1)) & hi_bit.value) else 0
        if(mask & FLAGS.CC_C.value):
            self.m_cc |= FLAGS.CC_C.value if (r & (hi_bit.value << 1)) else 0
        
        ret_obj = member_class()
        ret_obj.value = r
        return ret_obj

    # //-------------------------------------------------
    # //  rotate_right
    # //-------------------------------------------------
    def rotate_right(self, value: T) -> T:
        new_carry = True if (value.value & 0x1) else False
        value.value = value.value >> 1

        param_class = type(value)
        high_bit = param_class()
        high_bit.value =  (1 << (sizeof(value)*8-1))

        if(self.m_cc and FLAGS.CC_C.value):
            value.value |= high_bit.value
        else:
            value.value &= (high_bit.value ^0xFF)

        if(new_carry):
            self.m_cc |= FLAGS.CC_C.value
        else:
            self.m_cc |= (FLAGS.CC_C.value ^ 0xFF)

        return value

    # //-------------------------------------------------
    # //  rotate_left
    # //-------------------------------------------------
    def rotate_left(self, value: T) -> c_uint32:
        param_class = type(value)
        high_bit = param_class()
        high_bit.value =  (1 << (sizeof(value)*8-1))
        new_carry = True if (value.value & high_bit.value) else False
        
        new_value = c_uint32(value.value)
        new_value.value <<= 1


        if(self.m_cc and FLAGS.CC_C.value):
            new_value.value |= 0X00000001
        else:
            new_value.value &= (0X00000001 ^ 0xFFFFFFFF)

        if(new_carry):
            self.m_cc |= FLAGS.CC_C.value
        else:
            self.m_cc |= (FLAGS.CC_C.value ^ 0xFF)

        return new_value


    def eat_remaining(self) -> None:
        real_pc = m_pc.w.value

        self.eat(self.m_icount)

        self.m_pc.w = self.m_ppc.w
        #debugger_instruction_hook(m_pc.w);
        self.m_pc.w.value = real_pc

    # bool is_register_addressing_mode();
    def is_register_addressing_mode(self) -> None:
        return ((self.m_addressing_mode != ADRMOD.ADDRESSING_MODE_IMMEDIATE.value)
        and (self.m_addressing_mode != ADRMOD.ADDRESSING_MODE_EA.value))

    def get_pending_interrupt(self) -> c_uint16:
        if(self.m_nmi_asserted):
            return CPUVECT.VECTOR_NMI.value
        elif( not(self.m_cc & FLAGS.CC_F.value) and self.m_firq_line):
            return CPUVECT.VECTOR_FIRQ.value
        elif( not(self.m_cc & FLAGS.CC_I.value) and self.m_irq_line):
            return CPUVECT.VECTOR_IRQ.value
        else:
            return 0x0000



	# // branch conditions
	# inline bool cond_hi() { return !(m_cc & CC_ZC); }                                                // BHI/BLS
    def cond_hi(self) -> bool:
        return not bool(self.m_cc & FLAGS.CC_ZC.value)                                                #BHI/BLS
        
	# inline bool cond_cc() { return !(m_cc & CC_C);   }                                               // BCC/BCS
    def cond_cc(self) -> bool:
        return not bool(self.m_cc & FLAGS.CC_C.value)                                                 #BCC/BCS

	# inline bool cond_ne() { return !(m_cc & CC_Z);   }                                               // BNE/BEQ
    def cond_ne(self) -> bool:
        return not bool(self.m_cc & FLAGS.CC_Z.value)                                                  #BNE/BEQ

	# inline bool cond_vc() { return !(m_cc & CC_V);   }                                               // BVC/BVS
    def cond_vc(self) -> bool:
        return not bool(self.m_cc & FLAGS.CC_V.value)                                                 #BVC/BVS

	# inline bool cond_pl() { return !(m_cc & CC_N);   }                                               // BPL/BMI
    def cond_pl(self) -> bool:
        return not bool (self.m_cc & FLAGS.CC_N.value)                                                 #BPL/BMI

	# inline bool cond_ge() { return (m_cc & CC_N ? true : false) == (m_cc & CC_V ? true : false); }   // BGE/BLT
    def cond_ge(self) -> bool:
        return (bool(self.m_cc & FLAGS.CC_N.value) == bool(self.m_cc & FLAGS.CC_V.value))   #BGE/BLT

	# inline bool cond_gt() { return cond_ge() && !(m_cc & CC_Z); }                                    // BGT/BLE
    def cond_gt(self) -> bool:
        return (self.cond_ge() and (not bool(self.m_cc & FLAGS.CC_Z.value)))   #BGT/BLE

	# inline void set_cond(bool cond)  { m_cond = cond; }
    def set_cond(self, cond: bool) -> None:
        self.m_cond = cond

	# inline bool branch_taken()       { return m_cond; }
    def branch_taken(self) -> bool:
        return self.m_cond

	# // interrupt registers
	# bool firq_saves_entire_state()      { return false; }
    def firq_saves_entire_state(self) -> bool:
        return False

	# uint16_t partial_state_registers()    { return 0x81; }
    def partial_state_registers(self) -> c_uint16:
        return 0x81

	# uint16_t entire_state_registers()     { return 0xFF; }
    def entire_state_registers(self) -> c_uint16:
        return 0xFF

	# bool is_ea_addressing_mode() { return m_addressing_mode == ADDRESSING_MODE_EA; }
    def is_ea_addressing_mode(self) -> bool:
        return (self.m_addressing_mode ==  ADRMOD.ADDRESSING_MODE_EA) 

	# void log_illegal();
    def log_illegal(self) -> None:
        pass

    #private:
    # // address spaces
	# const address_space_config  m_program_config;
	# const address_space_config  m_sprogram_config;
    def execute_one(self) -> None:
        pass

# if __name__ == "__main__":
#     modo_dbg = True #False 

#     if(sys.gettrace() is not None):
#         #print('*** Modo depuracion ***')
#         modo_dbg = True

#     mirommap =  Konami2eproms(modo_dbg=modo_dbg)       
#     romdata = array('B', [0x10, 0x20, 0x30, 0x40])
#     romdata = mirommap.readall_eprom(EPROM_Type.PROG)
#     m6809 = m6809_base_device(clock=12000000)  
#     m6809.device_start(AS_PROGRAM=romdata)
#     m6809.device_reset()

#     print('0x{:04X}=0x{:02X}'.format(0xfffe, m6809.read_memory(0xfffe))) 
#     print('0x{:04X}=0x{:02X}'.format(0xffff, m6809.read_memory(0xffff))) 
#     print('PC=0x{:04X}'.format(m6809.m_pc.w.value))
#     m6809.m_q.q.value = 0xaabbeeff
#     print('m_q.q = {:08X}'.format(m6809.m_q.q.value))
#     print('m_q.p.w = {:04X}'.format(m6809.m_q.p.w.w.value))
#     print('m_q.p.d = {:04X}'.format(m6809.m_q.p.d.w.value))
#     print('m_q.p.w = {:04X}'.format(m6809.m_q.r.r16.w.value))
#     print('m_q.p.d = {:04X}'.format(m6809.m_q.r.r16.d.value))
#     print('m_q.r.r8.a= {:02X}'.format(m6809.m_q.r.r8.a.value))
#     print('m_q.r.r8.b= {:02X}'.format(m6809.m_q.r.r8.b.value))
#     print('m_q.r.r8.e= {:02X}'.format(m6809.m_q.r.r8.e.value))
#     print('m_q.r.r8.f= {:02X}'.format(m6809.m_q.r.r8.f.value))

#     m6809.set_regop8(m6809.m_q.r.r8.a)
#     print('Antes: m_q.r.r8.a = {:02X}'.format(m6809.regop8().value))

#     m6809.m_q.r.r8.a.value = 0x22
#     print('Despues: m_q.r.r8.a = {:02X}'.format(m6809.regop8().value))

#     m6809.set_regop8(m6809.m_q.r.r8.b)
#     print('Despues: m_q.r.r8.a = {:02X}'.format(m6809.regop8().value))
#     #m6809.write_memory(0x0001, 0xff) 
#     #print('0x{:04X}=0x{:02X}'.format(0x0001, m6809.read_memory(0x0001))) 
#     m6809._daa2()
#     print(f"{m6809.rotate_left(Tuint8(0x1f)).value:02X}")
#     print(f"{m6809.rotate_left(Tuint16(0x1ff)).value:04X}")
#     print(f"{m6809.rotate_left(Tuint32(0x1ffff)).value:08X}")

#     print(f"{m6809.rotate_right(Tuint8(0x3)).value:02X}")
#     print(f"{m6809.rotate_right(Tuint16(0x3)).value:04X}")
#     print(f"{m6809.rotate_right(Tuint32(0x3)).value:08X}")