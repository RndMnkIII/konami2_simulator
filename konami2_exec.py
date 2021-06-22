#konami2_exec.py
from typing import NamedTuple, Callable
from ctypes import byref, pointer, Union, Structure, c_uint, c_int, c_ulong, c_long, c_uint8, c_int8, c_uint16, c_int16, c_uint32, c_int32
#from konami2_label_table import label_table_jump
from m6809 import m6809_base_device
from m6809_types import ADRMOD, exgtfr_register, FLAGS, CPUVECT, LINEDEF, line_state
from konami2_types import KIRQLINE

class Konami2StateMachine(object):
    def execute_one(self) -> None:
        self.cpu_state_table_jump[self.pop_state()](self)








