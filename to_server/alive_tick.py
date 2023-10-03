from net.ipacket import IPacket, Field
from net.opcode import Opcode


class AliveTick(IPacket):
    opcode = Opcode.AliveTick
