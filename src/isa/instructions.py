from enum import Enum


class InstructionOpcode(Enum):
    # Load/Store Instructions
    LUI = "1110000"
    LLI = "1110001"
    LW = "0000000"
    SW = "0000001"
    LWR = "1010010"
    SWR = "1010011"
    MV = "1010101"

    # Arithmetic Instructions
    ADD = "1100000"
    ADDI = "1110010"
    SUB = "1100001"
    MUL = "1100010"
    DIV = "1100011"
    REM = "1100100"
    NEG = "1010100"

    # Logical Instructions
    AND = "1100101"
    OR = "1100110"
    XOR = "1100111"
    NOT = "1010000"

    # Shift Instructions
    SHL = "1101000"
    SHR = "1101001"

    # Comparison Instructions
    CMP = "1010001"

    # Jump Instructions
    JR = "1000000"
    JAL = "0000010"
    JO = "0010000"
    JZ = "0010001"
    JNZ = "0010010"

    # Set Flag Instructions
    SETEQ = "1000010"
    SETNE = "1000011"
    SETGE = "1000100"
    SETLE = "1000101"
    SETSG = "1000110"
    SETSL = "1000111"

    # System Instructions
    RETI = "0110000"
    HALT = "0110001"

    @property
    def alias(self) -> str:
        return self.name

    @property
    def bincode(self) -> str:
        return self.value
