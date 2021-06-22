from enum import Enum    
from ctypes import Union, BigEndianStructure, Structure, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32
import sys

# class Hello:
#     def __init__(self):
#         self.greeting = "Hello!"

# class Salut:
#     def __init__(self):
#         self.greeting = "Salut!"

# if sys.byteorder == 'little':
#     Hello = Salut

#I have a litte-endian machine, but target is big-endian

class PAIR16(Union):
    class _B(Structure):
        _pack_ = 1
        _fields_ = [
            ('l', c_uint8),
            ('h', c_uint8)

        ]

    class _SB(Structure):
        _pack_ = 1 
        _fields_ = [
            ('l', c_int8),
            ('h', c_int8)
        ]

    _pack_ = 1
    _fields_ = [
        ('b', _B),
        ('sb', _SB),
        ('w', c_uint16),
        ('sw', c_int16)
    ]



class M6809Q(Union):
    class _P(Structure):
        _pack_ = 1
        _fields_ = [
            ('d',  PAIR16),
            ('w',  PAIR16)
        ]

    class _R(Union):
        class _R8(Structure):
            _pack_ = 1
            _fields_ = [
                ('a', c_uint8),
                ('b', c_uint8),
                ('e', c_uint8),
                ('f', c_uint8)
            ]

        class _R16(Structure):
            _pack_ = 1
            _fields_ = [
                ('d', c_uint16),
                ('w', c_uint16)
            ]    
            
        _pack_ = 1
        _fields_ = [
            ('r8', _R8),
            ('r16', _R16)
        ]

    _pack_ = 1
    _fields_ = [
        ('r', _R),
        ('p', _P),
        ('q', c_uint32)
    ]


# m_pc = PAIR16()
# m_pc.b.h = 0xff
# m_pc.b.l = 0x77
# print(sys.byteorder)
# print('m_pc.w = 0x{:X}'.format(m_pc.w))
# print('m_pc.sw = {:d}'.format(m_pc.sw))

# m_q = M6809Q()
# m_q.p.d.w = 0xffaa
# print('m_q.p.d.b.h= 0x{:2X}'.format(m_q.p.d.b.h))
# print('m_q.p.d.b.l= 0x{:2X}'.format(m_q.p.d.b.l))

# CPU Registers
m_pc = PAIR16()
m_ppc = PAIR16()
m_q = M6809Q()
m_x = PAIR16()
m_y = PAIR16()
m_u = PAIR16()
m_s = PAIR16()
m_dp : int
m_cc : int
m_temp = PAIR16()
m_opcode : int

# Other internal state
m_reg8: int
m_reg16= PAIR16()
m_reg : int
m_nmi_line : bool
m_nmi_asserted : bool
m_firq_line : bool
m_irq_line : bool
m_lds_encountered : bool
m_icount : int
m_addressing_mode : int
m_ea = PAIR16()

class FLAGS(Enum):
    CC_C        = 0x01         # Carry
    CC_V        = 0x02         # Overflow
    CC_Z        = 0x04         # Zero
    CC_N        = 0x08         # Negative
    CC_I        = 0x10         # Inhibit IRQ
    CC_H        = 0x20         # Half (auxiliary) carry
    CC_F        = 0x40         # Inhibit FIRQ
    CC_E        = 0x80         # Entire state pushed

class FLGC(Enum):
    CC_VC   = FLAGS.CC_V.value | FLAGS.CC_C.value
    CC_ZC   = FLAGS.CC_Z.value | FLAGS.CC_C.value
    CC_NZ   = FLAGS.CC_N.value | FLAGS.CC_Z.value
    CC_NZC  = FLAGS.CC_N.value | FLAGS.CC_Z.value | FLAGS.CC_C.value
    CC_NZV  = FLAGS.CC_N.value | FLAGS.CC_Z.value | FLAGS.CC_V.value
    CC_NZVC = FLAGS.CC_N.value | FLAGS.CC_Z.value | FLAGS.CC_V.value | FLAGS.CC_C.value
    CC_HNZVC = FLAGS.CC_H.value | FLAGS.CC_N.value | FLAGS.CC_Z.value | FLAGS.CC_V.value | FLAGS.CC_C.value

print('0x{:X}'.format(FLGC.CC_HNZVC.value))
