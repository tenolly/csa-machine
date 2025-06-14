from isa.constants import INSTR_OPCODE_SIZE, REG_ID_SIZE, WORD_SIZE
from isa.instructions import AddressingMode, InstructionOpcode
from isa.registers import RegisterCode

from ..units.common.helpers import convert_to_signed


def get_register_name(register_code: str) -> str:
    for reg_enum in RegisterCode:
        if reg_enum.value == register_code:
            return reg_enum.name
    raise ValueError(f"unknown register {register_code}")


def string_repr_instruction(binary_instruction: str) -> str:
    if not binary_instruction or len(binary_instruction) != WORD_SIZE:
        raise ValueError("instruction must be 32 bits long")

    opcode_start_bit = WORD_SIZE - INSTR_OPCODE_SIZE
    opcode_full_bin = binary_instruction[opcode_start_bit:WORD_SIZE]
    addressing_mode_bin = opcode_full_bin[:3]

    mnemonic = None
    instruction_type = None

    for op_enum in InstructionOpcode:
        if op_enum.bincode == opcode_full_bin:
            mnemonic = op_enum.alias
            instruction_type = op_enum
            break

    if instruction_type is None:
        raise ValueError(f"unknown instruction opcode: {opcode_full_bin}")

    try:
        addressing_mode = AddressingMode(addressing_mode_bin)
    except ValueError:
        raise ValueError(f"unknown addressing mode: {addressing_mode_bin}")

    if addressing_mode == AddressingMode.ABSOLUTE:
        reg_start_idx = opcode_start_bit - REG_ID_SIZE
        addr_end_idx = reg_start_idx

        addr_bin = binary_instruction[:addr_end_idx]
        reg_bin = binary_instruction[reg_start_idx:opcode_start_bit]

        address = int(addr_bin, 2)
        register_name = get_register_name(reg_bin)

        if instruction_type in [InstructionOpcode.LW, InstructionOpcode.SW, InstructionOpcode.JAL]:
            return f"{mnemonic} {register_name}, 0x{address:0X}"

        raise ValueError(f"unexpected instruction for absolute addressing: {mnemonic}")

    elif addressing_mode == AddressingMode.RELATIVE:
        value_bin = binary_instruction[:opcode_start_bit]
        value = convert_to_signed(int(value_bin, 2), len(value_bin))

        if instruction_type in [InstructionOpcode.JO, InstructionOpcode.JZ, InstructionOpcode.JNZ]:
            return f"{mnemonic} 0x{value:0X}"

        raise ValueError(f"unexpected instruction for relative addressing: {mnemonic}")

    elif addressing_mode == AddressingMode.NO_ADDRESS:
        if instruction_type in [InstructionOpcode.RETI, InstructionOpcode.HALT]:
            return mnemonic

        raise ValueError(f"unexpected instruction for no_address addressing: {mnemonic}")

    elif addressing_mode == AddressingMode.REGISTER_1:
        reg1_bin = binary_instruction[opcode_start_bit - REG_ID_SIZE:opcode_start_bit]
        register1_name = get_register_name(reg1_bin)

        if instruction_type == InstructionOpcode.JR:
            return f"{mnemonic} {register1_name}"

        if instruction_type in [
            InstructionOpcode.SETEQ, InstructionOpcode.SETNE,
            InstructionOpcode.SETGE, InstructionOpcode.SETLE, InstructionOpcode.SETSG,
            InstructionOpcode.SETSL,
        ]:
            return f"{mnemonic} {register1_name}"

        raise ValueError(f"unexpected instruction for 1-register addressing: {mnemonic}")

    elif addressing_mode == AddressingMode.REGISTER_2:
        reg2_bin = binary_instruction[opcode_start_bit - (2 * REG_ID_SIZE):opcode_start_bit - REG_ID_SIZE]
        reg1_bin = binary_instruction[opcode_start_bit - REG_ID_SIZE:opcode_start_bit]

        register1_name = get_register_name(reg1_bin)
        register2_name = get_register_name(reg2_bin)

        if instruction_type in [
            InstructionOpcode.NEG, InstructionOpcode.NOT,
            InstructionOpcode.CMP, InstructionOpcode.MV,
        ]:
            return f"{mnemonic} {register1_name}, {register2_name}"

        if instruction_type == InstructionOpcode.LWR:
            return f"{mnemonic} {register1_name}, {register2_name}"

        if instruction_type == InstructionOpcode.SWR:
            return f"{mnemonic} {register1_name}, {register2_name}"

        raise ValueError(f"unexpected instruction for 2-register addressing: {mnemonic}")

    elif addressing_mode == AddressingMode.REGISTER_3:
        reg3_bin = binary_instruction[opcode_start_bit - (3 * REG_ID_SIZE):opcode_start_bit - (2 * REG_ID_SIZE)]
        reg2_bin = binary_instruction[opcode_start_bit - (2 * REG_ID_SIZE):opcode_start_bit - REG_ID_SIZE]
        reg1_bin = binary_instruction[opcode_start_bit - REG_ID_SIZE:opcode_start_bit]

        register1_name = get_register_name(reg1_bin)
        register2_name = get_register_name(reg2_bin)
        register3_name = get_register_name(reg3_bin)

        if instruction_type in [
            InstructionOpcode.ADD, InstructionOpcode.SUB, InstructionOpcode.MUL,
            InstructionOpcode.DIV, InstructionOpcode.REM, InstructionOpcode.AND,
            InstructionOpcode.OR, InstructionOpcode.XOR, InstructionOpcode.SHL,
            InstructionOpcode.SHR,
        ]:
            return f"{mnemonic} {register1_name}, {register2_name}, {register3_name}"

        raise ValueError(f"unexpected instruction for 3-register addressing: {mnemonic}")

    elif addressing_mode == AddressingMode.DIRECT_LOAD:
        value_bin = binary_instruction[:opcode_start_bit - REG_ID_SIZE]
        reg_bin = binary_instruction[opcode_start_bit - REG_ID_SIZE:opcode_start_bit]

        value = convert_to_signed(int(value_bin, 2), len(value_bin))
        register_name = get_register_name(reg_bin)

        if instruction_type in [InstructionOpcode.ADDI, InstructionOpcode.LUI, InstructionOpcode.LLI]:
            return f"{mnemonic} {register_name}, 0x{value:0X}"

        raise ValueError(f"unexpected instruction for direct load addressing: {mnemonic}")

    raise ValueError(f"unhandled instruction format (opcode: {opcode_full_bin}, addr_mode: {addressing_mode_bin})")
