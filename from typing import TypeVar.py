from typing import TypeVar, Type
from ctypes import  c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32, c_long, c_ulong

T = TypeVar('T')      # Declare type variable

def set_flags(a: T) -> T:
    print(type(a))
    b = Type[T]
    print(type(a))
    b.value= a.value + 1
    print(b.value)
    return b

c = set_flags(c_uint8(0xfa))
print(c.value)
c = set_flags(c_int8(0xfa))
print(c.value)
c = set_flags(c_uint16(0xfa))
print(c.value)
c = set_flags(c_int16(0xfa))
print(c.value)
c = set_flags(c_uint32(0xfa))
print(c.value)
c = set_flags(c_int32(0xfa))
print(c.value)
c = set_flags(c_ulong(0xfa))
print(c.value)
c = set_flags(c_long(0xfa))
print(c.value)