from enum import IntEnum, auto


class ALUOperation(IntEnum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()

    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()

    SHL = auto()
    SHR = auto()

    NEG = auto()

    FETCH_B = auto()
    FETCH_B_SET_Z = auto()
    FETCH_B_LOWER = auto()
    FETCH_B_SHIFT_16 = auto()


class Interrupts(IntEnum):
    ZERO_DIVISION = 0b0000000000000000
    INPUT_DATA = 0b1000000000000000


class RegisterFileFetch(IntEnum):
    LEFT = auto()
    RIGHT = auto()
    BOTH = auto()
