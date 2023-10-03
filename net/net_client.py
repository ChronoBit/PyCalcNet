import asyncio
import struct
from net.ipacket import IPacket
from net.tcp_client import TcpClient


class NetClient:
    def __init__(self, ip, port):
        self.tcp = TcpClient(ip, port)

    async def _recv(self):
        head = await self.tcp.recv(2)
        if head is None:
            return False
        head = struct.unpack('H', head)[0]
        if head != 0x6529:
            return False

        sz = await self.tcp.recv(4)
        if sz is None:
            return False
        sz = struct.unpack('I', sz)[0]
        if sz > 64 * 1024 * 1024:
            return False

        data = await self.tcp.recv(sz)
        if data is None:
            return False
        opcode, data = struct.unpack(f'B{sz-1}s', data)
        packet = IPacket.load_packet(opcode)
        if packet is not None:
            packet.unpack_data(data)
            packet.parse()
        return True

    async def _runner(self):
        while True:
            if not self.tcp.is_connected() and not await self.tcp.connect():
                await asyncio.sleep(1)
                continue

            if not await self._recv():
                await self.tcp.disconnect()
                await asyncio.sleep(1)
                continue

    def run(self):
        return self._runner()

    async def send(self, packet: IPacket):
        opcode = packet.opcode
        if opcode is None:
            return False

        packed = packet.pack()
        data = struct.pack('H', 0x6529)
        data += struct.pack('I', len(packed) + 1)
        data += struct.pack('B', opcode.value)
        data += packed
        if not self.tcp.is_connected():
            if not await self.tcp.connect():
                return False
        return await self.tcp.send(data)
