#Little-endian version of m6809_regs
# The C++ structure and union manipulation using pointers
# it is replicated in python using the cpython module
# to get the address of a sub-structure in python use the ctypes
# function addressof(ctypes_obj) instead of the incorporated python function id(obj)

# The MC6x09 CPU family is big-endian
#   MSB                                 LSB
#   --------- --------- --------- ---------
#  |    A    |    B    |    E    |    F    |
#   --------- --------- --------- ---------
#   7       0 7       0 7       0 7       0
#
#   ------------------- -------------------
#  |         D         |         W         |
#   ------------------- ------------------- 
#  15                 0 15                 0
#
#   ---------------------------------------
#  |                   Q                   |
#   ---------------------------------------
#  31                                      0
#                       
#  E,F,W,Q are 6309 EXCLUSIVE REGS
#
#   MSB             LSB
#   15                0
#   -------------------
#  |  X hi   |  X lo   |
#   -------------------
#  |  Y hi   |  Y lo   |
#   -------------------
#  | SP hi   | SP lo   |
#   -------------------
#  |  U hi   |  U lo   |
#   -------------------
#  | PC hi   | PC lo   |
#   -------------------

from ctypes import Union, Structure, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32, POINTER, pointer, addressof

class Tuint8(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_uint8)
    ]

class Tint8(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_int8)
    ]

class Tuint16(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_uint16)
    ]

class Tint16(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_int16)
    ]

class Tuint32(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_uint32)
    ]

class Tint32(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_int32)
    ]   

class PAIR(Union):
    class _B32(Structure):
        _pack_ = 1
        _fields_ = [
            ('l',  Tuint8),
            ('h',  Tuint8),
            ('h2',  Tuint8),
            ('h3',  Tuint8)
        ]

    class _SB32(Structure):
        _pack_ = 1 
        _fields_ = [
            ('l',  Tint8),
            ('h',  Tint8),
            ('h2',  Tint8),
            ('h3',  Tint8)
        ]

    class _W32(Structure):
        _pack_ = 1
        _fields_ = [
            ('l',  Tuint16),
            ('h',  Tuint16)
            ]

    class _SW32(Structure):
        _pack_ = 1
        _fields_ = [
            ('l',  Tint16),
            ('h',  Tint16)
            ]     

    _pack_ = 1
    _fields_ = [
        ('b', _B32),
        ('w', _W32),
        ('sb', _SB32),
        ('sw', _SW32),
        ('d', Tuint32),
        ('sd', Tint32)
    ]

class PAIR16(Union):
    class _B(Structure):
        _pack_ = 1
        _fields_ = [
            ('l',  Tuint8),
            ('h',  Tuint8)
        ]

    class _SB(Structure):
        _pack_ = 1 
        _fields_ = [
            ('l', Tint8),
            ('h', Tint8)
        ]

    _pack_ = 1
    _fields_ = [
        ('b', _B),
        ('sb', _SB),
        ('w', Tuint16),
        ('sw', Tint16)
    ]

class M6809Q(Union):
    class _P(Structure):
        _pack_ = 1
        _fields_ = [
            ('w',  PAIR16),
            ('d',  PAIR16)
        ]

    class _R(Union):
        class _R8(Structure):
            _pack_ = 1
            _fields_ = [
                ('f', Tuint8),
                ('e', Tuint8),
                ('b', Tuint8),
                ('a', Tuint8)
            ]

        class _R16(Structure):
            _pack_ = 1
            _fields_ = [
                ('w', Tuint16),
                ('d', Tuint16)
            ]

        class _SR8(Structure):
            _pack_ = 1
            _fields_ = [
                ('f', Tint8),
                ('e', Tint8),
                ('b', Tint8),
                ('a', Tint8)
            ]

        class _SR16(Structure):
            _pack_ = 1
            _fields_ = [
                ('w', Tint16),
                ('d', Tint16)
            ]             
            
        _pack_ = 1
        _fields_ = [
            ('r8', _R8),
            ('r16', _R16),
            ('sr8', _SR8),
            ('sr16', _SR16)
        ]

    _pack_ = 1
    _fields_ = [
        ('r', _R),
        ('p', _P),
        ('q', Tuint32)
    ]


#Important example testing add/substracting signed value to unsigned value to apply an offset in address
# m_temp = PAIR16()
# m_temp.sb.l.value = -16
# print(f"byte value temp:{m_temp.b.l.value}")
# print(f"byte value temp: 0x{m_temp.b.l.value:02X}")
# print(f"signed byte value temp:{m_temp.sb.l.value}")
# print(f"signed byte value temp:{m_temp.sb.l.value:02X}")
# m_ea = PAIR16()
# m_ea.w.value = 0x8000
# m_ea.w.value += m_temp.sb.l.value
# print(f"effective address value:{m_ea.w.value}")
# print(f"effective address value: 0x{m_ea.w.value:04X}")

# #asignar a un unsigned mismo valor negado
# m_temp.b.l.value =32
# m_temp.b.l.value = -m_temp.b.l.value
# print('----')
# print(m_temp.b.l.value)
# print(m_temp.sb.l.value)

# print (f"{0x01 ^ 0xFFFF:04X}")
# print (f"{0x81 & (0x01 ^ 0xFFFF):04X}")
# var =  M6809Q()
# var.r.r8.a.value = 0xf2
# print(f"{var.r.r8.a.value}")
# print(f"{var.r.sr8.a.value}")