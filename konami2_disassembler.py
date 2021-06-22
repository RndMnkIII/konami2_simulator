# konami2_disassembler.py
# Konami-2 CPU disassembler based on MAME 
# 6x09dasm.cpp - a 6809/6309/Konami opcode disassembler
# by Nathan Woods,Sean Riddle,Tim Lindner

#from konami2_disassembler import OpcodesData, Konami2Disassembler
from typing import NamedTuple, Dict, List
from ctypes import c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32
import konami2_opcodes as k2op
from array import array
from io import StringIO

class OpcodesData(NamedTuple):
    addr: int
    data: int

class Konami2Disassembler:
    m6x09_btwregs = ( "CC", "A", "B", "inv" )

    hd6309_tfmregs = ("D",   "X",   "Y",   "U",   "S", "inv", "inv", "inv", "inv", "inv", "inv", "inv", "inv", "inv", "inv", "inv")

    tfm_s = ( "{}+,{}+", "{}-,{}-", "{}+,{}", "{},{}+")
    #private data of the class
    m_opcode = 0x00       # 8-bit opcode value
    m_length = 0x00       # Opcode length in bytes
    m_mode = k2op.Konami2_addr_mode.IMM     # Addressing mode
    m_level=0    # 0 (General), or  1 (6309 only)?
    m_flags = 0x0000      # Disassembly flags
    m_name = ''           # Opcode name

    def __init__(self) -> None:
        from memory_mapper import SELECTOR, memory_mapper

    #public interface
    def opcode(self) -> int:
        return m_opcode

    def length(self) -> int:
        return m_length

    def mode(self) -> k2op.Konami2_addr_mode:
        return m_mode

    def level(self) -> int:
        return m_level

    def flags(self) -> int:
        return m_flags

    def name(self) -> str:
        return m_name

    # def fetch_opcode(self,  pc: int, opcodes: Dict[int, k2op.OpcodeInfo], opcode_data:List[OpcodesData]) -> k2op.OpcodeInfo:
    #     return opcodes.get(opcode_data[pc].data) #return None is key is not found

    # def fetch_opcode(self,  pc: int, opcodes: Dict[int, k2op.OpcodeInfo], opcode_data:array) -> k2op.OpcodeInfo:
    #     return opcodes.get(opcode_data[pc]) #return None is key is not found
    def fetch_opcode(self,  pc: int, opcodes: Dict[int, k2op.OpcodeInfo], opcode_mem) -> k2op.OpcodeInfo:
        return opcodes.get(opcode_mem.read(pc)) #return None is key is not found

    #def disassembler(self, pc: int, stream: StringIO, opcode_data:array, opcode_mem: memory_mapper) -> int:
    def disassembler(self, pc: int, stream:StringIO, opcode_mem) -> int:
        pb = 0x00 #uint_8
        ea =0x0000 #unsigned int
        offset = 0 #int
        p  = 0 #uint32_t
        p = int(pc) #I use list as way of get a mutable integer

        #lookup opcode
        # op = self.fetch_opcode(p, k2op.konami_opcodes, opcode_data)
        op = self.fetch_opcode(p, k2op.konami_opcodes, opcode_mem)


        #increase pc always after fetch opcode
        p += 1

        if (op is not None):
            self.m_opcode = op.opcode
            self.m_name = op.name
            self.m_mode = op.mode
            self.m_length = op.length
            self.m_level = 0 #M6x09_GENERAL
            
        if(op is None):
            #Illegal opcode
            stream.write('{:<6}${:02X}'.format('FCB', opcode_mem.read(pc)))
            for q in range(pc+1, p):
                stream.write(',${:02X}'.format(opcode_mem.read(q)))

            return (p - int(pc))

        #How many operands do we have?
        numoperands = (op.length - 1) if ((p - int(pc)) == 1) else (op.length - 2)

        ppc = p #uint32_t
        p += numoperands

        #Output the base instruction name
        if(op.mode == k2op.Konami2_addr_mode.INH):
            stream.write(op.name)
        else:
            stream.write("{:<6}".format(op.name))    

        #SWITCH CASE emulated with if... elif ... elif ... else chain
        if(op.mode == k2op.Konami2_addr_mode.INH):
            pass

        elif(op.mode == k2op.Konami2_addr_mode.PSHS or op.mode == k2op.Konami2_addr_mode.PSHU):
            #this ensures that the value is unsigned 8 bits
            #pb = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
            pb = c_uint8(opcode_mem.read(ppc)).value

            if (pb & 0x80):
                stream.write('PC')
            if (pb & 0x40):
                stream.write('{}{}'.format( (',' if (pb & 0x80) else ''),('U' if (op.mode == k2op.Konami2_addr_mode.PSHS) else 'S')  ) )    
            if (pb & 0x20):
                stream.write('{}Y'.format(',' if (pb & 0xc0) else ''))
            if (pb & 0x10):
                stream.write('{}X'.format(',' if (pb & 0xe0) else ''))   
            if (pb & 0x08):
                stream.write('{}DP'.format(',' if (pb & 0xf0) else ''))     
            if (pb & 0x04):
                stream.write('{}B'.format(',' if (pb & 0xf8) else ''))
            if (pb & 0x02):
                stream.write('{}A'.format(',' if (pb & 0xfc) else ''))
            if (pb & 0x01):
                stream.write('{}CC'.format(',' if (pb & 0xfe) else ''))    
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.PULS or op.mode == k2op.Konami2_addr_mode.PULU):                                
            #this ensures that the value is unsigned 8 bits
            #pb = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
            pb = c_uint8(opcode_mem.read(ppc)).value

            if (pb & 0x01):
                stream.write('CC')
            if (pb & 0x02):
                stream.write('{}A'.format( ',' if (pb & 0x01) else ''))
            if (pb & 0x04):
                stream.write('{}B'.format( ',' if (pb & 0x03) else ''))
            if (pb & 0x08):
                stream.write('{}DP'.format( ',' if (pb & 0x07) else ''))
            if (pb & 0x10):
                stream.write('{}X'.format( ',' if (pb & 0x0f) else ''))   
            if (pb & 0x20):
                stream.write('{}Y'.format( ',' if (pb & 0x1f) else ''))
            if (pb & 0x40):
                stream.write('{}{}'.format(( ',' if (pb & 0x3f) else ''),('U' if (op.mode == k2op.Konami2_addr_mode.PSHS) else 'S')  ) ) 
            if (pb & 0x80):
                stream.write('{}PC'.format( ',' if (pb & 0x7f) else ''))
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.DIR):
            #this ensures that the value is unsigned 8 bits
            #ea = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
            ea = c_uint8(opcode_mem.read(ppc)).value
            stream.write('${:02X}'.format(ea))
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.DIR_IM):
            if(self.m_level < 1): #m_level < HD6309_EXCLUSIVE
                assert false, "Error: este modo de direccionamiento es exclusivo del HD6309 (DIR_IM)"
            stream.write('#${:02X};'.format(opcode_mem.read(ppc)))
            stream.write('#${:02X}'.format(opcode_mem.read(ppc + 1)))   
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.REL):   
            #this ensures that offset is SIGNED 8 bits
            #offset =  int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=True)
            offset = c_int8(opcode_mem.read(ppc)).value
            stream.write('${:04X}'.format((pc + op.length + offset) & 0xffff))
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.LREL):
            #this ensures that offset is SIGNED 16 bits
            #offset =  int.from_bytes(opcode_data[ppc:ppc+2].tobytes(), byteorder='big', signed=True)
            offset = c_int16(opcode_mem.read16(ppc)).value
            stream.write('${:04X}'.format((pc + op.length + offset) & 0xffff))
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.EXT):
            if(numoperands == 3):
                if(self.m_level < 1): #m_level < HD6309_EXCLUSIVE
                    assert false, "Error: este modo de direccionamiento es exclusivo del HD6309 (EXT 3operands)"
                #this ensures that the value is unsigned 8 bits
                #pb = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
                pb = c_uint8(opcode_mem.read(ppc)).value
                #this ensures that the value is unsigned 16 bits
                #ea = int.from_bytes(opcode_data[ppc:ppc+2].tobytes(), byteorder='big', signed=False)
                ea = c_uint16(opcode_mem.read16(ppc)).value
                stream.write('#${:02X},${:04X}'.format(pb, ea))
            elif(numoperands == 2):
                #this ensures that the value is unsigned 16 bits
                #ea = int.from_bytes(opcode_data[ppc:ppc+2].tobytes(), byteorder='big', signed=False)
                ea = c_uint16(opcode_mem.read16(ppc)).value
                if((ea & 0xff00) == 0):  # XXX NEED TO DEBUG THIS XXX, C++ expr is: if !(ea & 0xff00)
                    stream.write('>')
                stream.write('${:04X}'.format(ea))
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.IND):
            if(numoperands == 2):
                if(self.m_level < 1): #m_level < HD6309_EXCLUSIVE
                    assert false, "Error: este modo de direccionamiento es exclusivo del HD6309 (IND two operands)"
                stream.write('#${:02X};'.format(opcode_mem.read(ppc)))

                #this ensures that the value is unsigned 8 bits
                #pb = int.from_bytes(opcode_data[ppc+1:ppc+2].tobytes(), byteorder='big', signed=False)
                pb = c_uint8(opcode_mem.read(ppc)).value
            else:
                #this ensures that the value is unsigned 8 bits
                #pb = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
                pb = c_uint8(opcode_mem.read(ppc)).value
                p = self.indexed(stream, pb, opcode_mem, p) #returns modified value of p inside 'indexed' function
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.IMM):
            if (numoperands == 4):
                #ea is always an unsigned integer value
                #ea = int.from_bytes(opcode_data[ppc:ppc+4].tobytes(), byteorder='big', signed=False)
                ea = c_uint32(opcode_mem.read32(ppc)).value
                stream.write('#${:08X}'.format(ea))
            elif (numoperands == 2):
                #ea = int.from_bytes(opcode_data[ppc:ppc+2].tobytes(), byteorder='big', signed=False)
                ea = c_uint16(opcode_mem.read16(ppc)).value
                stream.write('#${:04X}'.format(ea))
            elif (numoperands == 1):
                #ea = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
                ea = c_uint8(opcode_mem.read(ppc)).value
                stream.write('#${:02X}'.format(ea))
            #BREAK

        elif(op.mode == k2op.Konami2_addr_mode.IMM_RR):
            #this ensures that the value is unsigned 8 bits
            #pb = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
            pb = c_uint8(opcode_mem.read(ppc)).value
            self.register_register(stream, pb)
            #BREAK
        elif(op.mode == k2op.Konami2_addr_mode.IMM_BW):
            #this ensures that the value is unsigned 8 bits
            #pb = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
            pb = c_uint8(opcode_mem.read(ppc)).value
            stream.write('{},'.format(self.m6x09_btwregs[((pb & 0xc0) >> 6)]))
            stream.write('{:d},'.format((pb & 0x38) >> 3))
            stream.write('{:d},'.format((pb & 0x07)))
            stream.write('${:02X}'.format(opcode_mem.read(ppc+1)))

        elif(op.mode == k2op.Konami2_addr_mode.IMM_TFM):
            #this ensures that the value is unsigned 8 bits
            #pb = int.from_bytes(opcode_data[ppc:ppc+1].tobytes(), byteorder='big', signed=False)
            pb = c_uint8(opcode_mem.read(ppc)).value
            stream.write(self.tfm_s[op.opcode & 0x07].format(self.hd6309_tfmregs[(pb >> 4) & 0xf],self.hd6309_tfmregs[pb & 0xf]))  
        else:
            assert false, "Error: modo de direccionamiento desconocido"  
        
        return (p - int(pc))

    def register_register(self, stream: StringIO, pb:int) -> None:
        konami_teregs = ('A', 'B', 'X', 'Y', 'S', 'U', '?', '?')
        stream.write('{},{}'.format(konami_teregs[(pb >> 0) & 0x7],	konami_teregs[(pb >> 4) & 0x7]))

    def indexed(self, stream: StringIO, mode: int, opcode_mem, p: int) -> int:
        #because p is passed by value, in the return value the function store
        #the modified valued of p inside the function.

        # 0 - extended mode
        # 4 - direct page
        # 7 - pc
        index_reg =("?", "?", "x", "y", "?", "u", "s", "pc")

        idx = (mode >> 4) & 0x07
        typeidx = mode & 0x0f
        val = 0

        #special modes:
        if(mode & 0x80):
            if(typeidx & 0x8):
                #indirect:

                #register a
                if ((typeidx & 0x7) == 0x00):
                    stream.write('[a,{}]'.format(index_reg[idx]))
                    #BREAK 

                #register b
                elif ((typeidx & 0x7) == 0x01):
                    stream.write('[b,{}]'.format(index_reg[idx]))
                    #BREAK 

                #direct - mode    
                elif ((typeidx & 0x7) == 0x04):
                    stream.write('[${:02X}]'.format(opcode_mem.read(p)))
                    p += 1
                    #BREAK 

                #register d
                elif ((typeidx & 0x7) == 0x07):
                    stream.write('[d,{}]'.format(index_reg[idx]))
                    #BREAK 

                #default
                else:
                    stream.write('[?,{}]'.format(index_reg[idx]))  
                    #BREAK
            else:
                #register a
                if ((typeidx & 0x7) == 0x00):
                    stream.write('a,{}'.format(index_reg[idx]))
                    #BREAK 

                #register b
                elif ((typeidx & 0x7) == 0x01):
                    stream.write('b,{}'.format(index_reg[idx]))
                    #BREAK 

                #direct - mode    
                elif ((typeidx & 0x7) == 0x04):
                    stream.write('${:02X}'.format(opcode_mem.read(p)))
                    p += 1
                    #BREAK 

                #register d
                elif ((typeidx & 0x7) == 0x07):
                    stream.write('d,{}'.format(index_reg[idx]))
                    #BREAK 

                #default
                else:
                    stream.write('????,{}'.format(index_reg[idx]))  
                    #BREAK
        else:
            if(typeidx & 0x8):

                #indirect

                #auto increment
                if ((typeidx & 0x7) == 0x00):
                    stream.write('[,{}+]'.format(index_reg[idx]))
                    #BREAK

                #auto double increment
                elif ((typeidx & 0x7) == 0x01):
                    stream.write('[,{}++]'.format(index_reg[idx]))
                    #BREAK
           
                #auto decrement
                elif ((typeidx & 0x7) == 0x02):
                    stream.write('[,-{}]'.format(index_reg[idx]))
                    #BREAK

                #auto double decrement
                elif ((typeidx & 0x7) == 0x03):
                    stream.write('[,--{}]'.format(index_reg[idx]))
                    #BREAK

                #post byte offset
                elif ((typeidx & 0x7) == 0x04):
                    #val = int.from_bytes(opcode_data[p:p+1].tobytes(), byteorder='big', signed=False)
                    val = c_uint8(opcode_mem.read(p)).value
                    p += 1

                    if (val & 0x80):
                        stream.write('[#$-{:02X},{}]'.format(0x100 - val, index_reg[idx]))
                    else:
                        stream.write('[#${:02X},{}]'.format(val, index_reg[idx]))                        
                    #BREAK

                #post word offset
                elif ((typeidx & 0x7) == 0x05):
                    #val = int.from_bytes(opcode_data[p:p+2].tobytes(), byteorder='big', signed=False)
                    val = c_uint16(opcode_mem.read16(p)).value
                    p += 2

                    if (val & 0x80):
                        stream.write('[#$-{:04X},{}]'.format(0x10000 - val, index_reg[idx]))
                    else:
                        stream.write('[#${:04X},{}]'.format(val, index_reg[idx]))                        
                    #BREAK  
                 
                #simple
                elif ((typeidx & 0x7) == 0x06):
                    stream.write('[,{}]'.format(index_reg[idx]))
                    #BREAK

                #extended
                elif ((typeidx & 0x7) == 0x07):
                    #val = int.from_bytes(opcode_data[p:p+2].tobytes(), byteorder='big', signed=False)
                    val = c_uint16(opcode_mem.read16(p)).value
                    p += 2

                    stream.write('[${:04X}]'.format(val))
                    #BREAK

                else:
                    assert False, "Error: IND: modo indirecto no reconcido"   

            else:
                #Non-Indirect Modes   

                #auto increment
                if ((typeidx & 0x7) == 0x00):
                    stream.write(',{}+'.format(index_reg[idx]))
                    #BREAK

                #auto double increment
                elif ((typeidx & 0x7) == 0x01):
                    stream.write(',{}++'.format(index_reg[idx]))
                    #BREAK
           
                #auto decrement
                elif ((typeidx & 0x7) == 0x02):
                    stream.write(',-{}'.format(index_reg[idx]))
                    #BREAK

                #auto double decrement
                elif ((typeidx & 0x7) == 0x03):
                    stream.write(',--{}'.format(index_reg[idx]))
                    #BREAK

                #post byte offset
                elif ((typeidx & 0x7) == 0x04):
                    #val = int.from_bytes(opcode_data[p:p+1].tobytes(), byteorder='big', signed=False)
                    val = c_uint8(opcode_mem.read(p)).value
                    p += 1

                    if (val & 0x80):
                        stream.write('#$-{:02X},{}'.format(0x100 - val, index_reg[idx]))
                    else:
                        stream.write('#${:02X},{}'.format(val, index_reg[idx]))                        
                    #BREAK

                #post word offset
                elif ((typeidx & 0x7) == 0x05):
                    #val = int.from_bytes(opcode_data[p:p+2].tobytes(), byteorder='big', signed=False)
                    val = c_uint16(opcode_mem.read16(p)).value
                    p += 2

                    if (val & 0x80):
                        stream.write('#$-{:04X},{}'.format(0x10000 - val, index_reg[idx]))
                    else:
                        stream.write('#${:04X},{}'.format(val, index_reg[idx]))                        
                    #BREAK  
                 
                #simple
                elif ((typeidx & 0x7) == 0x06):
                    stream.write(',{}'.format(index_reg[idx]))
                    #BREAK

                #extended
                elif ((typeidx & 0x7) == 0x07):
                    #val = int.from_bytes(opcode_data[p:p+2].tobytes(), byteorder='big', signed=False)
                    val = c_uint16(opcode_mem.read16(p)).value
                    p += 2

                    stream.write('${:04X}'.format(val))
                    #BREAK

                else:
                    assert False, "Error: IND: modo no-indirecto no reconcido"                 
        return p
