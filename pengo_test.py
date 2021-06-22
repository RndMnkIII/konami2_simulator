from ctypes import Union, BigEndianStructure, Structure, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32, c_int, c_char_p, POINTER, pointer, create_string_buffer, addressof

class Tuint8(Structure):
    _pack_ = 1
    _fields_ = [
        ('val', c_uint8)
    ]

class Tint8(Structure):
    _pack_ = 1
    _fields_ = [
        ('val', c_int8)
    ]

class Tuint16(Structure):
    _pack_ = 1
    _fields_ = [
        ('val', c_uint16)
    ]

class Tint16(Structure):
    _pack_ = 1
    _fields_ = [
        ('val', c_int16)
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
            
        _pack_ = 1
        _fields_ = [
            ('r8', _R8),
            ('r16', _R16)
        ]

    _pack_ = 1
    _fields_ = [
        ('r', _R),
        ('p', _P),
        ('q', Tuint32)
    ]

class Pengo:
    name: str
    color: int

    def __init__(self, n: str, c: int)->None:
        self.name = n
        self.color = c

class CPengo(Structure):
    _fields_ = [
        ('name', c_char_p),
        ('color', PAIR16)
    ]

class PengoCol:
    p1: Pengo
    p2: Pengo

    def __init__(self, p1: Pengo, p2: Pengo)->None:
        self.p1 = p1
        self.p2 = p2

    def get_p1(self)-> Pengo:
        return self.p1

    def get_p2(self)-> Pengo:
        return self.p2


class CPengoCol:
    p1: CPengo
    p2: CPengo

    def __init__(self, p1: CPengo, p2: CPengo)->None:
        self.p1 = p1
        self.p2 = p2

    def get_cp1(self)-> CPengo:
        return self.p1

    def get_cp2(self)-> CPengo:
        return self.p2


p1 = Pengo("Azul", 1)
p2 = Pengo("Verde", 4)

p3 = p1
pc = PengoCol(p1, p2)

pc.get_p2()
print('*** Pengo colllection ***')
print(id(p1))
print(id(p2))
print(id(p3))

print(id(pc.get_p1()))
print(id(pc.get_p2()))


cp1 = CPengo(str.encode('Violeta'), PAIR16())
cp2 = CPengo(str.encode('Purpura'), PAIR16())
cp3 = cp1
cp1_color = cp1.color.w

cpc = CPengoCol(cp1, cp2)

print('*** CPengo colllection ***')
print(addressof(cp1))
print(addressof(cp2))
print(addressof(cp3))
print('--------------------------')
print(addressof(cp1.color.w))
print(addressof(cp1_color))
print('--------------------------')
print(addressof(cpc.get_cp1()))
print(addressof(cpc.get_cp2()))
