from ctypes import Union, BigEndianStructure, Structure, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32, POINTER, pointer, addressof

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

class Tuint32(Structure):
    _pack_ = 1
    _fields_ = [
        ('val', c_uint32)
    ]

class Tint32(Structure):
    _pack_ = 1
    _fields_ = [
        ('val', c_int32)
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

class Regop:
    m_reg8 : Tuint8 = None
    m_reg8Id : int = 0
    m_reg16 : PAIR16 = None
    m_reg16Id : int = 0
    
    def set_regop8(self, reg:Tuint8) -> None:
        self.m_reg8 = reg
        self.m_reg8Id = addressof(reg)
        self.m_reg16 = None
        self.m_reg16Id = 0

    def set_regop16(self, reg:PAIR16) -> None:
        self.m_reg16 = reg
        self.m_reg16Id = addressof(reg)
        self.m_reg8 = None
        self.m_reg8Id = 0

    def regop8(self) -> Tuint8:
        assert ( self.m_reg8 is not None), 'regop8(): no debe ser nulo'
        return self.m_reg8

    def regop8id(self) -> int:
        return self.m_reg8Id  

    def regop16(self) -> PAIR16:
        assert ( self.m_reg16 is not None), 'regop16(): no debe ser nulo'
        return self.m_reg16

    def regop16id(self) -> int:
        return self.m_reg16Id

regop = Regop()
regs = M6809Q()
regs.r.r8.a.val = 0x01
regs.r.r8.b.val = 0x00
#print(regs.r.r16.d.val)
#print(regs.p.d.w.val)

# m_reg8 = pointer(regs.r.r8.a)
# print(m_reg8.contents.val)
# regs.r.r8.a.val = 0x02
# # print(regs.r.r16.d.val)
# print(m_reg8.contents.val)

# print(type(m_reg8.contents))
# print(type(regs.r.r8.a))
# print(id(m_reg8.contents))
# print(id(regs.r.r8.a))
regop.set_regop8(regs.r.r8.a)
print(regop.regop8().val)
regs.r.r8.a.val = 0x02
# print(regs.r.r16.d.val)
print(regop.regop8().val)

print('*** type and id ***')
print(type(regop.regop8()))
print(type(regs.r.r8.a))
print(regop.regop8id())
print(addressof(regs.r.r8.a))
print('******************')



#m_reg8 = pointer()
# CPU Registers
m_pc = PAIR16()
m_ppc = PAIR16()
m_q = M6809Q()
m_x = PAIR16()
m_y = PAIR16()
m_u = PAIR16()
m_s = PAIR16()
m_dp = c_uint8()
m_cc = c_uint8()
m_temp = PAIR16()
m_opcode = c_uint8()

m_pc.w.val=-1
regop.set_regop16(m_pc.w)
print(regop.regop16().val)
m_pc.w.val+=2
print(regop.regop16().val)