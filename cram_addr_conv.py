from ctypes import c_uint16, c_uint8
from random import randint, seed


### CRAM memory banks init ###
valor:c_uint8=0
cram = []
for i in range(0,0x400):
    cram.append(valor)

cram_e14 = []
for i in range(0,0x200):
    cram_e14.append(valor)

cram_e15 = []
for i in range(0,0x200):
    cram_e15.append(valor)

def cram_write(addr: c_uint16, data: c_uint8) -> c_uint16:
    bank = addr & 0x1 #A0=0 even addr, data store in e15 (upper),else A0=1 odd addr stored in e14
    new_addr:c_uint16 = 0
    if (bank==0):
        new_addr |= (addr & 0x2)        #A1 -> A1 
        new_addr |= ((addr & 0x4)<<2)   #A2 -> A4
        new_addr |= ((addr & 0x8)>>1)   #A3 -> A2
        new_addr |= ((addr & 0x10)>>1)   #A4 -> A3
        new_addr |= ((addr & 0x20)<<3)   #A5 -> A8
        new_addr |= ((addr & 0x40)<<1)   #A6 -> A7
        new_addr |= ((addr & 0x80)>>1)   #A7 -> A6
        new_addr |= ((addr & 0x100)>>8)   #A8 -> A0
        new_addr |= ((addr & 0x200)>>4)   #A9 -> A5
        cram_e15[new_addr] = data
        return new_addr
    else:
        new_addr |= (addr & 0x2)        #A1 -> A1 
        new_addr |= ((addr & 0x4)<<2)   #A2 -> A4
        new_addr |= ((addr & 0x8)>>1)   #A3 -> A2
        new_addr |= ((addr & 0x10)>>1)   #A4 -> A3
        new_addr |= ((addr & 0x20)<<2)   #A5 -> A7
        new_addr |= ((addr & 0x40)<<2)   #A6 -> A8
        new_addr |= ((addr & 0x80)>>1)   #A7 -> A6
        new_addr |= ((addr & 0x100)>>8)   #A8 -> A0
        new_addr |= ((addr & 0x200)>>4)   #A9 -> A5
        cram_e14[new_addr] = data
        return new_addr

def cram_read(addr: c_uint16) -> c_uint8:        
    bank = addr & 0x1 #A0=0 even addr, data store in e15 (upper),else A0=1 odd addr stored in e14
    new_addr:c_uint16 = 0
    if (bank==0):
        new_addr |= (addr & 0x2)        #A1 -> A1 
        new_addr |= ((addr & 0x4)<<2)   #A2 -> A4
        new_addr |= ((addr & 0x8)>>1)   #A3 -> A2
        new_addr |= ((addr & 0x10)>>1)   #A4 -> A3
        new_addr |= ((addr & 0x20)<<3)   #A5 -> A8
        new_addr |= ((addr & 0x40)<<1)   #A6 -> A7
        new_addr |= ((addr & 0x80)>>1)   #A7 -> A6
        new_addr |= ((addr & 0x100)>>8)   #A8 -> A0
        new_addr |= ((addr & 0x200)>>4)   #A9 -> A5
        return cram_e15[new_addr]
    else:
        new_addr |= (addr & 0x2)        #A1 -> A1 
        new_addr |= ((addr & 0x4)<<2)   #A2 -> A4
        new_addr |= ((addr & 0x8)>>1)   #A3 -> A2
        new_addr |= ((addr & 0x10)>>1)   #A4 -> A3
        new_addr |= ((addr & 0x20)<<2)   #A5 -> A7
        new_addr |= ((addr & 0x40)<<2)   #A6 -> A8
        new_addr |= ((addr & 0x80)>>1)   #A7 -> A6
        new_addr |= ((addr & 0x100)>>8)   #A8 -> A0
        new_addr |= ((addr & 0x200)>>4)   #A9 -> A5
        return cram_e14[new_addr]

if __name__ == "__main__":
    #write random byte values to the RAM
    seed(1234)
    for i in range (0x400):
        valor = randint(0,255)
        new_addr=cram_write(addr=i, data=valor)
        print(f"{i:03X} -> {new_addr:03X}: {valor:02X}")
        cram[i] = valor

    print("*** CRAM E15,E14                                    ****** RAM ***")
    for i in range(0x0, 0x400, 16):
        print(f"{i:03X}: ", end='')
        for j in range (0, 16):
            print(f"{cram_read(addr=i+j):02X} ", end='')
        print("    ", end='')

        print(f"{i:03X}: ", end='')
        for j in range (0, 16):
            print(f"{cram[i+j]:02X} ", end='')
        print()        


    