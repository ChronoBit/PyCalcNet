import struct
from enum import Enum


class Bin(Enum):
    UInt8 = 0
    Int8 = 1
    UInt16 = 2
    Int16 = 3
    UInt32 = 4
    Int32 = 5
    UInt64 = 6
    Int64 = 7
    Float = 8
    Double = 9
    String = 10
    List = 11


def pack_string(value):
    if value is None or len(value) == 0:
        return struct.pack("I", 0)
    value_bytes = value.encode('utf-8')
    sz = len(value_bytes)
    if sz == 0:
        return struct.pack("I", 0)
    packed_length = struct.pack("I", sz)
    packed_value = struct.pack(f"{sz}s", value_bytes)
    return packed_length + packed_value


packers = {
    Bin.UInt8: lambda value: struct.pack("B", value),
    Bin.Int8: lambda value: struct.pack("b", value),
    Bin.UInt16: lambda value: struct.pack("H", value),
    Bin.Int16: lambda value: struct.pack("h", value),
    Bin.UInt32: lambda value: struct.pack("I", value),
    Bin.Int32: lambda value: struct.pack("i", value),
    Bin.UInt64: lambda value: struct.pack("Q", value),
    Bin.Int64: lambda value: struct.pack("q", value),
    Bin.Float: lambda value: struct.pack("f", value),
    Bin.Double: lambda value: struct.pack("d", value),
    Bin.String: pack_string
}


class BinaryWriter:
    def __init__(self):
        self.buffer = bytearray()

    def pack_list(self, item_type: Bin, value):
        sz = len(value)
        self.buffer.extend(struct.pack('I', sz))
        if sz == 0:
            return
        for item in value:
            data = packers[item_type](item)
            self.buffer.extend(data)

    def pack(self, bin: Bin, value, item_type: Bin = None):
        if bin is Bin.List:
            self.pack_list(item_type, value)
            return
        data = packers[bin](value)
        self.buffer.extend(data)


unpackers = {
    Bin.UInt8: lambda br: br.unpack_from("B"),
    Bin.Int8: lambda br: br.unpack_from("b"),
    Bin.UInt16: lambda br: br.unpack_from("H"),
    Bin.Int16: lambda br: br.unpack_from("h"),
    Bin.UInt32: lambda br: br.unpack_from("I"),
    Bin.Int32: lambda br: br.unpack_from("i"),
    Bin.UInt64: lambda br: br.unpack_from("Q"),
    Bin.Int64: lambda br: br.unpack_from("q"),
    Bin.Float: lambda br: br.unpack_from("f"),
    Bin.Double: lambda br: br.unpack_from("d"),
    Bin.String: lambda br: br.unpack_from("s"),
}


class BinaryReader:
    def __init__(self, data: bytes):
        self.buffer = data
        self.offset = 0

    def unpack_from(self, fmt):
        if self.offset >= len(self.buffer) - 1:
            raise ValueError('Data is end')
        if fmt == 's':
            count = struct.unpack_from('I', self.buffer, self.offset)[0]
            if count > 65536:
                raise ValueError('Too many large string')
            val = struct.unpack_from(f'{count}s', self.buffer, self.offset + 4)[0]
            self.offset += 4 + count
            return val.decode('utf-8')
        sz = struct.calcsize(fmt)
        val = struct.unpack_from(fmt, self.buffer, self.offset)[0]
        self.offset += sz
        return val

    def unpack_list(self, item_type: Bin):
        count = self.unpack_from('I')
        if count > 4096:
            raise ValueError('Too many large array')
        res = list()
        for i in range(count):
            res.append(unpackers[item_type](self))
        return res

    def unpack(self, bin_type: Bin, item_type: Bin = None):
        if bin_type is Bin.List:
            return self.unpack_list(item_type)
        return unpackers[bin_type](self)
