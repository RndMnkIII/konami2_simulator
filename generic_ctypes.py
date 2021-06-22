from typing import TypeVar, Type
from ctypes import  Structure, sizeof, c_ubyte, c_byte, c_ushort, c_short, c_uint, c_int, c_ulong, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32, c_long, c_ulong


class Tuint8(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_uint8)
    ]

class Tuint16(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_uint16)
    ]    

class Tuint32(Structure):
    _pack_ = 1
    _fields_ = [
        ('value', c_uint32)
    ] 

T = TypeVar('T',Tuint8, Tuint16, Tuint32)

def set_flags(a: T) -> T:
    clase = type(a)
    b = clase()
    b.value=11
    return _set_flags(member_class = type(a), a=a, b=b)

def _set_flags(member_class: Type[T], a: T, b: T) -> T:

    print(f"_set_flags: b.value= {b.value:X}")
    
    hi_bit = member_class()
    hi_bit.value =  (1 << (sizeof(hi_bit)*8-1))

    if(isinstance(hi_bit, Tuint16)):
        print('hi_bit is instance of Tuint16')    
    elif(isinstance(hi_bit, Tuint8)):
        print('hi_bit is instance of Tuint8')
    elif(isinstance(hi_bit, c_uint8)):
        print('hi_bit is instance of c_uint8')    
    tam = sizeof(hi_bit)
    print("set_flags:", type(hi_bit), tam)
    print("set_flags:", type(b))

    return hi_bit

#valor = Tuint8(0xff)
valor = Tuint32(0xffffaabb)

c = set_flags(valor)
print(f"{c.value:02X}")
print(type(c))
print(sizeof(c))

d = c_uint16(0xffaa)
e = Tuint8()
e.value = d

>>> a = (c_byte * 4)()
>>> cast(e, POINTER(c_uint8))
print(f"d={d:04X} e={e:02X}")

