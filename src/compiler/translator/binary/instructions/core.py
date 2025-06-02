from ..constants import INSTR_OPCODE_SIZE, REG_ID_SIZE


class InstructionOpcode:
    def __init__(self, alias: str, bincode: str):
        if len(bincode) != INSTR_OPCODE_SIZE:
            raise ValueError(
                f"failed to init {self.__class__.__name__}({alias!r}, {bincode!r}), "
                f"because bincode's length must be equal to {INSTR_OPCODE_SIZE}.",
            )

        self.alias = alias
        self.bincode = bincode

    def __repr__(self):
        return f"{self.__class__.__name__}({self.alias!r}, {self.bincode!r})"


class Register:
    def __init__(self, alias: str, bincode: str):
        if len(bincode) != REG_ID_SIZE:
            raise ValueError(
                f"failed to init {self.__class__.__name__}({alias!r}, {bincode!r}), "
                f"because bincode's length must be equal to {REG_ID_SIZE}.",
            )

        self.alias = alias
        self.bincode = bincode

    def __repr__(self):
        return f"{self.__class__.__name__}({self.alias!r}, {self.bincode!r})"


class Value:
    def __init__(self, value: int):
        self.deccode = value
        self.bincode = bin(value)[2:]
        self.hexcode = "0x" + hex(value)[2:].upper()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.deccode!r}, {self.bincode!r}, {self.hexcode!r})"
