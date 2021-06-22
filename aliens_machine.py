#aliens_machine.py
#Compilar con nuitka:
#python3 -m nuitka --follow-imports aliens_machine.py
#run ./aliens_machine.bin

from eproms import EPROM_Type, EPROM_entry, Konami2eproms
from io import StringIO, TextIOWrapper
from timeit import default_timer as timer
from m6809_types import ADRMOD, FLAGS, FLAGS2
import konami2_opcodes as k2op
from ctypes import c_uint8, c_uint16, c_ulong
from typing import NamedTuple
import curses
import time
import sys
import numpy as np

class Subr_Jmp_Elem(NamedTuple):
    pc: c_uint16
    jmp_addr: c_uint16

class aliens_machine:
    def __init__(self)->None:
        from memory_mapper import SELECTOR, memory_mapper
        from konami2 import konami2_cpu_device
        self.m_kon2_cpu:konami2_cpu_device
        self.m_mapper:memory_mapper
        self.m_memory:Konami2eproms
        self.m_kon2_cpu = konami2_cpu_device(3000000) #clock speed 3000000
        self.m_memory = Konami2eproms(modo_dbg=False        )
        self.m_memory.create_RAM_entry(0x2000) #Work RAM
        self.m_memory.create_RAM_entry(0x200) #Color RAM TOP E15 W15-W8
        self.m_memory.create_RAM_entry(0x400) #SPRITE RAM
        self.m_memory.create_RAM_entry(0x4000) #TILEMAP RAM
        self.m_memory.create_RAM_entry(0x200) #Color RAM BOTTON E14 W7-W0
        self.m_mapper = memory_mapper(cpu=self.m_kon2_cpu, memory=self.m_memory) #irq callback
        self.m_kon2_cpu.set_mapper(self.m_mapper)
        self.m_kon2_cpu.set_memory(self.m_memory)

        self.m_kon2_dis = self.m_kon2_cpu.create_disassembler()
        self.m_kon2_cpu.device_start()
        self.m_kon2_cpu.device_reset()
        self.cienmil=0
        start = timer()
        trig_irq=True
        m_gosub_lvl=0
        frame_cnt=0


        #color conversion
        self.color:c_uint8=0
        #vblank period
        #vblank for 6Mpixel clock with 396: 54-288-342, 256: 16-224-240
        #vblank = 0.002112s <-> CPU 3Mhz cycle 6336 cycles after of IRQ (line 240)
        self.vblank_cnt=0
        self.vblank_start=False

        #IRQ TIMER
        self.m_irq_timer = 0

        self.CHAR_ROM= ("0123456789**-.?!" +
                        "█ABCDEFGHIJKLMNO" +
                        "PQRSTUVWXYZ'┛┗┓┏" +
                        "██▀▁▂▃▄▅▆▇█▉▊▋▌▍" +
                        " ▎▏▐░▒▓▔▕▖▗▘▙▚▛▜" +
                        "▝▞▟─━│┃┄┅┆┇┈┉┊┋┌" +
                        "┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├" +
                        "┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬" +
                        "┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼" +
                        "┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋╌" +
                        "╍╎╏═║╒╓╔╕╖╗╘╙╚╛╜" +
                        "╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬" +
                        "╭╮╯╰╱╲◞╴╵╶╷╸╹╺╻╼" +
                        "╽╾╿▲△▴▵▶▷▸▹►▻▼▽▾" +
                        "▿◀◁◂◃◄◅◆◇◈◉◊○◌◍◎" +
                        "●◐◑◒◓◔◕◖◗◘◙◚◛◜◝╳")

        #time
        self.start=0
        self.elapsed=0

        # *** WATCHPOINTS ***
        self.m_kon2_cpu.m_wp_addr1 = 0x1fec


        #List to store called subroutines and return address
        #Lst_Subr_Jmp_Elem = []
        Dict_Subr_Jmp_Elem = {}
        #Subr_Jmp_Elem

        # #curses init
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        
        # # Start colors in curses
        curses.start_color()
        # curses.init_color(30, 700 ,0 ,700) #RGB (0-1000) RANGE VALUE) VIOLET
        # curses.init_color(31, 700 ,700 ,700) #RGB (0-1000) RANGE VALUE) LIGHT GRAY 30%
        
        # curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_WHITE)
        # curses.init_pair(2, curses.COLOR_GREEN, 31)
        # curses.init_pair(3, 30 ,curses.COLOR_WHITE)
        # curses.init_pair(4, curses.COLOR_CYAN, 31)
        # curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_WHITE)
        # curses.init_pair(6, 30, 31)
        # curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_BLACK)

        #curses.resize_term(65+2,257+3)
        curses.resize_term(232,700)
        #curses.resize_term(67, 531)

        # # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        # #self.stdscr.addstr(0, 25+395,  "   WORK RAM   ", curses.color_pair(5))
        # self.stdscr.addstr(0, 25,      "FIX LAYER CODE", curses.color_pair(1))
        # self.stdscr.addstr(0, 25+65,   " A LAYER CODE ", curses.color_pair(2))
        # self.stdscr.addstr(0, 25+130,  " B LAYER CODE ", curses.color_pair(3))
        # self.stdscr.addstr(0, 25+195,  "  COLOR RAM   ", curses.color_pair(4))
        # self.stdscr.addstr(33, 25,     "FIX LAYER ATRB", curses.color_pair(6))
        # self.stdscr.addstr(33, 25+65,  " A LAYER ATRB ", curses.color_pair(1))
        # self.stdscr.addstr(33, 25+130, " B LAYER ATRB ", curses.color_pair(2))
        # self.stdscr.addstr(17, 25+195, "  SPRITE RAM  ", curses.color_pair(3))
        # #self.stdscr.addstr(66, 25+65,  " A LAYER SCRY ", curses.color_pair(2))
        # #self.stdscr.addstr(66, 25+130,  " B LAYER SCRY ", curses.color_pair(3))
        # #self.stdscr.addstr(68, 25+65,  " A LAYER SCRX ", curses.color_pair(4))
        # self.stdscr.addstr(68, 25+65,  " WORKRAM 1E00 ", curses.color_pair(4))
        # #self.stdscr.addstr(68, 25+130,  " B LAYER SCRX ", curses.color_pair(5))
        # self.stdscr.refresh()

    ### Printout 9EC4 Subroutine
        scr_count=0
        pausa=0
        self.last = 0
        self.m_irq_timer = 50000 #start generating irq at time 0
        self.frame_cnt=0


        with open('Sub_9EC4.lst', mode='w') as fsub:
            print(file=fsub)
            #print("*** Printout 9EC4 Subroutine ***", file=fsub)
            #print("*** Printout 9EC4 Subroutine ***")
            #while (self.m_kon2_cpu.m_pc.w.value != 0x9EC4):
            #while (self.m_kon2_cpu.m_pc.w.value != 0xADA6):
            self.start = time.time()
            while (self.m_kon2_cpu.m_pc.w.value != 0xFFFF): # and self.m_kon2_cpu.m_tcount < 150000000):
                self.last = self.m_kon2_cpu.m_icount

                self.m_kon2_cpu.execute_one()

                # if(self.m_kon2_cpu.m_pc.w.value == 0x9Ef2): # and self.m_kon2_cpu.m_u.w.value >= 0x3f0): # and self.m_kon2_cpu.m_x.w.value == 0x200):
                #     pausa=1
                # if self.m_kon2_cpu.m_tcount >=22239990:
                #     pausa=1
                
                #IRQ ENABLER EACH 1/60s or (cpu clock speed Hz) * (1/60) = 3000000 * (1/60) = 50000 cycles
                if(self.m_irq_timer >= 50000): 
                    self.m_irq_timer -= 50000
                    self.m_kon2_cpu.m_irq_line = True
                    self.frame_cnt+=1
                    linea = f"PC:{self.m_kon2_cpu.m_pc.w.value:04x} EA:{self.m_kon2_cpu.m_ea.w.value:04x} TCYCLE:{self.m_kon2_cpu.m_tcount:010d} FRAME:{self.frame_cnt:06d} BNK0 {self.m_mapper.m_k052109_charrombank[0]:02x} BNK1:{self.m_mapper.m_k052109_charrombank[1]:02x} BNK2:{self.m_mapper.m_k052109_charrombank[2]:02x} BNK3:{self.m_mapper.m_k052109_charrombank[3]:02x}"
                    self.stdscr.addstr(225, 1, linea, curses.color_pair(0))
                    #self.draw_layer_fix(scr=self.stdscr)

                if(self.m_irq_timer >= 43664): #50000 - 6336
                    self.vblank_start = True
                    self.vblank_start = 0
                    self.m_mapper.m_k051937_vblank=True
                
                if(self.vblank_start):
                    self.vblank_cnt += (self.m_kon2_cpu.m_icount-self.last)
                
                if(self.vblank_cnt >= 6336):
                    self.vblank_start = False
                    self.m_mapper.m_k051937_vblank=False
                     
                if(scr_count > 100000):
                    scr_count -=  100000
                    #self.print_screen()
                    self.draw_layer_fix(scr=self.stdscr)

                    

                elif(pausa == 1):
                    self.print_screen()
                    self.stdscr.addstr(54, 195, "*** PAUSA ***", curses.color_pair(3))
                    if (self.m_kon2_cpu.m_state):
                        self.m_kon2_cpu.execute_one()
                    output = StringIO()
                    self.m_kon2_dis.disassembler(pc=self.m_kon2_cpu.m_pc.w.value, stream=output,  opcode_mem=self.m_mapper)
                    kondis_str = "{:04X}: {}".format(self.m_kon2_cpu.m_pc.w.value, output.getvalue())
                    output.close()
                    self.stdscr.addstr(56, 195, kondis_str, curses.color_pair(3))
                    #time.sleep(5)

                scr_count+=(self.m_kon2_cpu.m_icount-self.last)
                self.m_irq_timer += (self.m_kon2_cpu.m_icount-self.last)

            # while (self.m_kon2_cpu.m_pc.w.value != 0x9F02 and self.m_kon2_cpu.m_pc.w.value != 0x9F09):
            #     self.print_one_exec(file=fsub)
            #     if(((self.m_kon2_cpu.m_tcount>>10)%1000) == 0):
            #         self.print_screen()                
            #     self.last = self.m_kon2_cpu.m_icount

            #self.workram_prinout()
            # self.cram_prinout()
            # self.fixed_tilemap_prinout()

            # for k in sorted(k2op.konami_opcodes.items(), key=lambda x: x[1][2]):
            # #for k in sorted(self.m_kon2_cpu.m_kon2_inst_cover):
            #     if( k[0] in self.m_kon2_cpu.m_kon2_inst_cover):
            #         print(f"{k2op.konami_opcodes[k[0]].name}({k2op.konami_opcodes[k[0]].mode.name})", end='')
            #         if (k[0] == 0xB6):
            #             print ("\t", end='')
            #         else:
            #             print ("\t\t", end='')
            #         print(f": {self.m_kon2_cpu.m_kon2_inst_cover[k[0]]:10} [", end='')
            #         for i in range(0,int(self.m_kon2_cpu.m_kon2_inst_cover[k[0]] / self.m_kon2_cpu.m_tcount * 100)):
            #             print(f"●", end='')
            #         for i in range(int(self.m_kon2_cpu.m_kon2_inst_cover[k[0]] / self.m_kon2_cpu.m_tcount * 100), 100):
            #             print(f" ", end='')
            #     else:
            #         print(f"{k2op.konami_opcodes[k[0]].name}({k2op.konami_opcodes[k[0]].mode.name})", end='')
            #         if (k[0] == 0xB6):
            #             print ("\t", end='')
            #         else:
            #             print ("\t\t", end='')
            #         print(f": {0:10} [", end='')
            #         for i in range(0, 100):
            #             print(f" ", end='')              
            #     print("]")

            # print(f"Total Cycles: {self.m_kon2_cpu.m_tcount:10}")
            # print(f"Opcodes covered {len(self.m_kon2_cpu.m_kon2_inst_cover)} of {len(k2op.konami_opcodes)} ({100.0 / len(k2op.konami_opcodes) * len(self.m_kon2_cpu.m_kon2_inst_cover):.2f}%)")

        #self.print_screen() 
        time.sleep(10)
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

            # CHEAT MEMORY LOCATION 0X1FEC WRITING 0X0 TO IT FOR CONTINUE CODE EXECUTION AT 9E30
            # if(self.m_kon2_cpu.m_pc.w.value == 0x9e30):
            # self.m_memory.write_RAM_entry_data(0,0x1fec,0x00)

        #0x8040, 0x8010
        #while ((self.m_kon2_cpu.m_cc & FLAGS.CC_I.value) == 0x10):
        #while (self.print_state_if_addr(0x9E85)): #
        ###while (self.m_kon2_cpu.m_pc.w.value != 0x9e30):
        #while (self.m_kon2_cpu.m_pc.w.value != 0xADA6):
        #while (self.m_kon2_cpu.m_pc.w.value != 0x9d28):
        #while (self.m_kon2_cpu.m_pc.w.value != 0x9eb2):
        #while (self.m_kon2_cpu.m_tcount <= 8547):
        #while (self.m_kon2_cpu.m_tcount < 50000000):
            # if((self.cienmil * 100000 + self.m_kon2_cpu.m_icount) > 700006 and trig_irq):
            #     trig_irq = False
            #     self.m_kon2_cpu.m_cc &= (FLAGS.CC_I.value ^ 0xff)
            #     self.m_kon2_cpu.m_irq_line = True
            #     print(f"***IRQ***  Flag I:{self.m_kon2_cpu.m_cc & FLAGS.CC_I.value:02X}  count:{self.cienmil * 100000 + self.m_kon2_cpu.m_icount}")
            # if(self.m_kon2_cpu.m_pc.w.value == 0x9e30):
            #     self.m_memory.write_RAM_entry_data(0,0x1fec,0x00)
                
            # self.m_kon2_cpu.execute_one()

            # # *** CHECK WATCHPOINTS ***
            # if(self.m_kon2_cpu.m_wp1):
            #     if(self.m_kon2_cpu.m_wp1 == 1):
            #         print(f"@WATCHPOINT1: READ value 0x{self.m_kon2_cpu.m_wp_val1:02X} from 0x{self.m_kon2_cpu.m_wp_addr1:04X} at 0x{self.m_kon2_cpu.lst_pc2:04X}")
            #     elif(self.m_kon2_cpu.m_wp1 == 2):
            #         print(f"@WATCHPOINT1: WRITE value 0x{self.m_kon2_cpu.m_wp_val1:02X} to 0x{self.m_kon2_cpu.m_wp_addr1:04X} at 0x{self.m_kon2_cpu.lst_pc2:04X}")
                
            #     self.m_kon2_cpu.m_wp1=0

            #print(f"PC:0x{self.m_kon2_cpu.m_pc.w.value:04X} Cycle:{self.m_kon2_cpu.m_tcount:010d}")
            # if(trig_irq):
            #     self.m_kon2_cpu.execute_one()
            # else:
            #     self.print_one_exec()

            # if(self.m_kon2_cpu.m_pc.w.value == 0xfffe):
            #     print()
            #     print("*** REACHED 0x9E3B ADDRESS ***")
            #     self.print_one_exec()
            #     sys.exit()

            # self.last = self.m_kon2_cpu.m_icount
            # if((self.m_kon2_cpu.m_icount) >= 100000): 
            #     self.cienmil+=1
            #     self.m_kon2_cpu.m_icount-=100000
            #     #print(".", end='')
            #     print(".")

        #     if(self.m_kon2_cpu.m_jmp_called):
        #         self.m_kon2_cpu.m_jmp_called = False
        #         print(f"@JMP: {self.m_kon2_cpu.lst_pc2:04X} |=> {self.m_kon2_cpu.m_ea.w.value:04X}")

        #     if(self.m_kon2_cpu.subr_called):
        #         self.m_kon2_cpu.subr_called = False
        #         #print()
        #         if self.m_kon2_cpu.lst_pc not in Dict_Subr_Jmp_Elem:
        #             #Dict_Subr_Jmp_Elem.append(self.m_kon2_cpu.lst_pc)
        #             Dict_Subr_Jmp_Elem[self.m_kon2_cpu.lst_pc] = 1
        #         else:
        #             Dict_Subr_Jmp_Elem[self.m_kon2_cpu.lst_pc] += 1

        #         print(f"Cycle:{self.m_kon2_cpu.m_tcount:010d} BANK:0x{self.m_kon2_cpu.m_bank:02X} CRAM:{self.m_mapper.m_cram} ", end='')
        #         for i in range(m_gosub_lvl): 
        #             print("        ", end='')
        #         print(f"{self.m_kon2_cpu.lst_pc2:04X} => {self.m_kon2_cpu.lst_pc:04X}({Dict_Subr_Jmp_Elem[self.m_kon2_cpu.lst_pc]})")
        #         m_gosub_lvl+=1
        #         #Lst_Subr_Jmp_Elem.append(Subr_Jmp_Elem(pc=self.m_kon2_cpu.lst_pc2, jmp_addr=self.m_kon2_cpu.lst_pc))

        #         #print(f"BK4:{self.m_mapper.get_BK4()} BANK:{self.m_kon2_cpu.m_bank:02X}")
        #         #print(f"PC:0x{self.m_kon2_cpu.lst_pc2:04X} SUBR CALLED TO 0x{self.m_kon2_cpu.lst_pc:04X} count:{self.cienmil * 100000 + self.m_kon2_cpu.m_icount} Flag I:{self.m_kon2_cpu.m_cc & FLAGS.CC_I.value:02X}")

        #     if(self.m_kon2_cpu.rts_exec):
        #         self.m_kon2_cpu.rts_exec = False
        #         m_gosub_lvl-=1
        #         #print()
        #         #Lst_Subr_Jmp_Elem.pop()
        #         print(f"Cycle:{self.m_kon2_cpu.m_tcount:010d} BANK:0x{self.m_kon2_cpu.m_bank:02X} CRAM:{self.m_mapper.m_cram} ", end='')
        #         for i in range(m_gosub_lvl): 
        #             print("        ", end='')
        #         print(f"{self.m_kon2_cpu.lst_pc2:04X} <= {self.m_kon2_cpu.lst_pc:04X}")
                
        #         #print(f"BK4:{self.m_mapper.get_BK4()} BANK:{self.m_kon2_cpu.m_bank:02X}")
        #         #print(f"PC=0x{self.m_kon2_cpu.lst_pc:04X} RTS TO: 0x{self.m_kon2_cpu.lst_pc2:04X} count:{self.cienmil * 100000 + self.m_kon2_cpu.m_icount} Flag I:{self.m_kon2_cpu.m_cc & FLAGS.CC_I.value:02X}")

        #     if(self.m_kon2_cpu.rti_exec):
        #         self.m_kon2_cpu.rti_exec = False
        #         print()
        #         print(f"BK4:{self.m_mapper.get_BK4()} BANK:{self.m_kon2_cpu.m_bank:02X} CRAM:{self.m_mapper.m_cram} ")
        #         print(f"PC=0x{self.m_kon2_cpu.lst_pc:04X} RTI TO: 0x{self.m_kon2_cpu.lst_pc2:04X} count:{self.cienmil * 100000 + self.m_kon2_cpu.m_icount} Flag I:{self.m_kon2_cpu.m_cc & FLAGS.CC_I.value:02X}")

        # for _ in range(0,0x10):
        #     self.print_one_exec()
        #     self.last = self.m_kon2_cpu.m_icount
        # self.cram_prinout()


    def fixed_tilemap_prinout(self) -> None:
        #fixed tilemap printout
        CHAR_ROM= "0123456789**-.?!\u2588ABCDEFGHIJKLMNOPQRSTUVWXYZ'┛┗\u2513\u250f\u2588\u2588\u2588                                                                       "
        with open('FIXED_TILEMAP_6000-6800.lst', mode='w') as file2:
            print(file=file2)
            print("     *** FIXED TILEMAP RAM 6000-6800 ***", file=file2)
            print(file=file2)
            for i in range (0x2000,0x2800,64):
                for j in range (0,64):
                    print(f"{CHAR_ROM[self.m_memory.read_RAM_entry_data(3,i+j)]}", end='', file=file2) #WORK RAM
                print(file=file2)

    def workram_prinout(self) -> None:
        #WORK RAM printout
        with open('WORKRAM.lst', mode='w') as file2:
            print(file=file2)
            print("     *** WORK RAM ***", file=file2)
            print(file=file2)
            for i in range (0x0,0x2000,16):
                if(i%31 == 0):
                    print("-----------------------------------------------------", file=file2)
                    print("      00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F", file=file2)
                    print("-----------------------------------------------------", file=file2)

                print(f"{i:04X}: ", end='', file=file2)
                for j in range (0,16):
                    print(f"{self.m_memory.read_RAM_entry_data(0,i+j):02X} ", end='', file=file2) #WORK RAM
                print(file=file2)

    def cram_prinout(self) -> None:
        #CRAM printout
        with open('CRAM.lst', mode='w') as file2:
            print(file=file2)
            print("     *** CRAM ***", file=file2)
            print(file=file2)
            for i in range (0x0,0x400,16):
                if(i%31 == 0):
                    print("-----------------------------------------------------", file=file2)
                    print("      00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F", file=file2)
                    print("-----------------------------------------------------", file=file2)

                print(f"{i:04X}: ", end='', file=file2)
                for j in range (0,16):
                    print(f"{self.m_memory.read_RAM_entry_data(1,i+j):02X} ", end='', file=file2) #CRAM
                print(file=file2)

    def print_one_exec(self, file:TextIOWrapper) -> None:
        if (self.m_kon2_cpu.m_state):
            self.m_kon2_cpu.execute_one()

        output = StringIO()
        
        offsetpc = self.m_kon2_dis.disassembler(pc=self.m_kon2_cpu.m_pc.w.value, stream=output,  opcode_mem=self.m_mapper)
        print("----------------------------", file=file)
        print("{:04X}: {}".format(self.m_kon2_cpu.m_pc.w.value, output.getvalue()), file=file)
        output.close()

        self.m_kon2_cpu.execute_one()

        if (self.m_kon2_cpu.m_state):
            print(">>> INDEXED opcode", file=file)
            self.m_kon2_cpu.execute_one()

        # print("----------------------------")
        # print("Konami-2 Registers Status:")
        # print()
        print(f"Cycle:{self.m_kon2_cpu.m_tcount:010d} BANK:0x{self.m_kon2_cpu.m_bank:02X} CRAM:{self.m_mapper.m_cram} RMRD:{self.m_mapper.m_rmrd} INIT:{self.m_mapper.m_init}", file=file)
        #print(f"             EFHINZVC", file=file)
        print(f"             ", end='', file=file)

        for cnt in (0x80,0x40,0x20,0x10,0x8,0x4,0x2,0x1):
            if self.m_kon2_cpu.m_cc & cnt:
                print(f"{FLAGS2(cnt).name}", end='', file=file)
            else:
                print("-", end='', file=file)
        print(file=file)
        print(f"DP: 0x{self.m_kon2_cpu.m_dp.value:02X} CC: {self.m_kon2_cpu.m_cc:08b} PC: 0x{self.m_kon2_cpu.m_pc.w.value:04X}", file=file)
        print(f"A:  0x{self.m_kon2_cpu.m_q.r.r8.a.value:02X} B:  0x{self.m_kon2_cpu.m_q.r.r8.b.value:02X} D:  0x{self.m_kon2_cpu.m_q.r.r16.d.value:04X}", file=file)
        print(f"X: 0x{self.m_kon2_cpu.m_x.w.value:04X} Y: 0x{self.m_kon2_cpu.m_y.w.value:04X}", file=file)
        print(f"S: 0x{self.m_kon2_cpu.m_s.w.value:04X} U: 0x{self.m_kon2_cpu.m_u.w.value:04X}", file=file)
        print(f"Effective Address 0x{self.m_kon2_cpu.m_ea.w.value:04X} Byte: 0x0x{self.m_kon2_cpu.read_memory(self.m_kon2_cpu.m_ea.w.value):02X} Word: 0x{self.m_kon2_cpu.read_memory(self.m_kon2_cpu.m_ea.w.value):02X}{self.m_kon2_cpu.read_memory(self.m_kon2_cpu.m_ea.w.value+1):02X}", file=file)
    
        print(f"Addr. Mode: {ADRMOD(self.m_kon2_cpu.m_addressing_mode).name}", file=file)
        print(f"Instruction cycle count: {(self.m_kon2_cpu.m_icount-self.last)}", file=file)
        # print("----------------------------")
        # print()
                
    def print_state_if_addr(self, print_cond: c_uint16) -> bool:
        if (self.m_kon2_cpu.m_pc.w.value == print_cond):
            output = StringIO()
            offsetpc = self.m_kon2_dis.disassembler(pc=self.m_kon2_cpu.m_pc.w.value, stream=output,  opcode_mem=self.m_mapper)
            print("----------------------------")
            # print("Executed instruction:")
            # print()
            print("{:04X}: {}".format(self.m_kon2_cpu.m_pc.w.value, output.getvalue()))
            output.close()

            self.m_kon2_cpu.execute_one()

            if (self.m_kon2_cpu.m_state):
                print(">>> INDEXED opcode")
                self.m_kon2_cpu.execute_one()

            # print("----------------------------")
            # print("Konami-2 Registers Status:")
            # print()
            print(f"Cycle:{self.m_kon2_cpu.m_tcount:010d} BANK:0x{self.m_kon2_cpu.m_bank:02X} CRAM:{self.m_mapper.m_cram} RMRD:{self.m_mapper.m_rmrd} INIT:{self.m_mapper.m_init}")
            print(f"A: 0x{self.m_kon2_cpu.m_q.r.r8.a.value:02X} B: 0x{self.m_kon2_cpu.m_q.r.r8.b.value:02X} D: 0x{self.m_kon2_cpu.m_q.r.r16.d.value:04X}")
            print(f"X: 0x{self.m_kon2_cpu.m_x.w.value:04X} Y: 0x{self.m_kon2_cpu.m_y.w.value:04X}")
            print(f"S: 0x{self.m_kon2_cpu.m_s.w.value:04X} U: 0x{self.m_kon2_cpu.m_u.w.value:04X}")
            print(f".            EFHINZVC")
            print(f"DP: 0x{self.m_kon2_cpu.m_dp.value:02X} CC: {self.m_kon2_cpu.m_cc:08b} PC: 0x{self.m_kon2_cpu.m_pc.w.value:04X}")
            print(f"EA: 0x{self.m_kon2_cpu.m_ea.w.value:04X} Addr. Mode: {ADRMOD(self.m_kon2_cpu.m_addressing_mode).name}")
            print(f"Last instruction cycle count: {(self.m_kon2_cpu.m_icount-self.last)}")
            # print("----------------------------")
            # print()
            return False #condition to exit from loop
        else:
            return True #condition to continue loop
    
    def print_screen(self) -> None:
        #work RAM
        # for i in range (0,32):
        #     for j in range(0,256):
        #         self.stdscr.addstr(i+1, j+275, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(0,i*256+j)], curses.color_pair(5))

        for i in range (0,32):
            for j in range (0,64):
                row1 = i+1
                row2 = i+34
                #row3 = i+68
                #row3
                col1 = j
                col2 = j+65
                col3 = j+130
                col4 = j+195
                #col4
                #FIX CODE
                self.stdscr.addstr(i+1, j, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x2000+i*64+j)], curses.color_pair(1))
                #LAYER A CODE
                self.stdscr.addstr(i+1, j+65, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x2800+i*64+j)], curses.color_pair(2))
                #LAYER B CODE
                self.stdscr.addstr(i+1, j+130, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x3000+i*64+j)], curses.color_pair(3))
                #COLOR RAM
                if(i%2 == 0): self.stdscr.addstr((i>>1)+1, j+195, self.CHAR_ROM[self.m_mapper.cram_read(addr=(i>>1)*64+j)], curses.color_pair(4))
                
                #FIX ATTRIB
                self.stdscr.addstr(i+34, j, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x0+i*64+j)], curses.color_pair(6))
                #FIX LAYER A
                self.stdscr.addstr(i+34, j+65, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x0800+i*64+j)], curses.color_pair(1))
                #FIX LAYER B
                self.stdscr.addstr(i+34, j+130, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x1000+i*64+j)], curses.color_pair(2))
                #SPRITE RAM
                if(i%2 == 0): self.stdscr.addstr((i>>1)+18, j+195, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(2,(i>>1)*64+j)], curses.color_pair(3))

        #Y SCROLL
        # for i in range(0,40):
        #     #A LAYER
        #     self.stdscr.addstr(67,i+77 , self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x180c+i)], curses.color_pair(2))
        #     #B LAYER
        #     self.stdscr.addstr(67,i+142 , self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x380c+i)], curses.color_pair(3))
        #X SCROLL
        # for i in range(0,8):
        #     for j in range(0,64):
        #         #LAYER A
        #         self.stdscr.addstr(i+69, j+65, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x1a00+i*64+j)], curses.color_pair(4))
        #         #LAYER B
        #         self.stdscr.addstr(i+69, j+130, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(3,0x3a00+i*64+j)], curses.color_pair(5))

        #WORKRAM 1E00-1EFF
        for i in range(0,4):
            for j in range(0,64):
                self.stdscr.addstr(i+69, j+65, self.CHAR_ROM[self.m_memory.read_RAM_entry_data(0,0x1E00+i*64+j)], curses.color_pair(4))

        #COUNTERS
        scr_cycle = f"Cycle:{self.m_kon2_cpu.m_tcount:010d} BANK:0x{self.m_kon2_cpu.m_bank:02X} IRQ:{ 1 if(self.m_kon2_cpu.m_irq_line) else 0}"
        scr_lin1 = f"DP: 0x{self.m_kon2_cpu.m_dp.value:02X} CC: {self.m_kon2_cpu.m_cc:08b} PC: 0x{self.m_kon2_cpu.m_pc.w.value:04X}"
        scr_lin2 = f"A:  0x{self.m_kon2_cpu.m_q.r.r8.a.value:02X} B:  0x{self.m_kon2_cpu.m_q.r.r8.b.value:02X} D:  0x{self.m_kon2_cpu.m_q.r.r16.d.value:04X}"
        scr_lin3 = f"X: 0x{self.m_kon2_cpu.m_x.w.value:04X} Y: 0x{self.m_kon2_cpu.m_y.w.value:04X}"
        scr_lin4 = f"S: 0x{self.m_kon2_cpu.m_s.w.value:04X} U: 0x{self.m_kon2_cpu.m_u.w.value:04X}"
        scr_lin5 = f"Addr. Mode: {ADRMOD(self.m_kon2_cpu.m_addressing_mode).name:26}"
        scr_lin6 = f"Effective Address 0x{self.m_kon2_cpu.m_ea.w.value:04X} Byte: 0x0x{self.m_kon2_cpu.read_memory(self.m_kon2_cpu.m_ea.w.value):02X} Word: 0x{self.m_kon2_cpu.read_memory(self.m_kon2_cpu.m_ea.w.value):02X}{self.m_kon2_cpu.read_memory(self.m_kon2_cpu.m_ea.w.value+1):02X}"
        scr_lin7 = f"Instruction cycle count: {(self.m_kon2_cpu.m_icount-self.last)} [TIME(s):{time.time()-self.start:09.2f}]"
        
        scroll_control = self.m_memory.read_RAM_entry_data(3,0x1c80)
        
        a_scroll_ctrl_lines = 0
        a_scroll_ctrl_cols = 0
        
        if ((scroll_control & 0x3) == 2):
            a_scroll_ctrl_lines = 64
        elif ((scroll_control & 0x3) == 3):            
            a_scroll_ctrl_lines = 256
        
        if (((scroll_control & 0x4)>>2) == 1):
            a_scroll_ctrl_cols = 64 #40

        b_scroll_ctrl_lines = 0
        b_scroll_ctrl_cols = 0
        
        if (((scroll_control & 0x18)>>3) == 2):
            b_scroll_ctrl_lines = 64
        elif (((scroll_control & 0x18)>>3) == 3):            
            b_scroll_ctrl_lines = 256
        
        if (((scroll_control & 0x20)>>4) == 1):
            b_scroll_ctrl_cols = 64 #40            

        scr_lin8 = f"LAYER A: ROW SCR:{a_scroll_ctrl_lines} COL SCR:{a_scroll_ctrl_cols}"
        scr_lin9 = f"LAYER B: ROW SCR:{b_scroll_ctrl_lines} COL SCR:{b_scroll_ctrl_cols}"

        self.stdscr.addstr(35, 195, scr_cycle, curses.color_pair(1))
        #scr_pc = f"PC: 0x{self.m_kon2_cpu.m_pc.w.value:04X}"
        #self.stdscr.addstr(36, 201, "    ", curses.color_pair(1)) #clear value
        #self.stdscr.addstr(36, 195, scr_pc, curses.color_pair(2))

        self.stdscr.addstr(36, 195, scr_lin1, curses.color_pair(1))
        self.stdscr.addstr(37, 195, scr_lin2, curses.color_pair(2))
        self.stdscr.addstr(38, 195, scr_lin3, curses.color_pair(3))
        self.stdscr.addstr(39, 195, scr_lin4, curses.color_pair(4))
        self.stdscr.addstr(40, 195, scr_lin5, curses.color_pair(5))
        self.stdscr.addstr(41, 195, scr_lin6, curses.color_pair(6))
        self.stdscr.addstr(42, 195, scr_lin7, curses.color_pair(1))
        self.stdscr.addstr(43, 195, scr_lin8, curses.color_pair(2))
        self.stdscr.addstr(44, 195, scr_lin9, curses.color_pair(3))

        self.stdscr.addstr(45, 195, "CC: ", curses.color_pair(2))
        i=0
        for cnt in (0x80,0x40,0x20,0x10,0x8,0x4,0x2,0x1):
            i+=1
            if self.m_kon2_cpu.m_cc & cnt:
                self.stdscr.addstr(45, 199+i, FLAGS2(cnt).name, curses.color_pair(3))
            else:
                self.stdscr.addstr(45, 199+i, FLAGS2(cnt).name, curses.color_pair(7))

        #CRAMCS is active low signal
        if (self.m_mapper.m_cram == 1):
            self.stdscr.addstr(47, 195, "CRAMCS", curses.color_pair(5))
        else:
            self.stdscr.addstr(47, 195, "      ", curses.color_pair(7)) #clear value
        #PROG
        if (self.m_mapper.m_prog == 1):
            self.stdscr.addstr(48, 195, "PROG", curses.color_pair(5))
        else:
            self.stdscr.addstr(48, 195, "      ", curses.color_pair(7)) #clear value
        #BANK
        if (self.m_mapper.m_bank == 1):
            self.stdscr.addstr(49, 195, "BANK", curses.color_pair(5))
        else:
            self.stdscr.addstr(49, 195, "      ", curses.color_pair(7)) #clear value
        #WORK
        if (self.m_mapper.m_work == 1):
            self.stdscr.addstr(50, 195, "WORK", curses.color_pair(5))
        else:
            self.stdscr.addstr(50, 195, "      ", curses.color_pair(7)) #clear value
        #VRAMCS
        if (self.m_mapper.m_videocs == 1):
            self.stdscr.addstr(51, 195, "VRAMCS", curses.color_pair(5))
        else:
            self.stdscr.addstr(51, 195, "      ", curses.color_pair(7)) #clear value
        #OBJCS
        if (self.m_mapper.m_objcs == 1):
            self.stdscr.addstr(52, 195, "OBJCS", curses.color_pair(5))
        else:
            self.stdscr.addstr(52, 195, "      ", curses.color_pair(7)) #clear value                                    
        #INIT
        if (self.m_mapper.m_init == 1):
            self.stdscr.addstr(54, 195, "INIT", curses.color_pair(6))
        else:
            self.stdscr.addstr(54, 195, "    ", curses.color_pair(7)) #clear value
        #RMRD
        if (self.m_mapper.m_rmrd == 1):
            self.stdscr.addstr(55, 195, "RMRD", curses.color_pair(1))
        else:
            self.stdscr.addstr(55, 195, "    ", curses.color_pair(7)) #clear value
            
        self.stdscr.refresh()

    def draw_layer_fix(self, scr) -> None:

        if self.m_mapper.m_vupdate == 1 or self.m_mapper.m_cram_update == 1:
            self.m_mapper.m_vupdate=0
            self.m_mapper.m_cram_update=0

            #update color palette
            curses.init_color(7 , 0, 0 ,0) #replaces white with black
            curses.init_color(15 , 1000, 0 ,580) #replaces black with pink
            for i in range(1,192):
                valor = self.m_mapper.cram_read16(i<<1)
                #valor = self.m_mapper.memory.read_RAM_entry_data16(num=1, offset=(i<<1))
                curses_b = (valor & 0x7c00) >> 5
                curses_g = valor & 0x03e0
                curses_r = (valor & 0x001f) << 5
                curses.init_color(i+15 , curses_r, curses_g ,curses_b)
                curses.init_pair(i, i+15, 15)
            
            for row in range(0,48):
                for col in range(0,64):
                    scr.addstr(row, col+600,   "█", curses.color_pair (((row>>2)<<4) + (col>>2))   )


            #draw fix tile layer 
            ROW_START = 0x02
            ROW_END = 0x1D
            COL_START = 0X0E
            COL_END = 0X31
            FIX_CODE_BASE = 0x2000
            FIX_ATTR_BASE = 0X0
            LAYER_A_CODE_BASE = 0X2800
            LAYER_A_ATTR_BASE = 0X0800
            LAYER_B_CODE_BASE = 0X3000
            LAYER_B_ATTR_BASE = 0X1000
            #NUM_LAYER=0 FIX, 1 LAYER_A, 2 LAYER_B
            layer_a_scroll_x = self.m_memory.read_RAM_entry_data(num=3, offset=0x1a00) + (self.m_memory.read_RAM_entry_data(num=3, offset=0x1a01)<<8) - 6
            layer_b_scroll_x = self.m_memory.read_RAM_entry_data(num=3, offset=0x3a00) + (self.m_memory.read_RAM_entry_data(num=3, offset=0x3a01)<<8) - 6
            x_a_offset = (layer_a_scroll_x & 0x7)
            x_b_offset = (layer_b_scroll_x & 0x7)
            self.x_desp=0
            self.col_range = 36
            if (x_a_offset):
                self.col_range+=1

            row_table = [0x0000, 0x0040, 0x0080, 0x00C0, 0x0100, 0x0140, 0x0180, 0x01C0, 0x0200, 0x0240, 0x0280, 0x02C0, 0x0300, 0x0340, 0x0380, 0x03C0, 0x0400, 0x0440, 0x0480, 0x04C0, 0x0500, 0x0540, 0x0580, 0x05C0, 0x0600, 0x0640, 0x0680, 0x06C0, 0x0700, 0x0740, 0x0780, 0x07C0 ]
            for row in range (0,224,8): #0-224 pixels
                #for col in range (0,self.col_range): #0-288 character width 8
                for col in range (0,36): #0-288 character width 8

                    ### LAYER A ###
                    #NUM_LAYER = 1
                    col8 = col << 4 

                    tile_index = row_table[ROW_START + (row>>3)] + (((layer_a_scroll_x>>3) + col+ 0x0e)%0x40)
                    
                    code = self.m_memory.read_RAM_entry_data(3,LAYER_A_CODE_BASE+tile_index)
                
                    attr = self.m_memory.read_RAM_entry_data(3,LAYER_A_ATTR_BASE+tile_index)
                    bank = self.m_mapper.m_k052109_charrombank[(attr & 0x0C)>>2]
                    
                    
                    #flags = 0
                    #priority = 0
                    
                    attr = (attr & 0xf3) | ((bank & 0x03)<<2)
                    bank >>=2
                    #flipy = attr  & 0x02
                    
                    code |= ((attr & 0x3f) << 8) | (bank << 14)
                    
                    self.color = (4 + ((attr & 0xc0) >> 6))<<4 # 2 bits superiores segun la capa (FIX 00, LAYER A 01, LAYER B 10), 2 bits inferiores    

                    #DRAW TILE ROWs
                    tile_rom_pixels = np.empty(8, dtype=np.uint32)

                    #code=0x77
                    if x_a_offset != 0 and col == 0: #There is a horizontal offset and we are in the first column char of screen
                        #compute how many remaining columns you have to draw after the offset in the column 0 tile
                        self.x_desp = 8 -  x_a_offset
                        
                        #draw it
                        for z in range(0,8):
                            valor = self.m_memory.rom_map[EPROM_Type.TILE].rom_data[(code<<3)+z]
                            if valor == 0:
                                tile_rom_pixels[0] = 0
                                tile_rom_pixels[1] = 0
                                tile_rom_pixels[2] = 0
                                tile_rom_pixels[3] = 0
                                tile_rom_pixels[4] = 0
                                tile_rom_pixels[5] = 0
                                tile_rom_pixels[6] = 0
                                tile_rom_pixels[7] = 0
                            else:
                                tile_rom_pixels[0] = ((valor & 0x80000000) >> 31) | ((valor & 0x800000) >> 22) | ((valor & 0x8000) >> 13) | ((valor & 0x80) >> 4) 
                                tile_rom_pixels[1] = ((valor & 0x40000000) >> 30) | ((valor & 0x400000) >> 21) | ((valor & 0x4000) >> 12) | ((valor & 0x40) >> 3) 
                                tile_rom_pixels[2] = ((valor & 0x20000000) >> 29) | ((valor & 0x200000) >> 20) | ((valor & 0x2000) >> 11) | ((valor & 0x20) >> 2) 
                                tile_rom_pixels[3] = ((valor & 0x10000000) >> 28) | ((valor & 0x100000) >> 19) | ((valor & 0x1000) >> 10) | ((valor & 0x10) >> 1) 
                                tile_rom_pixels[4] = ((valor & 0x08000000) >> 27) | ((valor & 0x080000) >> 18) | ((valor & 0x0800) >> 9) | (valor & 0x08) 
                                tile_rom_pixels[5] = ((valor & 0x04000000) >> 26) | ((valor & 0x040000) >> 17) | ((valor & 0x0400) >> 8) | ((valor & 0x04) << 1) 
                                tile_rom_pixels[6] = ((valor & 0x02000000) >> 25) | ((valor & 0x020000) >> 16) | ((valor & 0x0200) >> 7) | ((valor & 0x02) << 2) 
                                tile_rom_pixels[7] = ((valor & 0x01000000) >> 24) | ((valor & 0x010000) >> 15) | ((valor & 0x0100) >> 6) | ((valor & 0x01) << 3)

                        for w in range (self.x_desp):
                            scr.addstr(row+z, w<<1, "██", curses.color_pair(self.color+tile_rom_pixels[w + x_a_offset]))
                        self.x_desp <<= 1 #compensate value for two chars writen to screen

                    elif x_a_offset != 0 and col == (self.col_range - 1):
                        #draw remaining of pixel of last column
                        for z in range(0,8):
                            valor = self.m_memory.rom_map[EPROM_Type.TILE].rom_data[(code<<3)+z]
                            if valor == 0:
                                tile_rom_pixels[0] = 0
                                tile_rom_pixels[1] = 0
                                tile_rom_pixels[2] = 0
                                tile_rom_pixels[3] = 0
                                tile_rom_pixels[4] = 0
                                tile_rom_pixels[5] = 0
                                tile_rom_pixels[6] = 0
                                tile_rom_pixels[7] = 0
                            else:
                                tile_rom_pixels[0] = ((valor & 0x80000000) >> 31) | ((valor & 0x800000) >> 22) | ((valor & 0x8000) >> 13) | ((valor & 0x80) >> 4) 
                                tile_rom_pixels[1] = ((valor & 0x40000000) >> 30) | ((valor & 0x400000) >> 21) | ((valor & 0x4000) >> 12) | ((valor & 0x40) >> 3) 
                                tile_rom_pixels[2] = ((valor & 0x20000000) >> 29) | ((valor & 0x200000) >> 20) | ((valor & 0x2000) >> 11) | ((valor & 0x20) >> 2) 
                                tile_rom_pixels[3] = ((valor & 0x10000000) >> 28) | ((valor & 0x100000) >> 19) | ((valor & 0x1000) >> 10) | ((valor & 0x10) >> 1) 
                                tile_rom_pixels[4] = ((valor & 0x08000000) >> 27) | ((valor & 0x080000) >> 18) | ((valor & 0x0800) >> 9) | (valor & 0x08) 
                                tile_rom_pixels[5] = ((valor & 0x04000000) >> 26) | ((valor & 0x040000) >> 17) | ((valor & 0x0400) >> 8) | ((valor & 0x04) << 1) 
                                tile_rom_pixels[6] = ((valor & 0x02000000) >> 25) | ((valor & 0x020000) >> 16) | ((valor & 0x0200) >> 7) | ((valor & 0x02) << 2) 
                                tile_rom_pixels[7] = ((valor & 0x01000000) >> 24) | ((valor & 0x010000) >> 15) | ((valor & 0x0100) >> 6) | ((valor & 0x01) << 3)

                        last_col = (self.col_range - 1)<<3
                        for w in range (x_a_offset):
                            scr.addstr(row+z, last_col - x_a_offset + (w<<1), "██", curses.color_pair(self.color+tile_rom_pixels[w]))
                    else:
                        for z in range(0,8):
                            valor = self.m_memory.rom_map[EPROM_Type.TILE].rom_data[(code<<3)+z]
                            if valor == 0:
                                tile_rom_pixels[0] = 0
                                tile_rom_pixels[1] = 0
                                tile_rom_pixels[2] = 0
                                tile_rom_pixels[3] = 0
                                tile_rom_pixels[4] = 0
                                tile_rom_pixels[5] = 0
                                tile_rom_pixels[6] = 0
                                tile_rom_pixels[7] = 0
                            else:
                                tile_rom_pixels[0] = ((valor & 0x80000000) >> 31) | ((valor & 0x800000) >> 22) | ((valor & 0x8000) >> 13) | ((valor & 0x80) >> 4) 
                                tile_rom_pixels[1] = ((valor & 0x40000000) >> 30) | ((valor & 0x400000) >> 21) | ((valor & 0x4000) >> 12) | ((valor & 0x40) >> 3) 
                                tile_rom_pixels[2] = ((valor & 0x20000000) >> 29) | ((valor & 0x200000) >> 20) | ((valor & 0x2000) >> 11) | ((valor & 0x20) >> 2) 
                                tile_rom_pixels[3] = ((valor & 0x10000000) >> 28) | ((valor & 0x100000) >> 19) | ((valor & 0x1000) >> 10) | ((valor & 0x10) >> 1) 
                                tile_rom_pixels[4] = ((valor & 0x08000000) >> 27) | ((valor & 0x080000) >> 18) | ((valor & 0x0800) >> 9) | (valor & 0x08) 
                                tile_rom_pixels[5] = ((valor & 0x04000000) >> 26) | ((valor & 0x040000) >> 17) | ((valor & 0x0400) >> 8) | ((valor & 0x04) << 1) 
                                tile_rom_pixels[6] = ((valor & 0x02000000) >> 25) | ((valor & 0x020000) >> 16) | ((valor & 0x0200) >> 7) | ((valor & 0x02) << 2) 
                                tile_rom_pixels[7] = ((valor & 0x01000000) >> 24) | ((valor & 0x010000) >> 15) | ((valor & 0x0100) >> 6) | ((valor & 0x01) << 3)
                            
                            
                            scr.addstr(row+z, col8 - x_a_offset, "██", curses.color_pair(self.color+tile_rom_pixels[0]))
                            scr.addstr(row+z, col8 - x_a_offset +2, "██", curses.color_pair(self.color+tile_rom_pixels[1]))
                            scr.addstr(row+z, col8 - x_a_offset +4, "██", curses.color_pair(self.color+tile_rom_pixels[2]))
                            scr.addstr(row+z, col8 - x_a_offset +6, "██", curses.color_pair(self.color+tile_rom_pixels[3]))
                            scr.addstr(row+z, col8 - x_a_offset +8, "██", curses.color_pair(self.color+tile_rom_pixels[4]))
                            scr.addstr(row+z, col8 - x_a_offset +10, "██", curses.color_pair(self.color+tile_rom_pixels[5]))
                            scr.addstr(row+z, col8 - x_a_offset +12, "██", curses.color_pair(self.color+tile_rom_pixels[6]))
                            scr.addstr(row+z, col8 - x_a_offset +14, "██", curses.color_pair(self.color+tile_rom_pixels[7]))

                        
                        # if (col == 35 and x_a_offset < 14):
                        #     for w in range(0, 14-x_a_offset+1, 2):
                        #         scr.addstr(row+z, col8+w,   "██", curses.color_pair(self.color+tile_rom_pixels[w>>1]))
                        # elif (col == 0 and x_a_offset < 14):
                        #     for w in range(x_a_offset,15,2):
                        # else:
                        #     col_offset = col8 + x_a_offset
                        #     scr.addstr(row+z, col_offset,   "██", curses.color_pair(self.color+tile_rom_pixels[0]))
                        #     scr.addstr(row+z, col_offset+2, "██", curses.color_pair(self.color+tile_rom_pixels[1]))
                        #     scr.addstr(row+z, col_offset+4, "██", curses.color_pair(self.color+tile_rom_pixels[2]))
                        #     scr.addstr(row+z, col_offset+6, "██", curses.color_pair(self.color+tile_rom_pixels[3]))
                        #     scr.addstr(row+z, col_offset+8, "██", curses.color_pair(self.color+tile_rom_pixels[4]))
                        #     scr.addstr(row+z, col_offset+10, "██", curses.color_pair(self.color+tile_rom_pixels[5]))
                        #     scr.addstr(row+z, col_offset+12, "██", curses.color_pair(self.color+tile_rom_pixels[6]))
                        #     scr.addstr(row+z, col_offset+14, "██", curses.color_pair(self.color+tile_rom_pixels[7]))
                    #scr.refresh()


                    ### LAYER B ###
                    #NUM_LAYER = 2
                    #tile_index = row_table[ROW_START + (row>>3)] + COL_START + col
                    tile_index = row_table[ROW_START + (row>>3)] + (((layer_b_scroll_x>>3) + col + 0x0e)%0x40)
                    
                    
                    code = self.m_memory.read_RAM_entry_data(3,LAYER_B_CODE_BASE+tile_index)
                
                    attr = self.m_memory.read_RAM_entry_data(3,LAYER_B_ATTR_BASE+tile_index)
                    bank = self.m_mapper.m_k052109_charrombank[(attr & 0x0C)>>2]
                    
                    #flags = 0
                    #priority = 0
                    
                    attr = (attr & 0xf3) | ((bank & 0x03)<<2)
                    bank >>=2
                    #flipy = attr  & 0x02
                    
                    code |= ((attr & 0x3f) << 8) | (bank << 14)
                    self.color = (8 + ((attr & 0xc0) >> 6))<<4 # 2 bits superiores segun la capa (FIX 00, LAYER A 01, LAYER B 10), 2 bits inferiores    

                    #code=0x77
                    for z in range(0,8):
                        valor = self.m_memory.rom_map[EPROM_Type.TILE].rom_data[(code<<3)+z]
                        if valor == 0:
                            tile_rom_pixels[0] = 0
                            tile_rom_pixels[1] = 0
                            tile_rom_pixels[2] = 0
                            tile_rom_pixels[3] = 0
                            tile_rom_pixels[4] = 0
                            tile_rom_pixels[5] = 0
                            tile_rom_pixels[6] = 0
                            tile_rom_pixels[7] = 0
                        else:
                            tile_rom_pixels[0] = ((valor & 0x80000000) >> 31) | ((valor & 0x800000) >> 22) | ((valor & 0x8000) >> 13) | ((valor & 0x80) >> 4) 
                            tile_rom_pixels[1] = ((valor & 0x40000000) >> 30) | ((valor & 0x400000) >> 21) | ((valor & 0x4000) >> 12) | ((valor & 0x40) >> 3) 
                            tile_rom_pixels[2] = ((valor & 0x20000000) >> 29) | ((valor & 0x200000) >> 20) | ((valor & 0x2000) >> 11) | ((valor & 0x20) >> 2) 
                            tile_rom_pixels[3] = ((valor & 0x10000000) >> 28) | ((valor & 0x100000) >> 19) | ((valor & 0x1000) >> 10) | ((valor & 0x10) >> 1) 
                            tile_rom_pixels[4] = ((valor & 0x08000000) >> 27) | ((valor & 0x080000) >> 18) | ((valor & 0x0800) >> 9) | (valor & 0x08) 
                            tile_rom_pixels[5] = ((valor & 0x04000000) >> 26) | ((valor & 0x040000) >> 17) | ((valor & 0x0400) >> 8) | ((valor & 0x04) << 1) 
                            tile_rom_pixels[6] = ((valor & 0x02000000) >> 25) | ((valor & 0x020000) >> 16) | ((valor & 0x0200) >> 7) | ((valor & 0x02) << 2) 
                            tile_rom_pixels[7] = ((valor & 0x01000000) >> 24) | ((valor & 0x010000) >> 15) | ((valor & 0x0100) >> 6) | ((valor & 0x01) << 3)

                        if tile_rom_pixels[0] != 0: scr.addstr(row+z, col8,   "██", curses.color_pair(self.color+tile_rom_pixels[0]))
                        if tile_rom_pixels[1] != 0: scr.addstr(row+z, col8+2, "██", curses.color_pair(self.color+tile_rom_pixels[1]))
                        if tile_rom_pixels[2] != 0: scr.addstr(row+z, col8+4, "██", curses.color_pair(self.color+tile_rom_pixels[2]))
                        if tile_rom_pixels[3] != 0: scr.addstr(row+z, col8+6, "██", curses.color_pair(self.color+tile_rom_pixels[3]))
                        if tile_rom_pixels[4] != 0: scr.addstr(row+z, col8+8, "██", curses.color_pair(self.color+tile_rom_pixels[4]))
                        if tile_rom_pixels[5] != 0: scr.addstr(row+z, col8+10, "██", curses.color_pair(self.color+tile_rom_pixels[5]))
                        if tile_rom_pixels[6] != 0: scr.addstr(row+z, col8+12, "██", curses.color_pair(self.color+tile_rom_pixels[6]))
                        if tile_rom_pixels[7] != 0: scr.addstr(row+z, col8+14, "██", curses.color_pair(self.color+tile_rom_pixels[7]))

                    #scr.refresh()
                    ### LAYER FIX ###
                    #NUM_LAYER = 0
                    tile_index = row_table[ROW_START + (row>>3)] + COL_START + col
                    
                    code = self.m_memory.read_RAM_entry_data(3,FIX_CODE_BASE+tile_index)
                    #code = self.m_memory.read_RAM_entry_data(3,FIX_CODE_BASE+tile_index) & 0xef #simulated error on VRAM output
                    attr = self.m_memory.read_RAM_entry_data(3,FIX_ATTR_BASE+tile_index)
                    bank = self.m_mapper.m_k052109_charrombank[(attr & 0x0C)>>2]
                    
                    #flags = 0
                    #priority = 0
                    
                    attr = (attr & 0xf3) | ((bank & 0x03)<<2)
                    bank >>=2
                    #flipy = attr  & 0x02
                    
                    code |= ((attr & 0x3f) << 8) | (bank << 14)
                    self.color = ((attr & 0xc0) >> 6)<<4 # 2 bits superiores segun la capa (FIX 00, LAYER A 01, LAYER B 10), 2 bits inferiores    

                    #code=0x77
                    for z in range(0,8):
                        valor = self.m_memory.rom_map[EPROM_Type.TILE].rom_data[(code<<3)+z]
                        if valor == 0:
                            tile_rom_pixels[0] = 0
                            tile_rom_pixels[1] = 0
                            tile_rom_pixels[2] = 0
                            tile_rom_pixels[3] = 0
                            tile_rom_pixels[4] = 0
                            tile_rom_pixels[5] = 0
                            tile_rom_pixels[6] = 0
                            tile_rom_pixels[7] = 0
                        else:
                            tile_rom_pixels[0] = ((valor & 0x80000000) >> 31) | ((valor & 0x800000) >> 22) | ((valor & 0x8000) >> 13) | ((valor & 0x80) >> 4) 
                            tile_rom_pixels[1] = ((valor & 0x40000000) >> 30) | ((valor & 0x400000) >> 21) | ((valor & 0x4000) >> 12) | ((valor & 0x40) >> 3) 
                            tile_rom_pixels[2] = ((valor & 0x20000000) >> 29) | ((valor & 0x200000) >> 20) | ((valor & 0x2000) >> 11) | ((valor & 0x20) >> 2) 
                            tile_rom_pixels[3] = ((valor & 0x10000000) >> 28) | ((valor & 0x100000) >> 19) | ((valor & 0x1000) >> 10) | ((valor & 0x10) >> 1) 
                            tile_rom_pixels[4] = ((valor & 0x08000000) >> 27) | ((valor & 0x080000) >> 18) | ((valor & 0x0800) >> 9) | (valor & 0x08) 
                            tile_rom_pixels[5] = ((valor & 0x04000000) >> 26) | ((valor & 0x040000) >> 17) | ((valor & 0x0400) >> 8) | ((valor & 0x04) << 1) 
                            tile_rom_pixels[6] = ((valor & 0x02000000) >> 25) | ((valor & 0x020000) >> 16) | ((valor & 0x0200) >> 7) | ((valor & 0x02) << 2) 
                            tile_rom_pixels[7] = ((valor & 0x01000000) >> 24) | ((valor & 0x010000) >> 15) | ((valor & 0x0100) >> 6) | ((valor & 0x01) << 3)

                        if tile_rom_pixels[0] != 0: scr.addstr(row+z, col8,   "██", curses.color_pair(self.color+tile_rom_pixels[0]))
                        if tile_rom_pixels[1] != 0: scr.addstr(row+z, col8+2, "██", curses.color_pair(self.color+tile_rom_pixels[1]))
                        if tile_rom_pixels[2] != 0: scr.addstr(row+z, col8+4, "██", curses.color_pair(self.color+tile_rom_pixels[2]))
                        if tile_rom_pixels[3] != 0: scr.addstr(row+z, col8+6, "██", curses.color_pair(self.color+tile_rom_pixels[3]))
                        if tile_rom_pixels[4] != 0: scr.addstr(row+z, col8+8, "██", curses.color_pair(self.color+tile_rom_pixels[4]))
                        if tile_rom_pixels[5] != 0: scr.addstr(row+z, col8+10, "██", curses.color_pair(self.color+tile_rom_pixels[5]))
                        if tile_rom_pixels[6] != 0: scr.addstr(row+z, col8+12, "██", curses.color_pair(self.color+tile_rom_pixels[6]))
                        if tile_rom_pixels[7] != 0: scr.addstr(row+z, col8+14, "██", curses.color_pair(self.color+tile_rom_pixels[7]))

            #linea = f"TCYCLE:{self.m_kon2_cpu.m_tcount:010d} FRAME:{self.frame_cnt:06d} BNK0 {self.m_mapper.m_k052109_charrombank[0]:02x} BNK1:{self.m_mapper.m_k052109_charrombank[1]:02x} BNK2:{self.m_mapper.m_k052109_charrombank[2]:02x} BNK3:{self.m_mapper.m_k052109_charrombank[3]:02x}"
            scroll_info_str = f"LAYER A X-scroll:{layer_a_scroll_x:03d} LAYER B X-scroll:{layer_b_scroll_x:03d}"
            #scr.addstr(225, 1, linea, curses.color_pair(15))
            scr.addstr(226, 1, scroll_info_str, curses.color_pair(15))
            scr.refresh()

if __name__ == "__main__":
    aliens = aliens_machine()
