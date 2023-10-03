from enum import Enum
from net.binary import Bin
from net.ipacket import IPacket, Field
from net.opcode import Opcode


class CalcError(Enum):
    Ok = 0
    InvalidInput = 1
    DivByZero = 2


class CalcResponse(IPacket):
    opcode = Opcode.CalculationResult

    def __init__(self):
        self.error = Field(Bin.Int32, 0)
        self.result = Field(Bin.Double, 0)
        super().__init__()
