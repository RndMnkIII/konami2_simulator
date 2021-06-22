from typing import NamedTuple
from enum import Enum

class Konami2_addr_mode(Enum):
	INH = 1          # Inherent
	PSHS = 2
	PSHU = 3         # Push
	PULS = 4
	PULU = 5         # Pull
	DIR = 6          # Direct
	DIR_IM = 7       # Direct in memory (6309 only)
	IND = 8          # Indexed
	REL = 9          # Relative (8 bit)
	LREL = 10        # Long relative (16 bit)
	EXT = 11         # Extended
	IMM = 12         # Immediate
	IMM_RR = 13      # Register-to-register	
	IMM_BW = 14      # Bitwise operations (6309 only)
	IMM_TFM = 15     # Transfer from memory (6309 only)
	PG1 = 16         # Switch to page 1 opcodes
	PG2 = 17         # Switch to page 2 opcodes

class OpcodeInfo(NamedTuple):
    opcode: int
    length: int
    name: str
    mode: Konami2_addr_mode


konami_opcodes = {
	 0x08: OpcodeInfo(0x08, 2, "LEAX", Konami2_addr_mode.IND)
}

opcode=0x08
print(konami_opcodes[opcode].mode)