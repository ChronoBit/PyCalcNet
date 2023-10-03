from net.binary import Bin
from net.ipacket import IPacket, FieldList
from net.opcode import Opcode


class CalcRequest(IPacket):
    opcode = Opcode.CalculateExpression

    def __init__(self):
        self.operations = FieldList(Bin.String)
        super().__init__()
