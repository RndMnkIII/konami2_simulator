#data types used by  m6809_base_device class
#use as:
#from m6809_types import ADRMOD, exgtfr_register, FLAGS, FLGC, CPUVECT
from enum import Enum
from ctypes import Union, Structure, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32
import sys

if (sys.byteorder == 'little'):
    from  m6809_regs_lite import Tuint8, Tuint16
else:
    from  m6809_regs_big import Tuint8, Tuint16
    #assert False, "No es sistema BigEndian"

class ADRMOD(Enum):
    ADDRESSING_MODE_IMMEDIATE = 0
    ADDRESSING_MODE_EA = 1
    ADDRESSING_MODE_REGISTER_A = 2
    ADDRESSING_MODE_REGISTER_B = 3
    ADDRESSING_MODE_REGISTER_D = 4

class exgtfr_register(Structure):
    _pack_ = 1
    _fields_ = [
        ('byte_value', Tuint8),
        ('word_value', Tuint16)
    ]

class FLAGS2(Enum):
    C        = 0x01         # Carry
    V        = 0x02         # Overflow
    Z        = 0x04         # Zero
    N        = 0x08         # Negative
    I        = 0x10         # Inhibit IRQ
    H        = 0x20         # Half (auxiliary) carry
    F        = 0x40         # Inhibit FIRQ
    E        = 0x80         # Entire state pushed
    
class FLAGS(Enum):
    CC_C        = 0x01         # Carry
    CC_V        = 0x02         # Overflow
    CC_Z        = 0x04         # Zero
    CC_N        = 0x08         # Negative
    CC_I        = 0x10         # Inhibit IRQ
    CC_H        = 0x20         # Half (auxiliary) carry
    CC_F        = 0x40         # Inhibit FIRQ
    CC_E        = 0x80         # Entire state pushed
    CC_VC       = 0x03 #self.FLAGS.CC_V.value | self.FLAGS.CC_C.value
    CC_ZC       = 0x05 #self.FLAGS.CC_Z.value | self.FLAGS.CC_C.value
    CC_NZ       = 0x0C #self.FLAGS.CC_N.value | self.FLAGS.CC_Z.value
    CC_NZC      = 0x0D #self.FLAGS.CC_N.value | self.FLAGS.CC_Z.value | self.FLAGS.CC_C.value
    CC_NZV      = 0x0E #self.FLAGS.CC_N.value | self.FLAGS.CC_Z.value | self.FLAGS.CC_V.value
    CC_NZVC     = 0x0F #self.FLAGS.CC_N.value | self.FLAGS.CC_Z.value | self.FLAGS.CC_V.value | self.FLAGS.CC_C.value
    CC_HNZVC    = 0x2F #self.FLAGS.CC_H.value | self.FLAGS.CC_N.value | self.FLAGS.CC_Z.value | self.FLAGS.CC_V.value | self.FLAGS.CC_C.value

class CPUVECT(Enum):
    VECTOR_SWI3         = 0xFFF2
    VECTOR_SWI2         = 0xFFF4
    VECTOR_FIRQ         = 0xFFF6
    VECTOR_IRQ          = 0xFFF8
    VECTOR_SWI          = 0xFFFA
    VECTOR_NMI          = 0xFFFC
    VECTOR_RESET_FFFE   = 0xFFFE

class STATEREGS(Enum):
        M6809_PC = -1
        M6809_S = 0
        M6809_CC = 1
        M6809_A = 2
        M6809_B = 3
        M6809_D = 4
        M6809_U = 5
        M6809_X = 6
        M6809_Y = 7
        M6809_DP = 8

class IRQLINE(Enum):
    M6809_IRQ_LINE = 0
    M6809_FIRQ_LINE = 1


#I/O line states
class line_state(Enum):
    CLEAR_LINE = 0 #clear (a fired or held) line
    ASSERT_LINE = 1 #assert an interrupt immediately
    HOLD_LINE = 2 #hold interrupt line until acknowledged


#I/O line definitions
class LINEDEF(Enum):
    #input lines
    MAX_INPUT_LINES = 64+3
    INPUT_LINE_IRQ0 = 0
    INPUT_LINE_IRQ1 = 1
    INPUT_LINE_IRQ2 = 2
    INPUT_LINE_IRQ3 = 3
    INPUT_LINE_IRQ4 = 4
    INPUT_LINE_IRQ5 = 5
    INPUT_LINE_IRQ6 = 6
    INPUT_LINE_IRQ7 = 7
    INPUT_LINE_IRQ8 = 8
    INPUT_LINE_IRQ9 = 9
    INPUT_LINE_NMI = MAX_INPUT_LINES - 3

    #special input lines that are implemented in the core
    INPUT_LINE_RESET = MAX_INPUT_LINES - 2
    INPUT_LINE_HALT = MAX_INPUT_LINES - 1



# print(0xf0 & FLGC.CC_ZC.value)    
# print(not(0xf0 & FLGC.CC_ZC.value)) 
# print(0xf5 & FLGC.CC_ZC.value)    
# print(not(0xf5 & FLGC.CC_ZC.value))
# print(0x04 & FLGC.CC_ZC.value)    
# print(not(0x04 & FLGC.CC_ZC.value))     
# print(0x05 & FLGC.CC_ZC.value)    
# print(not(0x05 & FLGC.CC_ZC.value))  

# a = 'h'
# if (a is not None):
#     print('a no está vacio')
# else:
#     print('a está vacio')
# val = 0x0a
# print (bool(val & FLAGS.CC_N.value) == bool(val & FLAGS.CC_V.value))
# print (bool(val & FLAGS.CC_N.value))
# print (bool(val & FLAGS.CC_V.value))
# print(type(c_uint8(FLAGS.CC_C.value)))
# print(c_uint8(FLAGS.CC_C.value).value)

# print(ADRMOD.ADDRESSING_MODE_EA.name)
# adr_mode = ADRMOD.ADDRESSING_MODE_REGISTER_A.value
# print(ADRMOD(adr_mode).name)