import asyncio
import socket


class TcpClient:
    PART_SIZE = 65536

    def __init__(self, ip, port):
        self.address = (ip, port)
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self._connected = False
        self.on_connected = None

    async def create_socket(self):
        self.reader, self.writer = await asyncio.open_connection(self.address[0], self.address[1])

    def _on_connect(self, val):
        flag = self._connected != val
        self._connected = val
        if flag and self.on_connected:
            self.on_connected(self._connected)

    async def connect(self):
        try:
            if self._connected:
                await self.disconnect()
            await self.create_socket()
            self._on_connect(True)
            return True
        except ConnectionError:
            self._on_connect(False)
            return False

    async def disconnect(self):
        self._on_connect(False)
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except ConnectionError:
            return False
        self.reader = self.writer = None

    def is_connected(self):
        return self._connected

    async def send(self, data):
        try:
            self.writer.write(data)
            await self.writer.drain()
            return True
        except ConnectionError:
            return False

    async def _recv(self, size):
        try:
            data = await self.reader.read(size)
            if len(data) == 0:
                return None
            return data
        except ConnectionError:
            return None

    async def recv(self, size):
        if size > self.PART_SIZE:
            i = 0
            res = bytearray()
            while i < size:
                total = min(size - i, self.PART_SIZE)
                data = await self._recv(total)
                if data is None:
                    return None
                res.extend(data)
                i += self.PART_SIZE
            return res
        return await self._recv(size)
