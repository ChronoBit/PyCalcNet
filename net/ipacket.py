from net.binary import Bin, BinaryWriter, BinaryReader

opcodes = {}


class MetaRegister(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if cls.opcode is not None:
            opcodes[cls.opcode.value] = cls


class Field:
    def __init__(self, bin_type: Bin, value: object = None):
        self.bin = bin_type
        self.value = value


class FieldList(Field):
    def __init__(self, item_type: Bin, value: object = None):
        if value is None:
            value = list()
        super().__init__(Bin.List, value)
        self.item = item_type


class IPacket(metaclass=MetaRegister):
    opcode = None

    def parse(self):
        return

    @staticmethod
    def load_packet(opcode):
        if opcode not in opcodes:
            return None
        return opcodes[opcode]()

    def __init__(self):
        self._fields = {}
        fields = [attr for attr in dir(self) if
                  not callable(getattr(self, attr)) and not attr.startswith("_")]
        for field_name in fields:
            field = getattr(self, field_name)
            self.check_field(field_name, field)

    def check_field(self, name, field):
        if isinstance(field, IPacket):
            self._fields[name] = field
        elif isinstance(field, Field):
            self._fields[name] = field

    def __getattribute__(self, item):
        try:
            val = object.__getattribute__(self, item)
            if item != '_fields' and item in self._fields:
                if isinstance(val, Field):
                    return val.value
            return val
        except AttributeError:
            return None

    def __setattr__(self, key, value):
        if self._fields is not None and key != '_fields' and key in self._fields:
            tp = self._fields[key]
            if isinstance(tp, Field):
                tp.value = value
                return
        object.__setattr__(self, key, value)

    def pack(self, bw: BinaryWriter = None):
        if bw is None:
            bw = BinaryWriter()
        for name in self._fields:
            field = self._fields[name]
            if isinstance(field, FieldList):
                bw.pack(field.bin, field.value, field.item)
            elif isinstance(field, Field):
                bw.pack(field.bin, field.value)
            elif isinstance(field, IPacket):
                field.pack(bw)
        return bw.buffer

    def unpack_data(self, data):
        br = BinaryReader(data)
        self.unpack(br)

    def unpack(self, br: BinaryReader):
        for name in self._fields:
            field = self._fields[name]
            if isinstance(field, FieldList):
                field.value = br.unpack(field.bin, field.item)
            elif isinstance(field, Field):
                field.value = br.unpack(field.bin)
            elif isinstance(field, IPacket):
                field.unpack(br)
