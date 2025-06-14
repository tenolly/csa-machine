from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from isa.constants import INSTR_OPCODE_SIZE, REG_ID_SIZE, WORD_SIZE
from isa.instructions import InstructionOpcode
from isa.registers import RegisterCode
from machine.constants import INPUT_ADDR, START_ADDR

from .common.components.data_latch import DataLatch
from .common.components.data_selector import DataSelector
from .common.enums import ALUOperation, Interrupts, RegisterFileFetch
from .common.exceptions import MachineLimitException, MachineStop
from .common.helpers import convert_to_signed

if TYPE_CHECKING:
    from .datapath import Datapath


class _InterruptHandler:
    def __init__(self, control_unit: ControlUnit):
        self.control_unit: ControlUnit = control_unit

        self.irq: DataLatch = DataLatch(bitsize=16)
        """
        Interrupt Request (input - Datapath interrupt signals)

        Using is hidden by the Interrupt Handler implementation.

        Output data bus leads to:
            - PC Multiplexer
        """

        self.ie: DataLatch = DataLatch(bitsize=1, defult_value=1)
        """
        Interrupt Enable (input - signals)

        Using is hidden by the Interrupt Handler implementation.
        """

        self.ipc: DataLatch = DataLatch()
        """
        Interrupt Program Counter (input - Program Counter)

        Output data bus leads to:
            - Interrupt Handler Out Multiplexer
        """

        self.out: DataSelector = DataSelector(2)
        """
        Interrupt Handler Out Multiplexer (2 inputs):
            0 - Interrupt Program Counter
            1 - Interrupt Vector

        Output data bus leads to:
            - PC Multiplexer
        """

    def signal_latch_ipc(self) -> None:
        if self.ie.get_value() == 0:
            return

        self.ipc.latch_value(value := self.control_unit.pc.get_value())
        self.out.set_input_value(0, value)

    def signal_sel_out(self, input_index: int) -> None:
        self.out.select_input(input_index)
        self.control_unit.mux_pc.set_input_value(1, self.out.get_selected_value())

    def signal_check_int(self) -> bool:
        if self.ie.get_value() == 0 or self.irq.get_value() == 0:
            return False

        self.signal_set_ie(0)

        irq_value = self.irq.get_value()
        for i in range(len(str(bin(irq_value)[2:]))):
            if (irq_value & 1) == 1:
                self.signal_remove_irq(int("1" + "0" * i, 2))
                self.signal_read_and_latch_iv(i)
                break

            irq_value >>= 1

        self.signal_sel_out(1)
        self.control_unit.signal_sel_pc(1)
        self.control_unit.signal_latch_pc()

        return True

    def signal_read_and_latch_iv(self, interrupt_vector: int):
        self.out.set_input_value(1, self.control_unit.datapath.memory.read(interrupt_vector * 4))

    def signal_add_irq(self, interrupt_vector: int) -> None:
        self.irq.latch_value(self.irq.get_value() | interrupt_vector)

    def signal_remove_irq(self, interrupt_vector: int) -> None:
        self.irq.latch_value(self.irq.get_value() - interrupt_vector)

    def signal_set_ie(self, value: int) -> None:
        self.ie.latch_value(value)


class _InstructionDecoder:
    _OPCODE_MASK = int("1" * INSTR_OPCODE_SIZE, 2)
    _REGISTER_MASK = int("1" * REG_ID_SIZE, 2)

    def __init__(self, control_unit: ControlUnit):
        self.control_unit: ControlUnit = control_unit

        self.ir: DataLatch = DataLatch()
        """
        Instruction Register (input - Memory Unit)

        Decoding is hidden by the Instruction Decoder implementation.
        """

        self.opcode: DataLatch = DataLatch(bitsize=INSTR_OPCODE_SIZE)
        """Decoded instruction opcode"""

        self.imm: DataLatch = DataLatch(bitsize=WORD_SIZE - INSTR_OPCODE_SIZE)
        """Decoded immediate value"""

        self.r1: DataLatch = DataLatch(bitsize=REG_ID_SIZE)
        """Decoded Register 1"""

        self.r2: DataLatch = DataLatch(bitsize=REG_ID_SIZE)
        """Decoded Register 2"""

        self.r3: DataLatch = DataLatch(bitsize=REG_ID_SIZE)
        """Decoded Register 3"""

        self.flags: Dict[str, DataLatch] = {
            "N": DataLatch(bitsize=1),
            "Z": DataLatch(bitsize=1),
            "V": DataLatch(bitsize=1),
            "C": DataLatch(bitsize=1),
        }
        """ALU Flags (get from Datapath)"""

        self.out: DataSelector = DataSelector(12)
        """
        Instruction Decoder Out Multiplexer (12 inputs):
            0 - Decoded immediate value
            1 - Decoded Register 1
            2 - Decoded Register 2
            3 - Decoded Register 3
            4 - Decoded Register 1 and Register 2
            5 - Decoded Register 2 and Register 3
            6 - Result of (Z = 1)
            7 - Result of (Z = 0)
            8 - Result of (N = V)
            9 - Result of (N != V or Z = 1)
            10 - Result of (Z = 0 and N = V)
            11 - Result of (N != V)

        Output data bus leads to:
            - Datapath Multiplexer
        """

    def signal_read_and_latch_ir(self) -> None:
        self.ir.latch_value(value := self.control_unit.datapath.memory.read(self.control_unit.pc.get_value()))
        self.opcode.latch_value(value & self._OPCODE_MASK)

    def signal_decode_instr(self) -> None:
        instruction = self.ir.get_value()

        opcode = bin(self.opcode.get_value())[2:].zfill(INSTR_OPCODE_SIZE)
        match opcode:
            case InstructionOpcode.LUI.bincode | InstructionOpcode.LLI.bincode | InstructionOpcode.ADDI.bincode \
                    | InstructionOpcode.LW.bincode | InstructionOpcode.SW.bincode | InstructionOpcode.JAL.bincode:
                self.r1.latch_value((instruction >> INSTR_OPCODE_SIZE) & self._REGISTER_MASK)
                imm_value = instruction >> (INSTR_OPCODE_SIZE + REG_ID_SIZE)
                imm_value_size = WORD_SIZE - INSTR_OPCODE_SIZE - REG_ID_SIZE
                self.imm.latch_value(convert_to_signed(imm_value, imm_value_size))

            case InstructionOpcode.LWR.bincode | InstructionOpcode.SWR.bincode | InstructionOpcode.MV.bincode \
                    | InstructionOpcode.NEG.bincode | InstructionOpcode.NOT.bincode | InstructionOpcode.CMP.bincode:
                self.r1.latch_value((instruction >> INSTR_OPCODE_SIZE) & self._REGISTER_MASK)
                self.r2.latch_value((instruction >> (INSTR_OPCODE_SIZE + REG_ID_SIZE)) & self._REGISTER_MASK)

            case InstructionOpcode.ADD.bincode | InstructionOpcode.SUB.bincode | InstructionOpcode.MUL.bincode \
                    | InstructionOpcode.DIV.bincode | InstructionOpcode.REM.bincode | InstructionOpcode.AND.bincode \
                    | InstructionOpcode.OR.bincode | InstructionOpcode.XOR.bincode | InstructionOpcode.SHL.bincode \
                    | InstructionOpcode.SHR.bincode:
                self.r1.latch_value((instruction >> INSTR_OPCODE_SIZE) & self._REGISTER_MASK)
                self.r2.latch_value((instruction >> (INSTR_OPCODE_SIZE + REG_ID_SIZE)) & self._REGISTER_MASK)
                self.r3.latch_value((instruction >> (INSTR_OPCODE_SIZE + REG_ID_SIZE * 2)) & self._REGISTER_MASK)

            case InstructionOpcode.JR.bincode | InstructionOpcode.SETEQ.bincode | InstructionOpcode.SETNE.bincode \
                    | InstructionOpcode.SETGE.bincode | InstructionOpcode.SETLE.bincode \
                    | InstructionOpcode.SETSG.bincode | InstructionOpcode.SETSL.bincode:
                self.r1.latch_value((instruction >> INSTR_OPCODE_SIZE) & self._REGISTER_MASK)

            case InstructionOpcode.JO.bincode | InstructionOpcode.JZ.bincode | InstructionOpcode.JNZ.bincode:
                imm_value = instruction >> INSTR_OPCODE_SIZE
                imm_value_size = WORD_SIZE - INSTR_OPCODE_SIZE
                self.imm.latch_value(convert_to_signed(imm_value, imm_value_size))

            case InstructionOpcode.RETI.bincode | InstructionOpcode.HALT.bincode:
                pass

            case _:
                raise NotImplementedError(f"unexpected opcode {opcode}")

        self.out.set_input_value(0, self.imm.get_value())
        self.out.set_input_value(1, self.r1.get_value())
        self.out.set_input_value(2, self.r2.get_value())
        self.out.set_input_value(3, self.r3.get_value())
        self.out.set_input_value(4, (self.r1.get_value() << REG_ID_SIZE) + self.r2.get_value())
        self.out.set_input_value(5, (self.r2.get_value() << REG_ID_SIZE) + self.r3.get_value())

    def signal_sel_out(self, input_index: int) -> None:
        self.out.select_input(input_index)
        self.control_unit.mux_dp.set_input_value(1, self.out.get_selected_value())

    def signal_nzvc(self) -> None:
        for flag in "NZVC":
            self.flags[flag].latch_value(self.control_unit.datapath.alu.flags[flag].get_value())

        z, n, v = self.flags["Z"].get_value(), self.flags["N"].get_value(), self.flags["V"].get_value()
        self.out.set_input_value(6, int(z == 1))
        self.out.set_input_value(7, int(z == 0))
        self.out.set_input_value(8, int(n == v))
        self.out.set_input_value(9, int(n != v or z == 1))
        self.out.set_input_value(10, int(n == v and z == 0))
        self.out.set_input_value(11, int(n != v))


class ControlUnit:
    def __init__(self, datapath: Datapath):
        self._tick: int = 0
        self.ticks_limit: Optional[int] = None
        self.input_tokens: Dict[int, str] = {}

        self.simulation_log: List[Dict[str, Any]] = []

        self.datapath: Datapath = datapath
        self.instruction_decoder: _InstructionDecoder = _InstructionDecoder(self)
        self.interrupt_handler: _InterruptHandler = _InterruptHandler(self)

        self.mux_dp: DataSelector = DataSelector(2)
        """
        Datapath Multiplexer (2 inputs):
            0 - Program Counter
            1 - Instruction Decoder

        Output data bus leads to:
            - Datapath
        """

        self.mux_jpc: DataSelector = DataSelector(2)
        """
        JPC Multiplexer (2 inputs):
            0 - Datapath
            1 - Instruction Decoder

        Output data bus leads to:
            - Jump Program Counter
        """

        self.jpc: DataLatch = DataLatch()
        """
        Jump Program Counter (input - JPC Multiplexer)

        Output data bus leads to:
            - PC Multiplexer
        """

        self.mux_pc: DataSelector = DataSelector(3)
        """
        PC Multiplexer (3 inputs):
            0 - Jump Program Counter
            1 - Interrupt Program Counter
            2 - Program Counter [+4]

        Output data bus leads to:
            - Program Counter
        """

        self.pc: DataLatch = DataLatch(defult_value=START_ADDR)
        """
        Program Counter (input - PC Multiplexer)

        Output data bus leads to:
            - Datapath Multiplexer
            - Interrupt Program Counter
            - Memory Unit
            - PC Multiplexer
        """

        self.signal_latch_pc(init=True)

    def process_instruction(self) -> None:
        interrupted = False

        # Simple steps
        def pc_to_ipc_and_check_int():
            """IPC <- PC"""
            nonlocal interrupted
            self.interrupt_handler.signal_latch_ipc()
            interrupted = self.interrupt_handler.signal_check_int()

        def ipc_to_pc():
            """PC <- IPC"""
            self.interrupt_handler.signal_sel_out(0)
            self.signal_sel_pc(1)
            self.signal_latch_pc()

        def set_ie_1():
            """IE = 1"""
            self.interrupt_handler.signal_set_ie(1)

        def mem_pc_to_ir():
            """IR <- [PC]"""
            self.instruction_decoder.signal_read_and_latch_ir()

        def pc_plus_4_to_pc():
            """PC <- PC + 4"""
            self.signal_sel_pc(2)
            self.signal_latch_pc()

        def decode_instruction():
            """imm, R1, R2, R3 <- IR"""
            self.instruction_decoder.signal_decode_instr()

        def imm_to_alu_b():
            """ALU_B <- IR[12:31] or ALU_B <- IR[7:11]"""
            self.instruction_decoder.signal_sel_out(0)
            self.signal_sel_dp(1)
            self.datapath.signal_sel_alu_b(1)
            self.datapath.alu.signal_latch_alu_b()

        def imm_to_ar():
            """AR <- IR[12:31]"""
            self.instruction_decoder.signal_sel_out(0)
            self.signal_sel_dp(1)
            self.datapath.signal_sel_ar(2)
            self.datapath.signal_latch_ar()

        def do_alu_op(operation: ALUOperation):
            """NZVC, ALU_Out <- any alu operation"""
            self.datapath.alu.signal_alu_op(operation)

        def do_alu_op_and_store_to_br(operation: ALUOperation):
            """BR <- any alu operation"""
            do_alu_op(operation)
            self.datapath.signal_sel_br(1)
            self.datapath.signal_latch_br()

        def mem_r1_to_alu_a():
            """ALU_A <- [R1]"""
            self.instruction_decoder.signal_sel_out(1)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.LEFT)
            self.datapath.signal_sel_alu_a(0)
            self.datapath.alu.signal_latch_alu_a()

        def mem_r1_to_alu_b():
            """ALU_B <- [R1]"""
            self.instruction_decoder.signal_sel_out(1)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.RIGHT)
            self.datapath.signal_sel_alu_b(0)
            self.datapath.alu.signal_latch_alu_b()

        def mem_r1_to_alu_a_mem_r2_to_alu_b():
            """ALU_A <- [R1], ALU_B <- [R2]"""
            self.instruction_decoder.signal_sel_out(4)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.BOTH)
            self.datapath.signal_sel_alu_a(0)
            self.datapath.alu.signal_latch_alu_a()
            self.datapath.signal_sel_alu_b(0)
            self.datapath.alu.signal_latch_alu_b()

        def mem_r2_to_alu_b():
            """ALU_B <- [R2]"""
            self.instruction_decoder.signal_sel_out(2)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.RIGHT)
            self.datapath.signal_sel_alu_b(0)
            self.datapath.alu.signal_latch_alu_b()

        def br_to_alu_b():
            """ALU_B <- BR"""
            self.datapath.signal_sel_alu_b(2)
            self.datapath.alu.signal_latch_alu_b()

        def br_to_mem_r1():
            """[R1] <- BR"""
            self.instruction_decoder.signal_sel_out(1)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_write_reg()

        def br_to_mem_ar():
            self.datapath.signal_write()

        def mem_ar_to_br():
            """BR <- [AR]"""
            self.datapath.signal_read()
            self.datapath.signal_sel_br(2)
            self.datapath.signal_latch_br()

        def mem_r1_to_br():
            """BR <- [R1]"""
            self.instruction_decoder.signal_sel_out(1)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.LEFT)
            self.datapath.signal_sel_br(0)
            self.datapath.signal_latch_br()

        def mem_r1_to_ar():
            """AR <- [R1]"""
            self.instruction_decoder.signal_sel_out(1)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.RIGHT)
            self.datapath.signal_sel_ar(1)
            self.datapath.signal_latch_ar()

        def mem_r2_to_ar():
            """AR <- [R2]"""
            self.instruction_decoder.signal_sel_out(2)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.RIGHT)
            self.datapath.signal_sel_ar(1)
            self.datapath.signal_latch_ar()

        def mem_r1_to_br_mem_r2_to_ar():
            """AR <- [R2], BR <- [R1]"""
            self.instruction_decoder.signal_sel_out(4)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.BOTH)
            self.datapath.signal_sel_br(0)
            self.datapath.signal_latch_br()
            self.datapath.signal_sel_ar(1)
            self.datapath.signal_latch_ar()

        def mem_r2_to_alu_a_mem_r3_to_alu_b():
            """ALU_A <- [R2], ALU_B <- [R3]"""
            self.instruction_decoder.signal_sel_out(5)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.BOTH)
            self.datapath.signal_sel_alu_a(0)
            self.datapath.alu.signal_latch_alu_a()
            self.datapath.signal_sel_alu_b(0)
            self.datapath.alu.signal_latch_alu_b()

        def mem_r2_to_alu_a():
            """ALU_A <- [R2]"""
            self.instruction_decoder.signal_sel_out(2)
            self.signal_sel_dp(1)
            self.datapath.register_file.signal_read_reg(RegisterFileFetch.LEFT)
            self.datapath.signal_sel_alu_a(0)
            self.datapath.alu.signal_latch_alu_a()

        def flags_cmp_to_alu_b(out_index: int):
            """ALU_B <- any flags comparison in instruction decoder"""
            self.instruction_decoder.signal_sel_out(out_index)
            self.signal_sel_dp(1)
            self.datapath.signal_sel_alu_b(1)
            self.datapath.alu.signal_latch_alu_b()

        def ar_to_jpc():
            """JPC <- AR"""
            self.datapath.signal_sel_cu(0)
            self.signal_sel_jpc(0)
            self.signal_latch_jpc()

        def jpc_to_pc():
            """PC <- JPC"""
            self.signal_sel_pc(0)
            self.signal_latch_pc()

        def pc_to_alu_a():
            """ALU_A <- PC"""
            self.signal_sel_dp(0)
            self.datapath.signal_sel_alu_a(1)
            self.datapath.alu.signal_latch_alu_a()

        def br_to_jpc():
            """JPC <- BR"""
            self.datapath.signal_sel_cu(1)
            self.signal_sel_jpc(0)
            self.signal_latch_jpc()

        # Similar instructions
        def alu_unop_instr_signals(operation: ALUOperation):
            # IF
            pc_to_ipc_and_check_int()
            self.tick()

            if interrupted:
                return

            pc_plus_4_to_pc()
            self.tick()

            # ID
            decode_instruction()
            self.tick()

            # EX
            mem_r2_to_alu_a()
            self.tick()

            do_alu_op_and_store_to_br(operation)
            self.tick()

            # WB
            br_to_mem_r1()
            self.tick()

        def alu_binop_instr_signals(operation: ALUOperation):
            # IF
            pc_to_ipc_and_check_int()
            self.tick()

            if interrupted:
                return

            pc_plus_4_to_pc()
            self.tick()

            # ID
            decode_instruction()
            self.tick()

            # EX
            mem_r2_to_alu_a_mem_r3_to_alu_b()
            self.tick()

            do_alu_op_and_store_to_br(operation)
            self.tick()

            # WB
            br_to_mem_r1()
            self.tick()

        def set_instr_signals(id_out_index: int):
            # IF
            pc_to_ipc_and_check_int()
            self.tick()

            if interrupted:
                return

            pc_plus_4_to_pc()
            self.tick()

            # ID
            decode_instruction()
            flags_cmp_to_alu_b(id_out_index)
            self.tick()

            # EX
            do_alu_op_and_store_to_br(ALUOperation.FETCH_B_SET_Z)
            self.tick()

            # WB
            br_to_mem_r1()
            self.tick()

        def jump_flag_condition(z_can_be: List[int]):
            # IF
            pc_to_ipc_and_check_int()
            self.tick()

            if interrupted:
                return

            if self.instruction_decoder.flags["Z"].get_value() not in z_can_be:
                pc_plus_4_to_pc()
                self.tick()
                return

            self.tick()

            # ID
            decode_instruction()
            pc_to_alu_a()
            self.tick()

            imm_to_alu_b()
            self.tick()

            # EX
            do_alu_op_and_store_to_br(ALUOperation.ADD)
            self.tick()

            br_to_jpc()
            jpc_to_pc()
            self.tick()

        mem_pc_to_ir()
        opcode = str(bin(self.instruction_decoder.opcode.get_value())[2:]).zfill(INSTR_OPCODE_SIZE)

        match opcode:
            case InstructionOpcode.LUI.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                imm_to_alu_b()
                self.tick()

                # EX
                do_alu_op_and_store_to_br(ALUOperation.FETCH_B_SHIFT_16)
                self.tick()

                mem_r1_to_alu_a()
                br_to_alu_b()
                self.tick()

                do_alu_op_and_store_to_br(ALUOperation.ADD)
                self.tick()

                # WB
                br_to_mem_r1()
                self.tick()

            case InstructionOpcode.LLI.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                imm_to_alu_b()
                self.tick()

                # EX
                do_alu_op_and_store_to_br(ALUOperation.FETCH_B_LOWER)
                self.tick()

                # WB
                br_to_mem_r1()
                self.tick()

            case InstructionOpcode.LW.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                imm_to_ar()
                self.tick()

                # MEM
                mem_ar_to_br()
                self.tick()

                # WB
                br_to_mem_r1()
                self.tick()

            case InstructionOpcode.SW.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                imm_to_ar()
                self.tick()

                # EX
                mem_r1_to_br()
                self.tick()

                # MEM
                br_to_mem_ar()
                self.tick()

            case InstructionOpcode.LWR.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                self.tick()

                # EX
                mem_r2_to_ar()
                self.tick()

                # MEM
                mem_ar_to_br()
                self.tick()

                # WB
                br_to_mem_r1()
                self.tick()

            case InstructionOpcode.SWR.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                self.tick()

                # EX
                mem_r1_to_br_mem_r2_to_ar()
                self.tick()

                # MEM
                br_to_mem_ar()
                self.tick()

            case InstructionOpcode.MV.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                self.tick()

                # EX
                mem_r2_to_alu_b()
                self.tick()

                do_alu_op_and_store_to_br(ALUOperation.FETCH_B)
                self.tick()

                # WB
                br_to_mem_r1()
                self.tick()

            case InstructionOpcode.ADDI.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                imm_to_alu_b()
                self.tick()

                # EX
                mem_r1_to_alu_a()
                self.tick()

                do_alu_op_and_store_to_br(ALUOperation.ADD)
                self.tick()

                # MEM
                br_to_mem_r1()
                self.tick()

            case InstructionOpcode.ADD.bincode:
                alu_binop_instr_signals(ALUOperation.ADD)

            case InstructionOpcode.SUB.bincode:
                alu_binop_instr_signals(ALUOperation.SUB)

            case InstructionOpcode.MUL.bincode:
                alu_binop_instr_signals(ALUOperation.MUL)

            case InstructionOpcode.DIV.bincode:
                alu_binop_instr_signals(ALUOperation.DIV)

            case InstructionOpcode.REM.bincode:
                alu_binop_instr_signals(ALUOperation.REM)

            case InstructionOpcode.NEG.bincode:
                alu_unop_instr_signals(ALUOperation.NEG)

            case InstructionOpcode.AND.bincode:
                alu_binop_instr_signals(ALUOperation.AND)

            case InstructionOpcode.OR.bincode:
                alu_binop_instr_signals(ALUOperation.OR)

            case InstructionOpcode.XOR.bincode:
                alu_binop_instr_signals(ALUOperation.XOR)

            case InstructionOpcode.NOT.bincode:
                alu_unop_instr_signals(ALUOperation.NOT)

            case InstructionOpcode.SHL.bincode:
                alu_binop_instr_signals(ALUOperation.SHL)

            case InstructionOpcode.SHR.bincode:
                alu_binop_instr_signals(ALUOperation.SHR)

            case InstructionOpcode.CMP.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                self.tick()

                # EX
                mem_r1_to_alu_a_mem_r2_to_alu_b()
                self.tick()

                do_alu_op(ALUOperation.SUB)
                self.tick()

            case InstructionOpcode.SETEQ.bincode:
                set_instr_signals(6)

            case InstructionOpcode.SETNE.bincode:
                set_instr_signals(7)

            case InstructionOpcode.SETGE.bincode:
                set_instr_signals(8)

            case InstructionOpcode.SETLE.bincode:
                set_instr_signals(9)

            case InstructionOpcode.SETSG.bincode:
                set_instr_signals(10)

            case InstructionOpcode.SETSL.bincode:
                set_instr_signals(11)

            case InstructionOpcode.JAL.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                pc_plus_4_to_pc()
                self.tick()

                # ID
                decode_instruction()
                imm_to_ar()
                self.tick()

                # EX
                ar_to_jpc()
                mem_r1_to_alu_b()
                self.tick()

                do_alu_op_and_store_to_br(ALUOperation.FETCH_B)
                self.tick()

                # WB
                br_to_mem_r1()
                self.tick()

            case InstructionOpcode.JR.bincode:
                # IF
                pc_to_ipc_and_check_int()
                self.tick()

                if interrupted:
                    return

                # ID
                decode_instruction()
                self.tick()

                # EX
                mem_r1_to_ar()
                ar_to_jpc()
                jpc_to_pc()
                self.tick()

            case InstructionOpcode.JO.bincode:
                jump_flag_condition([0, 1])

            case InstructionOpcode.JZ.bincode:
                jump_flag_condition([1])

            case InstructionOpcode.JNZ.bincode:
                jump_flag_condition([0])

            case InstructionOpcode.RETI.bincode:
                self.tick()

                # ID
                ipc_to_pc()
                set_ie_1()
                self.tick()

            case InstructionOpcode.HALT.bincode:
                self.tick()
                raise MachineStop()

            case _:
                raise NotImplementedError(f"unexpected opcode {opcode}")

    def signal_read_instr(self) -> None:
        self.instruction_decoder.signal_latch_ir(self.datapath.memory.read(self.pc.get_value()))

    def signal_sel_dp(self, input_index: int) -> None:
        self.mux_dp.select_input(input_index)
        self.datapath.mux_alu_a.set_input_value(1, self.mux_dp.get_selected_value())
        self.datapath.mux_alu_b.set_input_value(1, self.mux_dp.get_selected_value())
        self.datapath.mux_ar.set_input_value(2, self.mux_dp.get_selected_value())

    def signal_sel_jpc(self, input_index: int) -> None:
        self.mux_jpc.select_input(input_index)

    def signal_latch_jpc(self) -> None:
        self.jpc.latch_value(value := self.mux_jpc.get_selected_value())
        self.mux_pc.set_input_value(0, value)

    def signal_sel_pc(self, input_index: int) -> None:
        self.mux_pc.select_input(input_index)

    def signal_latch_pc(self, init: bool = False) -> None:
        if init:
            value = self.pc.get_value()
        else:
            value = self.mux_pc.get_selected_value()

        self.pc.latch_value(value)
        self.mux_dp.set_input_value(0, value)
        self.mux_pc.set_input_value(2, value + 4)

    def tick(self) -> None:
        self._tick += 1

        if self._tick in self.input_tokens.keys():
            self.datapath.memory.write(INPUT_ADDR, ord(self.input_tokens[self._tick]))
            self.interrupt_handler.signal_add_irq(Interrupts.INPUT_DATA)

        tick_log = {
            "TICK": self._tick,

            "PC": self.pc.get_value(),
            "JPC": self.jpc.get_value(),

            "IR": self.instruction_decoder.ir.get_value(),
            "OPCODE": self.instruction_decoder.opcode.get_value(),
            "R1": self.instruction_decoder.r1.get_value(),
            "R2": self.instruction_decoder.r2.get_value(),
            "R3": self.instruction_decoder.r3.get_value(),
            "IMM": self.instruction_decoder.imm.get_value(),
            "ID_NZVC": int("".join(str(self.instruction_decoder.flags[flag].get_value()) for flag in "NZVC"), 2),

            "IPC": self.interrupt_handler.ipc.get_value(),
            "IRQ": self.interrupt_handler.irq.get_value(),
            "IE": self.interrupt_handler.ie.get_value(),

            "AR": self.datapath.ar.get_value(),
            "BR": self.datapath.br.get_value(),

            "ALU_A": self.datapath.alu.a.get_value(),
            "ALU_B": self.datapath.alu.b.get_value(),
            "ALU_NZVC": int("".join(str(self.datapath.alu.flags[flag].get_value()) for flag in "NZVC"), 2),
        }

        tick_log.update({
            register.name: self.datapath.register_file.registers[register.value].get_value()
            for register in [
                RegisterCode.SP, RegisterCode.RA, RegisterCode.S1, RegisterCode.S2, RegisterCode.S3,
                RegisterCode.S4, RegisterCode.S5, RegisterCode.S6, RegisterCode.S7, RegisterCode.S8,
                RegisterCode.S9, RegisterCode.S10, RegisterCode.S11, RegisterCode.S12, RegisterCode.I1,
                RegisterCode.I2, RegisterCode.T1, RegisterCode.T2, RegisterCode.T3, RegisterCode.T4,
                RegisterCode.T5, RegisterCode.T6, RegisterCode.T7, RegisterCode.T8, RegisterCode.A1,
                RegisterCode.A2, RegisterCode.A3, RegisterCode.A4, RegisterCode.A5, RegisterCode.A6,
                RegisterCode.A7, RegisterCode.A8,
            ]
        })

        self.simulation_log.append({"tick_state": tick_log})

        if self.ticks_limit is not None and self._tick >= self.ticks_limit:
            raise MachineLimitException("tick's limit reached")
