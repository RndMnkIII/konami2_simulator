# konami2_opcodes.py
# Konami-2 CPU opcode data structures used to
# disassembly the captured code
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
	0x08: OpcodeInfo(0x08, 2, "LEAX", Konami2_addr_mode.IND),
	0x09: OpcodeInfo(0x09, 2, "LEAY", Konami2_addr_mode.IND),
	0x0A: OpcodeInfo(0x0A, 2, "LEAU", Konami2_addr_mode.IND),
	0x0B: OpcodeInfo(0x0B, 2, "LEAS", Konami2_addr_mode.IND),
	0x0C: OpcodeInfo(0x0C, 2, "PUSHS",  Konami2_addr_mode.PSHS),
	0x0D: OpcodeInfo(0x0D, 2, "PUSHU",  Konami2_addr_mode.PSHU),
	0x0E: OpcodeInfo(0x0E, 2, "PULLS",  Konami2_addr_mode.PULS),
	0x0F: OpcodeInfo(0x0F, 2, "PULLU",  Konami2_addr_mode.PULU),
	0x10: OpcodeInfo(0x10, 2, "LDA",   Konami2_addr_mode.IMM),
	0x11: OpcodeInfo(0x11, 2, "LDB",   Konami2_addr_mode.IMM),
	0x12: OpcodeInfo(0x12, 2, "LDA",   Konami2_addr_mode.IND),
	0x13: OpcodeInfo(0x13, 2, "LDB",   Konami2_addr_mode.IND),
	0x14: OpcodeInfo(0x14, 2, "ADDA",  Konami2_addr_mode.IMM),
	0x15: OpcodeInfo(0x15, 2, "ADDB",  Konami2_addr_mode.IMM),
	0x16: OpcodeInfo(0x16, 2, "ADDA",  Konami2_addr_mode.IND),
	0x17: OpcodeInfo(0x17, 2, "ADDB",  Konami2_addr_mode.IND),
	0x18: OpcodeInfo(0x18, 2, "ADCA",  Konami2_addr_mode.IMM),
	0x19: OpcodeInfo(0x19, 2, "ADCB",  Konami2_addr_mode.IMM),
	0x1A: OpcodeInfo(0x1A, 2, "ADCA",  Konami2_addr_mode.IND),
	0x1B: OpcodeInfo(0x1B, 2, "ADCB",  Konami2_addr_mode.IND),
	0x1C: OpcodeInfo(0x1C, 2, "SUBA",  Konami2_addr_mode.IMM),
	0x1D: OpcodeInfo(0x1D, 2, "SUBB",  Konami2_addr_mode.IMM),
	0x1E: OpcodeInfo(0x1E, 2, "SUBA",  Konami2_addr_mode.IND),
	0x1F: OpcodeInfo(0x1F, 2, "SUBB",  Konami2_addr_mode.IND),

	0x20: OpcodeInfo(0x20, 2, "SBCA",  Konami2_addr_mode.IMM),
	0x21: OpcodeInfo(0x21, 2, "SBCB",  Konami2_addr_mode.IMM),
	0x22: OpcodeInfo(0x22, 2, "SBCA",  Konami2_addr_mode.IND),
	0x23: OpcodeInfo(0x23, 2, "SBCB",  Konami2_addr_mode.IND),
	0x24: OpcodeInfo(0x24, 2, "ANDA",  Konami2_addr_mode.IMM),
	0x25: OpcodeInfo(0x25, 2, "ANDB",  Konami2_addr_mode.IMM),
	0x26: OpcodeInfo(0x26, 2, "ANDA",  Konami2_addr_mode.IND),
	0x27: OpcodeInfo(0x27, 2, "ANDB",  Konami2_addr_mode.IND),
	0x28: OpcodeInfo(0x28, 2, "BITA",  Konami2_addr_mode.IMM),
	0x29: OpcodeInfo(0x29, 2, "BITB",  Konami2_addr_mode.IMM),
	0x2A: OpcodeInfo(0x2A, 2, "BITA",  Konami2_addr_mode.IND),
	0x2B: OpcodeInfo(0x2B, 2, "BITB",  Konami2_addr_mode.IND),
	0x2C: OpcodeInfo(0x2C, 2, "EORA",  Konami2_addr_mode.IMM),
	0x2D: OpcodeInfo(0x2D, 2, "EORB",  Konami2_addr_mode.IMM),
	0x2E: OpcodeInfo(0x2E, 2, "EORA",  Konami2_addr_mode.IND),
	0x2F: OpcodeInfo(0x2F, 2, "EORB",  Konami2_addr_mode.IND),

	0x30: OpcodeInfo(0x30, 2, "ORA",   Konami2_addr_mode.IMM),
	0x31: OpcodeInfo(0x31, 2, "ORB",   Konami2_addr_mode.IMM),
	0x32: OpcodeInfo(0x32, 2, "ORA",   Konami2_addr_mode.IND),
	0x33: OpcodeInfo(0x33, 2, "ORB",   Konami2_addr_mode.IND),
	0x34: OpcodeInfo(0x34, 2, "CMPA",  Konami2_addr_mode.IMM),
	0x35: OpcodeInfo(0x35, 2, "CMPB",  Konami2_addr_mode.IMM),
	0x36: OpcodeInfo(0x36, 2, "CMPA",  Konami2_addr_mode.IND),
	0x37: OpcodeInfo(0x37, 2, "CMPB",  Konami2_addr_mode.IND),
	0x38: OpcodeInfo(0x38, 2, "SETLINES",  Konami2_addr_mode.IMM),
	0x39: OpcodeInfo(0x39, 2, "SETLINES",  Konami2_addr_mode.IND),
	0x3A: OpcodeInfo(0x3A, 2, "STA",   Konami2_addr_mode.IND),
	0x3B: OpcodeInfo(0x3B, 2, "STB",   Konami2_addr_mode.IND),
	0x3C: OpcodeInfo(0x3C, 2, "ANDCC", Konami2_addr_mode.IMM),
	0x3D: OpcodeInfo(0x3D, 2, "ORCC",  Konami2_addr_mode.IMM),
	0x3E: OpcodeInfo(0x3E, 2, "EXG",   Konami2_addr_mode.IMM_RR),
	0x3F: OpcodeInfo(0x3F, 2, "TFR",   Konami2_addr_mode.IMM_RR),

	0x40: OpcodeInfo(0x40, 3, "LDD",   Konami2_addr_mode.IMM),
	0x41: OpcodeInfo(0x41, 2, "LDD",   Konami2_addr_mode.IND),
	0x42: OpcodeInfo(0x42, 3, "LDX",   Konami2_addr_mode.IMM),
	0x43: OpcodeInfo(0x43, 2, "LDX",   Konami2_addr_mode.IND),
	0x44: OpcodeInfo(0x44, 3, "LDY",   Konami2_addr_mode.IMM),
	0x45: OpcodeInfo(0x45, 2, "LDY",   Konami2_addr_mode.IND),
	0x46: OpcodeInfo(0x46, 3, "LDU",   Konami2_addr_mode.IMM),
	0x47: OpcodeInfo(0x47, 2, "LDU",   Konami2_addr_mode.IND),
	0x48: OpcodeInfo(0x48, 3, "LDS",   Konami2_addr_mode.IMM),
	0x49: OpcodeInfo(0x49, 2, "LDS",   Konami2_addr_mode.IND),
	0x4A: OpcodeInfo(0x4A, 3, "CMPD",  Konami2_addr_mode.IMM),
	0x4B: OpcodeInfo(0x4B, 2, "CMPD",  Konami2_addr_mode.IND),
	0x4C: OpcodeInfo(0x4C, 3, "CMPX",  Konami2_addr_mode.IMM),
	0x4D: OpcodeInfo(0x4D, 2, "CMPX",  Konami2_addr_mode.IND),
	0x4E: OpcodeInfo(0x4E, 3, "CMPY",  Konami2_addr_mode.IMM),
	0x4F: OpcodeInfo(0x4F, 2, "CMPY",  Konami2_addr_mode.IND),

	0x50: OpcodeInfo(0x50, 3, "CMPU",  Konami2_addr_mode.IMM),
	0x51: OpcodeInfo(0x51, 2, "CMPU",  Konami2_addr_mode.IND),
	0x52: OpcodeInfo(0x52, 3, "CMPS",  Konami2_addr_mode.IMM),
	0x53: OpcodeInfo(0x53, 2, "CMPS",  Konami2_addr_mode.IND),
	0x54: OpcodeInfo(0x54, 3, "ADDD",  Konami2_addr_mode.IMM),
	0x55: OpcodeInfo(0x55, 2, "ADDD",  Konami2_addr_mode.IND),
	0x56: OpcodeInfo(0x56, 3, "SUBD",  Konami2_addr_mode.IMM),
	0x57: OpcodeInfo(0x57, 2, "SUBD",  Konami2_addr_mode.IND),
	0x58: OpcodeInfo(0x58, 2, "STD",   Konami2_addr_mode.IND),
	0x59: OpcodeInfo(0x59, 2, "STX",   Konami2_addr_mode.IND),
	0x5A: OpcodeInfo(0x5A, 2, "STY",   Konami2_addr_mode.IND),
	0x5B: OpcodeInfo(0x5B, 2, "STU",   Konami2_addr_mode.IND),
	0x5C: OpcodeInfo(0x5C, 2, "STS",   Konami2_addr_mode.IND),

	0x60: OpcodeInfo(0x60, 2, "BRA",   Konami2_addr_mode.REL),
	0x61: OpcodeInfo(0x61, 2, "BHI",   Konami2_addr_mode.REL),
	0x62: OpcodeInfo(0x62, 2, "BCC",   Konami2_addr_mode.REL),
	0x63: OpcodeInfo(0x63, 2, "BNE",   Konami2_addr_mode.REL),
	0x64: OpcodeInfo(0x64, 2, "BVC",   Konami2_addr_mode.REL),
	0x65: OpcodeInfo(0x65, 2, "BPL",   Konami2_addr_mode.REL),
	0x66: OpcodeInfo(0x66, 2, "BGE",   Konami2_addr_mode.REL),
	0x67: OpcodeInfo(0x67, 2, "BGT",   Konami2_addr_mode.REL),
	0x68: OpcodeInfo(0x68, 3, "LBRA",  Konami2_addr_mode.LREL),
	0x69: OpcodeInfo(0x69, 3, "LBHI",  Konami2_addr_mode.LREL),
	0x6A: OpcodeInfo(0x6A, 3, "LBCC",  Konami2_addr_mode.LREL),
	0x6B: OpcodeInfo(0x6B, 3, "LBNE",  Konami2_addr_mode.LREL),
	0x6C: OpcodeInfo(0x6C, 3, "LBVC",  Konami2_addr_mode.LREL),
	0x6D: OpcodeInfo(0x6D, 3, "LBPL",  Konami2_addr_mode.LREL),
	0x6E: OpcodeInfo(0x6E, 3, "LBGE",  Konami2_addr_mode.LREL),
	0x6F: OpcodeInfo(0x6F, 3, "LBGT",  Konami2_addr_mode.LREL),

	0x70: OpcodeInfo(0x70, 2, "BRN",   Konami2_addr_mode.REL),
	0x71: OpcodeInfo(0x71, 2, "BLS",   Konami2_addr_mode.REL),
	0x72: OpcodeInfo(0x72, 2, "BCS",   Konami2_addr_mode.REL),
	0x73: OpcodeInfo(0x73, 2, "BEQ",   Konami2_addr_mode.REL),
	0x74: OpcodeInfo(0x74, 2, "BVS",   Konami2_addr_mode.REL),
	0x75: OpcodeInfo(0x75, 2, "BMI",   Konami2_addr_mode.REL),
	0x76: OpcodeInfo(0x76, 2, "BLT",   Konami2_addr_mode.REL),
	0x77: OpcodeInfo(0x77, 2, "BLE",   Konami2_addr_mode.REL),
	0x78: OpcodeInfo(0x78, 3, "LBRN",  Konami2_addr_mode.LREL),
	0x79: OpcodeInfo(0x79, 3, "LBLS",  Konami2_addr_mode.LREL),
	0x7A: OpcodeInfo(0x7A, 3, "LBCS",  Konami2_addr_mode.LREL),
	0x7B: OpcodeInfo(0x7B, 3, "LBEQ",  Konami2_addr_mode.LREL),
	0x7C: OpcodeInfo(0x7C, 3, "LBVS",  Konami2_addr_mode.LREL),
	0x7D: OpcodeInfo(0x7D, 3, "LBMI",  Konami2_addr_mode.LREL),
	0x7E: OpcodeInfo(0x7E, 3, "LBLT",  Konami2_addr_mode.LREL),
	0x7F: OpcodeInfo(0x7F, 3, "LBLE",  Konami2_addr_mode.LREL),

	0x80: OpcodeInfo(0x80, 1, "CLRA",  Konami2_addr_mode.INH),
	0x81: OpcodeInfo(0x81, 1, "CLRB",  Konami2_addr_mode.INH),
	0x82: OpcodeInfo(0x82, 2, "CLR",   Konami2_addr_mode.IND),
	0x83: OpcodeInfo(0x83, 1, "COMA",  Konami2_addr_mode.INH),
	0x84: OpcodeInfo(0x84, 1, "COMB",  Konami2_addr_mode.INH),
	0x85: OpcodeInfo(0x85, 2, "COM",   Konami2_addr_mode.IND),
	0x86: OpcodeInfo(0x86, 1, "NEGA",  Konami2_addr_mode.INH),
	0x87: OpcodeInfo(0x87, 1, "NEGB",  Konami2_addr_mode.INH),
	0x88: OpcodeInfo(0x88, 2, "NEG",   Konami2_addr_mode.IND),
	0x89: OpcodeInfo(0x89, 1, "INCA",  Konami2_addr_mode.INH),
	0x8A: OpcodeInfo(0x8A, 1, "INCB",  Konami2_addr_mode.INH),
	0x8B: OpcodeInfo(0x8B, 2, "INC",   Konami2_addr_mode.IND),
	0x8C: OpcodeInfo(0x8C, 1, "DECA",  Konami2_addr_mode.INH),
	0x8D: OpcodeInfo(0x8D, 1, "DECB",  Konami2_addr_mode.INH),
	0x8E: OpcodeInfo(0x8E, 2, "DEC",   Konami2_addr_mode.IND),
	0x8F: OpcodeInfo(0x8F, 1, "RTS",   Konami2_addr_mode.INH),

	0x90: OpcodeInfo(0x90, 1, "TSTA",  Konami2_addr_mode.INH),
	0x91: OpcodeInfo(0x91, 1, "TSTB",  Konami2_addr_mode.INH),
	0x92: OpcodeInfo(0x92, 2, "TST",   Konami2_addr_mode.IND),
	0x93: OpcodeInfo(0x93, 1, "LSRA",  Konami2_addr_mode.INH),
	0x94: OpcodeInfo(0x94, 1, "LSRB",  Konami2_addr_mode.INH),
	0x95: OpcodeInfo(0x95, 2, "LSR",   Konami2_addr_mode.IND),
	0x96: OpcodeInfo(0x96, 1, "RORA",  Konami2_addr_mode.INH),
	0x97: OpcodeInfo(0x97, 1, "RORB",  Konami2_addr_mode.INH),
	0x98: OpcodeInfo(0x98, 2, "ROR",   Konami2_addr_mode.IND),
	0x99: OpcodeInfo(0x99, 1, "ASRA",  Konami2_addr_mode.INH),
	0x9A: OpcodeInfo(0x9A, 1, "ASRB",  Konami2_addr_mode.INH),
	0x9B: OpcodeInfo(0x9B, 2, "ASR",   Konami2_addr_mode.IND),
	0x9C: OpcodeInfo(0x9C, 1, "ASLA",  Konami2_addr_mode.INH),
	0x9D: OpcodeInfo(0x9D, 1, "ASLB",  Konami2_addr_mode.INH),
	0x9E: OpcodeInfo(0x9E, 2, "ASL",   Konami2_addr_mode.IND),
	0x9F: OpcodeInfo(0x9F, 1, "RTI",   Konami2_addr_mode.INH),

	0xA0: OpcodeInfo(0xA0, 1, "ROLA",  Konami2_addr_mode.INH),
	0xA1: OpcodeInfo(0xA1, 1, "ROLB",  Konami2_addr_mode.INH),
	0xA2: OpcodeInfo(0xA2, 2, "ROL",   Konami2_addr_mode.IND),
	0xA3: OpcodeInfo(0xA3, 2, "LSRW",  Konami2_addr_mode.IND),
	0xA4: OpcodeInfo(0xA4, 2, "RORW",  Konami2_addr_mode.IND),
	0xA5: OpcodeInfo(0xA5, 2, "ASRW",  Konami2_addr_mode.IND),
	0xA6: OpcodeInfo(0xA6, 2, "ASLW",  Konami2_addr_mode.IND),
	0xA7: OpcodeInfo(0xA7, 2, "ROLW",  Konami2_addr_mode.IND),
	0xA8: OpcodeInfo(0xA8, 2, "JMP",   Konami2_addr_mode.IND),
	0xA9: OpcodeInfo(0xA9, 2, "JSR",   Konami2_addr_mode.IND),
	0xAA: OpcodeInfo(0xAA, 2, "BSR",   Konami2_addr_mode.REL),
	0xAB: OpcodeInfo(0xAB, 3, "LBSR",  Konami2_addr_mode.LREL),
	0xAC: OpcodeInfo(0xAC, 2, "DECB,JNZ",   Konami2_addr_mode.REL),
	0xAD: OpcodeInfo(0xAD, 2, "DECX,JNZ",   Konami2_addr_mode.REL),
	0xAE: OpcodeInfo(0xAE, 1, "NOP",   Konami2_addr_mode.INH),

	0xB0: OpcodeInfo(0xB0, 1, "ABX",   Konami2_addr_mode.INH),
	0xB1: OpcodeInfo(0xB1, 1, "DAA",   Konami2_addr_mode.INH),
	0xB2: OpcodeInfo(0xB2, 1, "SEX",   Konami2_addr_mode.INH),
	0xB3: OpcodeInfo(0xB3, 1, "MUL",   Konami2_addr_mode.INH),
	0xB4: OpcodeInfo(0xB4, 1, "LMUL",   Konami2_addr_mode.INH),
	0xB5: OpcodeInfo(0xB5, 1, "DIV X,B",   Konami2_addr_mode.INH),
	0xB6: OpcodeInfo(0xB6, 1, "BMOVE Y,X,U", Konami2_addr_mode.INH),
	0xB7: OpcodeInfo(0xB7, 1, "MOVE Y,X,U", Konami2_addr_mode.INH),
	0xB8: OpcodeInfo(0xB8, 2, "LSRD",   Konami2_addr_mode.IMM),
	0xB9: OpcodeInfo(0xB9, 2, "LSRD",   Konami2_addr_mode.IND),
	0xBA: OpcodeInfo(0xBA, 2, "RORD",   Konami2_addr_mode.IMM),
	0xBB: OpcodeInfo(0xBB, 2, "RORD",   Konami2_addr_mode.IND),
	0xBC: OpcodeInfo(0xBC, 2, "ASRD",   Konami2_addr_mode.IMM),
	0xBD: OpcodeInfo(0xBD, 2, "ASRD",   Konami2_addr_mode.IND),
	0xBE: OpcodeInfo(0xBE, 2, "ASLD",   Konami2_addr_mode.IMM),
	0xBF: OpcodeInfo(0xBF, 2, "ASLD",   Konami2_addr_mode.IND),

	0xC0: OpcodeInfo(0xC0, 2, "ROLD",   Konami2_addr_mode.IMM),
	0xC1: OpcodeInfo(0xC1, 2, "ROLD",   Konami2_addr_mode.IND),
	0xC2: OpcodeInfo(0xC2, 1, "CLRD",   Konami2_addr_mode.INH),
	0xC3: OpcodeInfo(0xC3, 2, "CLRW",   Konami2_addr_mode.IND),
	0xC4: OpcodeInfo(0xC4, 1, "NEGD",   Konami2_addr_mode.INH),
	0xC5: OpcodeInfo(0xC5, 2, "NEGW",   Konami2_addr_mode.IND),
	0xC6: OpcodeInfo(0xC6, 1, "INCD",   Konami2_addr_mode.INH),
	0xC7: OpcodeInfo(0xC7, 2, "INCW",   Konami2_addr_mode.IND),
	0xC8: OpcodeInfo(0xC8, 1, "DECD",   Konami2_addr_mode.INH),
	0xC9: OpcodeInfo(0xC9, 2, "DECW",   Konami2_addr_mode.IND),
	0xCA: OpcodeInfo(0xCA, 1, "TSTD",   Konami2_addr_mode.INH),
	0xCB: OpcodeInfo(0xCB, 2, "TSTW",   Konami2_addr_mode.IND),
	0xCC: OpcodeInfo(0xCC, 1, "ABSA",   Konami2_addr_mode.INH),
	0xCD: OpcodeInfo(0xCD, 1, "ABSB",   Konami2_addr_mode.INH),
	0xCE: OpcodeInfo(0xCE, 1, "ABSD",   Konami2_addr_mode.INH),
	0xCF: OpcodeInfo(0xCF, 1, "BSET A,X,U", Konami2_addr_mode.INH),
	0xD0: OpcodeInfo(0xD0, 1, "BSET D,X,U", Konami2_addr_mode.INH)
}

# for k in sorted(konami_opcodes.items(), key=lambda x: x[1][2]):
# 	#print(konami_opcodes[k])
# 	print(k[0])
