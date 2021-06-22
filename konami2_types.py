#konami2_types.py
from enum import Enum
from m6809_types import IRQLINE

class KIRQLINE(Enum):
    KONAMI_IRQ_LINE = IRQLINE.M6809_IRQ_LINE.value
    KONAMI_FIRQ_LINE = IRQLINE.M6809_FIRQ_LINE.value

# print(KIRQLINE.KONAMI_FIRQ_LINE.value)    