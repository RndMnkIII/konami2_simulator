#m6809_execi.py
#from m6809_execi import device_execute_interface, device_input
#Execute interface
from m6809_types import ADRMOD, exgtfr_register, FLAGS, CPUVECT, LINEDEF, line_state, IRQLINE
from ctypes import addressof, byref, pointer, Union, Structure, c_int, c_ulong, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32
from typing import NamedTuple, List, TypeVar, Type

class device_execute_interface():
    MAX_INPUT_LINES = 64+3

    def __init__(self) -> None:
        self.m_curstate:line_state = line_state.HOLD_LINE
        self.m_curvector:int = 0
        self.m_stored_vector:int = 0
        self.m_linenum:int = 0
        self.m_execute:device_execute_interface = None
        self.m_input:List[device_input] = [device_input() for _ in range(self.MAX_INPUT_LINES)]
    
    def start(self, linenum: int) -> None:
        self.m_linenum = linenum
        self.reset()


    def execute_set_input(self, linenum: int, state: int) -> None:
        pass

    def default_irq_vector(self, linenum: int) -> int:
        return self.execute_default_irq_vector(linenum)

    def execute_default_irq_vector(self, linenum: int) -> int:
        return 0

    def standard_irq_callback(self, irqline: int) -> int:
        vector:int = self.m_input[irqline].default_irq_callback()
        return vector
     
class device_input():
    m_execute: device_execute_interface = None
    m_linenum: int = 0
    m_stored_vector: c_int32 = 0
    m_curvector : c_int32 = 0
    m_curstate : c_uint8 = 0
    #m_queue : List =  list(range(32))
    #m_qindex : int = 0

    def start(self, execute: device_execute_interface, linenum: int) -> None:
        self.m_execute = execute
        self.m_linenum = linenum

    def reset(self) -> None:
        self.m_curvector = m_execute.default_irq_vector(self.m_linenum)
        #self.m_qindex = 0

    def set_vector(self, vector: int) -> None:
        self.m_stored_vector = vector

    def default_irq_callback(self) -> int:
        vector: int = self.m_curvector
        if(self.m_curstate == line_state.HOLD_LINE.value):
            #print("default_irq_callback HOLD")
            self.m_execute.execute_set_input(self.m_linenum, line_state.CLEAR_LINE.value)
            self.m_curstate = line_state.CLEAR_LINE.value

# dei = device_execute_interface()
# dei.standard_irq_callback(IRQLINE.M6809_IRQ_LINE.value)
# print(f"Current state {dei.m_curstate}")

