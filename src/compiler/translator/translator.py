from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Type, Union

from ..parser.terms import (
    ArithmeticOperator,
    BinOpTerm,
    BitwiseOperator,
    BranchTerm,
    BreakTerm,
    ComparisonOperator,
    ContinueTerm,
    ExpressionTerm,
    ForTerm,
    FunctionCallTerm,
    FunctionDefinitionTerm,
    InputTerm,
    LogicalOperator,
    NumberLiteralTerm,
    PrintTerm,
    ProgramTerm,
    StringLiteralTerm,
    Term,
    UnaryOpTerm,
    VariableAssignmentTerm,
    VariableDefinitionTerm,
    VariableTerm,
)
from .binary.instructions.core import Register, Value
from .binary.instructions.instruction_set import (
    ArithmeticShiftLeft,
    ArithmeticShiftRight,
    Compare,
    Halt,
    JumpIfZero,
    JumpOffset,
    LoadLowerImmediate,
    LoadUpperImmediate,
    LoadWord,
    LoadWordFromRegister,
    LogicalAnd,
    LogicalNot,
    LogicalOr,
    Move,
    Negative,
    ReturnFromInterruption,
    SaveWord,
    SaveWordToRegister,
    SetIfEqual,
    SetIfGreaterOrEqual,
    SetIfLessOrEqual,
    SetIfNotEqual,
    SetIfStrictlyGreater,
    SetIfStrictlyLess,
    SignedAddition,
    SignedAdditionImmediate,
    SignedDivision,
    SignedMultiply,
    SignedRemainder,
    SignedSubtraction,
)
from .binary.instructions.instruction_types import BaseInstruction
from .binary.instructions.register_set import (
    I1,
    I2,
    S1,
    S2,
    S3,
    S4,
    S5,
    S6,
    S7,
    S8,
    S9,
    S10,
    S11,
    S12,
    T1,
    T2,
    T3,
    T4,
    T5,
    T6,
    T7,
    T8,
)
from .binary.transform import to_bytes
from .binary.word import Word
from .exceptions import RegisterManagementException, TranslateException

################################
#         ! ATTENTION !        #
################################
# The code below is disgusting #
# TODO: do a total refactoring #
################################


@dataclass
class Section:
    prefix: str
    start_addr: Addr
    instructions: List[LazyInstruction]


@dataclass
class Variable:
    addr: int
    value: Union[str, int]


@dataclass
class VariableRelativeAddr:
    variable: Variable
    offset: int


@dataclass
class Offset:
    value: int


@dataclass
class Addr:
    value: int


class LazyInstruction:
    def __init__(self, instr_class: Type[BaseInstruction], *args):
        self.instr_class = instr_class
        self.args = args
        self.metainfo = {}

    def produce(self) -> BaseInstruction:
        args = []

        for arg in self.args:
            if isinstance(arg, Variable):
                args.append(Value(arg.addr))
            elif isinstance(arg, Offset) or isinstance(arg, Addr):
                args.append(Value(arg.value))
            elif isinstance(arg, VariableRelativeAddr):
                args.append(Value(arg.variable.addr + arg.offset))
            else:
                args.append(arg)

        return self.instr_class(*args)


class MemoryManager:
    def __init__(self):
        self.constants: Dict[str, Variable] = {}
        self.variables: Dict[str, Variable] = {}
        self.io_data_read_addr: Addr = Addr(-1)
        self.io_data_addr: Addr = Addr(-1)
        self.io_data: Variable = Variable(-1, "0" * 1024)

    def get_variable(self, variable_label: str) -> Optional[Variable]:
        if variable_label in self.constants:
            return self.constants[variable_label]

        if variable_label in self.variables:
            return self.variables[variable_label]

    def create_constant(self, variable_label: Optional[str], variable_value: Union[int, str]) -> Variable:
        if variable_label is None:
            variable_label = f"literal_{len(self.constants)}"

        self.constants[variable_label] = Variable(-1, variable_value)
        return self.constants[variable_label]

    def create_variable(self, variable_label: Optional[str], variable_value: Union[int, str]) -> Variable:
        if variable_label is None:
            variable_label = f"literal_{len(self.variables)}"

        self.variables[variable_label] = Variable(-1, variable_value)
        return self.variables[variable_label]


class RegistersManager:
    def __init__(self):
        self.first_interrupt_register: Register = I1
        self.second_interrupt_register: Register = I2
        self.first_load_temp_register: Register = T7
        self.second_load_temp_register: Register = T8
        self.temp_registers: List[Register] = [T1, T2, T3, T4, T5, T6]
        self.saved_registers: List[Register] = [S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12]

        self.occupied_registers: Dict[Register, str] = {}

    def get_register_by_variable_label(self, variable_label: str) -> Optional[Register]:
        for reg, label in self.occupied_registers.items():
            if label == variable_label:
                return reg

    def find_free_temp_register(self) -> Optional[Register]:
        used_registers = set(self.occupied_registers.keys())
        for register in self.temp_registers:
            if register not in used_registers:
                return register

    def find_free_saved_register(self) -> Optional[Register]:
        used_registers = set(self.occupied_registers.keys())
        for register in self.saved_registers:
            if register not in used_registers:
                return register

    def take_register(self, target_register: Register, variable_label: Optional[str] = None) -> None:
        if target_register in self.occupied_registers:
            raise RegisterManagementException(f"{target_register!r} is not free")

        if variable_label is None:
            variable_label = f"literal_{len(self.occupied_registers)}"

        self.occupied_registers[target_register] = variable_label

    def free_register(self, target_register: Register) -> None:
        if target_register not in self.occupied_registers:
            raise RegisterManagementException(f"{target_register!r} is not in use")

        del self.occupied_registers[target_register]

    def free_temp_register(self, target_register: Register, strict: bool = False) -> None:
        if target_register not in self.temp_registers:
            if not strict:
                return

            raise RegisterManagementException(f"{target_register!r} is not temporary register")

        self.free_register(target_register)


class Translator:
    def __init__(self, program_ast: ProgramTerm):
        self.program_ast: ProgramTerm = program_ast

        self.memory_manager: MemoryManager = MemoryManager()
        self.register_manager: RegistersManager = RegistersManager()

        self.input_port_addr: int = 0x10
        self.output_port_addr: int = 0x11
        self.program_start_addr: int = 0x1000

        self.interrupt_vectors: List[Addr] = []
        self.functions: Dict[str, Section] = {}
        self._init_default_interrupt_vectors()

        self.program: Section = Section("_start", Addr(-1), [])
        self.sections_stack: List[Section] = [self.program]

    def _init_default_interrupt_vectors(self) -> None:
        default_interrupt_handler_addr = Addr(-1)
        default_interrupt_handler = Section("d_int", default_interrupt_handler_addr, [])
        default_interrupt_handler.instructions.append(LazyInstruction(ReturnFromInterruption))
        self.functions[default_interrupt_handler.prefix] = default_interrupt_handler

        char_reg = self.register_manager.first_interrupt_register
        input_addr_reg = self.register_manager.second_interrupt_register

        input_interrupt_handler_addr = Addr(-1)
        input_interrupt_handler = Section("input_int", input_interrupt_handler_addr, [])
        input_interrupt_handler.instructions.extend([
            LazyInstruction(LoadLowerImmediate, input_addr_reg, self.memory_manager.io_data_addr),
            LazyInstruction(LoadUpperImmediate, input_addr_reg, self.memory_manager.io_data_addr),
            LazyInstruction(LoadWord, char_reg, Addr(self.input_port_addr)),
            LazyInstruction(SaveWordToRegister, char_reg, input_addr_reg),
            LazyInstruction(SignedAdditionImmediate, input_addr_reg, Value(1)),
            LazyInstruction(SaveWord, input_addr_reg, self.memory_manager.io_data_addr),
            LazyInstruction(ReturnFromInterruption),
        ])
        self.functions[input_interrupt_handler.prefix] = input_interrupt_handler

        for _ in range(15):
            self.interrupt_vectors.append(default_interrupt_handler_addr)

        self.interrupt_vectors.append(input_interrupt_handler_addr)

    def translate(self) -> bytes:
        for ast_node in self.program_ast.terms:
            self.program.instructions.extend(self._translate_root_ast_node(ast_node))
        self.program.instructions.append(LazyInstruction(Halt))

        self._process_addresses()

        program_instructions = [instr.produce() for instr in self.program.instructions]
        functions = [
            [instr.produce() for instr in func_section.instructions]
            for func_section in self.functions.values()
        ]

        bits = []
        for interrupt_vector in self.interrupt_vectors:
            bits.append(Word.from_integer(interrupt_vector.value))

        bits.append(Word.from_integer(self.input_port_addr))
        bits.append(Word.from_integer(self.output_port_addr))

        for instruction in program_instructions:
            bits.append(Word.from_instruction(instruction.bits()))

        for func_instructions in functions:
            for instruction in func_instructions:
                bits.append(Word.from_instruction(instruction.bits()))

        bytes_gen = map(to_bytes, bits)
        bytes_representation = next(bytes_gen)
        for b_part in bytes_gen:
            bytes_representation += b_part

        return bytes_representation

    def _process_addresses(self) -> None:
        data_addr = self.output_port_addr + 1
        for variables_dict in (self.memory_manager.constants, self.memory_manager.variables):
            for variable in variables_dict.values():
                variable.addr = data_addr
                if isinstance(variable.value, int):
                    data_addr += 1
                elif isinstance(variable.value, str):
                    data_addr += len(variable.value)
                else:
                    raise TranslateException(f"unexpected variable value {variable.value} (variable: {variable!r})")

        data_addr += 2

        self.memory_manager.io_data_addr.value = data_addr
        self.memory_manager.io_data_read_addr.value = data_addr
        self.memory_manager.io_data.addr = data_addr

        memory_end_addr = data_addr + len(self.memory_manager.io_data.value) + 1
        if memory_end_addr > self.program_start_addr:
            raise TranslateException(f"memory out (max {self.program_start_addr}, got {memory_end_addr})")

        program_addr = self.program_start_addr
        self.program.start_addr.value = program_addr

        program_addr += len(self.program.instructions) + 1
        for function in self.functions.values():
            function.start_addr.value = program_addr
            program_addr += len(function.instructions) + 1

    def _translate_root_ast_node(self, ast_node: Term) -> List[LazyInstruction]:
        transitions = {
            FunctionCallTerm: self._translate_function_call,
            FunctionDefinitionTerm: self._translate_function_definition,
            VariableAssignmentTerm: self._translate_variable_assigment,
            VariableDefinitionTerm: self._translate_variable_definition,
            BranchTerm: self._translate_branch,
            ForTerm: self._translate_for,
            PrintTerm: self._translate_print,
            ContinueTerm: self._translate_continue,
            BreakTerm: self._translate_break,
        }

        for target_ast_node, translate_ast_node_function in transitions.items():
            if isinstance(ast_node, target_ast_node):
                return translate_ast_node_function(ast_node)

        self._throw_semantic_exception(ast_node)

    def _translate_function_definition(self, ast_node: FunctionDefinitionTerm) -> List[LazyInstruction]:
        # TODO: add feature
        raise TranslateException("functions are not supported in this language version")

    def _translate_variable_assigment(self, ast_node: VariableAssignmentTerm) -> List[LazyInstruction]:
        variable_name = self._get_ident_name(ast_node.name)
        variable_loc = self._get_variable_location_by_name(variable_name)
        register_or_variable, variable_instructions = self._translate_variable_value(ast_node.value)

        if isinstance(variable_loc, Register):
            if isinstance(register_or_variable, Register):
                if variable_loc != register_or_variable:
                    variable_instructions.append(LazyInstruction(Move, variable_loc, register_or_variable))
                    self.register_manager.free_temp_register(register_or_variable)
            elif isinstance(register_or_variable, Variable):
                variable_instructions.append(LazyInstruction(LoadWord, variable_loc, register_or_variable))
            else:
                self._throw_semantic_exception(register_or_variable)
        elif isinstance(variable_loc, Variable):
            if isinstance(register_or_variable, Register):
                variable_instructions.append(LazyInstruction(SaveWord, register_or_variable, variable_loc))
                self.register_manager.free_temp_register(register_or_variable)
            elif isinstance(register_or_variable, Variable):
                variable_instructions.append(
                    LazyInstruction(LoadWord, self.register_manager.first_load_temp_register, register_or_variable),
                )
                variable_instructions.append(
                    LazyInstruction(SaveWord, self.register_manager.first_load_temp_register, variable_loc),
                )
            else:
                self._throw_semantic_exception(register_or_variable)
        else:
            self._throw_semantic_exception(register_or_variable)

        return variable_instructions

    def _translate_variable_definition(self, ast_node: VariableDefinitionTerm) -> List[LazyInstruction]:
        variable_name = self._get_ident_name(ast_node.name)
        register_or_variable, variable_instructions = self._translate_variable_value(ast_node.value)

        if isinstance(register_or_variable, Register):
            register_to_save = self.register_manager.find_free_saved_register()
            if register_to_save is not None:
                variable_instructions.append(LazyInstruction(Move, register_to_save, register_or_variable))
                self.register_manager.take_register(register_to_save, variable_name)
                self.register_manager.free_temp_register(register_or_variable)
            else:
                variable = self.memory_manager.create_variable(variable_name, 0)
                variable_instructions.append(LazyInstruction(SaveWord, register_or_variable, variable))
                self.register_manager.free_temp_register(register_or_variable)
        elif isinstance(register_or_variable, Variable):
            self.memory_manager.create_variable(variable_name, register_or_variable.value)
        else:
            self._throw_semantic_exception(register_or_variable)

        return variable_instructions

    def _translate_branch(self, ast_node: BranchTerm) -> List[LazyInstruction]:
        instructions = []
        self._translate_branch_node(ast_node, instructions)

        for i, lazy_instruction in enumerate(instructions):
            if lazy_instruction.metainfo.get("calc_jump_to_end"):
                lazy_instruction.metainfo["calc_jump_to_end"] = False
                lazy_instruction.args[0].value = len(instructions) - i

        return instructions

    def _translate_branch_node(self, ast_node: BranchTerm, instructions: List[LazyInstruction]) -> List[LazyInstruction]:
        jump_to_end_offset = Offset(0)

        body_instructions = []
        for term in ast_node.body:
            body_instructions.extend(self._translate_root_ast_node(term))

        instruction = LazyInstruction(JumpOffset, jump_to_end_offset)
        instruction.metainfo["calc_jump_to_end"] = True
        body_instructions.append(instruction)

        condition_instructions = []
        if ast_node.condition is not None:
            offset_to_end = Offset(len(body_instructions))

            register_or_variable = self._translate_expression(ast_node.condition, condition_instructions)
            if isinstance(register_or_variable, Register):
                condition_instructions.append(LazyInstruction(JumpIfZero, offset_to_end))
            elif isinstance(register_or_variable, Variable):
                condition_instructions.append(
                    LazyInstruction(LoadWord, self.register_manager.first_load_temp_register, register_or_variable),
                )
                condition_instructions.append(LazyInstruction(JumpIfZero, offset_to_end))
            else:
                self._throw_semantic_exception(register_or_variable)

            self.register_manager.free_temp_register(register_or_variable)

        instructions.extend(condition_instructions + body_instructions)
        jump_to_end_offset.value -= len(instructions)

        if ast_node.next_branch is not None:
            return self._translate_branch_node(ast_node.next_branch, instructions)
        else:
            del instructions[-1]

        return instructions

    def _translate_for(self, ast_node: ForTerm) -> List[LazyInstruction]:
        instructions = []

        if isinstance(ast_node.start, VariableAssignmentTerm):
            instructions.extend(self._translate_variable_assigment(ast_node.start))
        elif isinstance(ast_node.start, VariableDefinitionTerm):
            instructions.extend(self._translate_variable_definition(ast_node.start))
        elif ast_node.start is not None:
            self._throw_semantic_exception(ast_node.start)

        offset_to_end = Offset(0)

        body_instructions = []

        register_or_variable = self._translate_expression(ast_node.condition, body_instructions)
        body_instructions.append(LazyInstruction(JumpIfZero, offset_to_end))
        offset_to_end.value -= len(body_instructions)

        if isinstance(register_or_variable, Register):
            self.register_manager.free_temp_register(register_or_variable)

        for term in ast_node.body:
            body_instructions.extend(self._translate_root_ast_node(term))

        end_instructions_len = 0
        if isinstance(ast_node.end, VariableAssignmentTerm):
            end_instructions = self._translate_variable_assigment(ast_node.end)
            end_instructions_len = len(end_instructions)
            body_instructions.extend(end_instructions)
        elif ast_node.start is not None:
            self._throw_semantic_exception(ast_node.start)

        body_instructions.append(LazyInstruction(JumpOffset, Offset(-1 * len(body_instructions))))

        offset_to_end.value += len(body_instructions) + 1

        for i, lazy_instruction in enumerate(body_instructions):
            if isinstance(lazy_instruction.metainfo.get("term"), ContinueTerm):
                lazy_instruction.args[0].value = len(body_instructions) - end_instructions_len - i - 1
            elif isinstance(lazy_instruction.metainfo.get("term"), BreakTerm):
                lazy_instruction.args[0].value = len(body_instructions) - i

        return instructions + body_instructions

    def _translate_continue(self, term: ContinueTerm) -> List[LazyInstruction]:
        if not isinstance(term, ContinueTerm):
            self._throw_semantic_exception(term)

        instruction = LazyInstruction(JumpOffset, Offset(0))
        instruction.metainfo["term"] = term
        instructions = [instruction]

        return instructions

    def _translate_break(self, term: BreakTerm) -> List[LazyInstruction]:
        if not isinstance(term, BreakTerm):
            self._throw_semantic_exception(term)

        instruction = LazyInstruction(JumpOffset, Offset(0))
        instruction.metainfo["term"] = term
        instructions = [instruction]

        return instructions

    def _translate_print(self, ast_node: PrintTerm) -> List[LazyInstruction]:
        instructions = []
        for expr in ast_node.args:
            register_or_variable = self._translate_expression(expr, instructions)
            if isinstance(register_or_variable, Register):
                instructions.append(LazyInstruction(SaveWord, register_or_variable, Addr(self.output_port_addr)))
            elif isinstance(register_or_variable, Variable):
                if isinstance(register_or_variable.value, int):
                    instructions.extend([
                        LazyInstruction(LoadWord, self.register_manager.first_load_temp_register, register_or_variable),
                        LazyInstruction(
                            SaveWord,
                            self.register_manager.first_load_temp_register,
                            Addr(self.output_port_addr),
                        ),
                    ])
                elif isinstance(register_or_variable.value, str):
                    string_addr_reg = self.register_manager.first_load_temp_register
                    chars_reg = self.register_manager.second_load_temp_register
                    instructions.extend([
                        LazyInstruction(LoadLowerImmediate, string_addr_reg, register_or_variable),
                        LazyInstruction(LoadUpperImmediate, string_addr_reg, register_or_variable),
                        LazyInstruction(LoadWordFromRegister, chars_reg, string_addr_reg),
                        LazyInstruction(SignedAdditionImmediate, chars_reg, Value(0)),
                        LazyInstruction(JumpIfZero, Offset(4)),
                        LazyInstruction(SaveWord, chars_reg, Addr(self.output_port_addr)),
                        LazyInstruction(SignedAdditionImmediate, string_addr_reg, Value(4)),
                        LazyInstruction(JumpOffset, Offset(-5)),
                    ])
                else:
                    self._throw_semantic_exception(register_or_variable.value)
            else:
                self._throw_semantic_exception(register_or_variable)

        return instructions

    def _translate_variable_value(
        self,
        ast_node: Union[ExpressionTerm, InputTerm],
    ) -> Tuple[Union[Register, Variable], List[LazyInstruction]]:
        instructions = []

        if isinstance(ast_node, InputTerm):
            register_or_variable = self._translate_input(ast_node, instructions)
        elif isinstance(ast_node, ExpressionTerm):
            register_or_variable = self._translate_expression(ast_node, instructions)
        else:
            self._throw_semantic_exception(ast_node)

        return register_or_variable, instructions

    def _translate_input(
        self,
        ast_node: InputTerm,
        instructions: List[LazyInstruction],
    ) -> Union[Register, Variable]:
        def read_word(instructions: List[LazyInstruction]) -> Register:
            enabled_words_register = self.register_manager.first_load_temp_register
            already_read_words_register = self.register_manager.second_load_temp_register
            instructions.extend([
                LazyInstruction(LoadLowerImmediate, enabled_words_register, self.memory_manager.io_data_addr),
                LazyInstruction(LoadLowerImmediate, enabled_words_register, self.memory_manager.io_data_addr),
                LazyInstruction(LoadLowerImmediate, already_read_words_register, self.memory_manager.io_data_read_addr),
                LazyInstruction(LoadLowerImmediate, already_read_words_register, self.memory_manager.io_data_read_addr),
                LazyInstruction(Compare, enabled_words_register, already_read_words_register),
                LazyInstruction(JumpIfZero, Offset(-5)),
                LazyInstruction(
                    LoadWordFromRegister,
                    inputed_word_register := enabled_words_register,
                    already_read_words_register,
                ),
                LazyInstruction(SignedAdditionImmediate, already_read_words_register, Value(1)),
                LazyInstruction(SaveWord, already_read_words_register, self.memory_manager.io_data_read_addr),
            ])
            return inputed_word_register

        if ast_node.count is None:
            inputed_word_register = read_word(instructions)
            register = self.register_manager.find_free_temp_register()
            if register is not None:
                instructions.append(Move, register, inputed_word_register)
                self.register_manager.take_register(register)
                return register
            else:
                variable = self.memory_manager.create_variable(None, 0)
                instructions.append(SaveWord, inputed_word_register, variable)
                return variable
        else:
            string_variable = self.memory_manager.create_constant(None, "0" * ast_node.count)
            for i in range(ast_node.count):
                inputed_word_register = read_word(instructions)
                instructions.append(
                    LazyInstruction(SaveWord, inputed_word_register, VariableRelativeAddr(string_variable, i)),
                )

    def _translate_expression(
        self,
        ast_node: ExpressionTerm,
        instructions: List[LazyInstruction],
    ) -> Union[Register, Variable]:
        if isinstance(ast_node, NumberLiteralTerm):
            return self._translate_number_literal(ast_node, instructions)

        if isinstance(ast_node, StringLiteralTerm):
            return self._translate_string_literal(ast_node)

        if isinstance(ast_node, VariableTerm):
            return self._translate_variable(ast_node)

        if isinstance(ast_node, FunctionCallTerm):
            return self._translate_function_call(ast_node, instructions)

        if isinstance(ast_node, BinOpTerm):
            return self._translate_bin_op(ast_node, instructions)

        if isinstance(ast_node, UnaryOpTerm):
            return self._translate_unary_op(ast_node, instructions)

        self._throw_semantic_exception(ast_node)

    def _translate_number_literal(
        self,
        ast_node: NumberLiteralTerm,
        instructions: List[LazyInstruction],
    ) -> Union[Register, Variable]:
        register = self.register_manager.find_free_temp_register()

        if register is not None:
            instructions.append(LazyInstruction(LoadLowerImmediate, register, Value(ast_node.value)))
            instructions.append(LazyInstruction(LoadUpperImmediate, register, Value(ast_node.value)))
            self.register_manager.take_register(register)
            return register
        else:
            return self.memory_manager.create_constant(None, ast_node.value)

    def _translate_string_literal(self, ast_node: StringLiteralTerm) -> Variable:
        return self.memory_manager.create_constant(None, ast_node.value)

    def _translate_variable(self, ast_node: VariableTerm) -> Union[Register, Variable]:
        return self._get_variable_location_by_name(self._get_ident_name(ast_node.name))

    def _translate_bin_op(self, ast_node: BinOpTerm, instructions: List[LazyInstruction]) -> Union[Register, Variable]:
        left = self._translate_expression(ast_node.left, instructions)
        right = self._translate_expression(ast_node.right, instructions)

        if left in self.register_manager.temp_registers:
            left_register = left
            result_register = left_register
        elif isinstance(left, Register):
            left_register = left
            result_register = self.register_manager.find_free_temp_register()
            if result_register is None:
                result_register = self.register_manager.first_load_temp_register
            else:
                self.register_manager.take_register(result_register)
        else:
            left_register = self.register_manager.first_load_temp_register
            instructions.append(LazyInstruction(LoadWord, left_register, left))
            result_register = left_register

        if right in self.register_manager.temp_registers:
            self.register_manager.free_temp_register(right)
            right_register = right
        elif isinstance(right, Register):
            right_register = self.register_manager.second_load_temp_register
            instructions.append(LazyInstruction(Move, right_register, right))
        else:
            instructions.append(LazyInstruction(LoadWord, self.register_manager.second_load_temp_register, right))
            right_register = self.register_manager.second_load_temp_register

        arithmetic_and_logical_operations_to_instr = {
            ArithmeticOperator.ADD: SignedAddition,
            ArithmeticOperator.SUB: SignedSubtraction,
            ArithmeticOperator.MUL: SignedMultiply,
            ArithmeticOperator.DIV: SignedDivision,
            ArithmeticOperator.MOD: SignedRemainder,
            LogicalOperator.AND: LogicalAnd,
            LogicalOperator.OR: LogicalOr,
            BitwiseOperator.SHL: ArithmeticShiftLeft,
            BitwiseOperator.SHR: ArithmeticShiftRight,
        }

        comparsion_operations_to_instr = {
            ComparisonOperator.EQ: SetIfEqual,
            ComparisonOperator.NEQ: SetIfNotEqual,
            ComparisonOperator.GT: SetIfStrictlyGreater,
            ComparisonOperator.GTE: SetIfGreaterOrEqual,
            ComparisonOperator.LT: SetIfStrictlyLess,
            ComparisonOperator.LTE: SetIfLessOrEqual,
        }

        if ast_node.op in arithmetic_and_logical_operations_to_instr:
            instr_class = arithmetic_and_logical_operations_to_instr[ast_node.op]
            instructions.append(LazyInstruction(instr_class, result_register, left_register, right_register))
        elif ast_node.op in comparsion_operations_to_instr:
            instr_class = comparsion_operations_to_instr[ast_node.op]
            instructions.append(LazyInstruction(Compare, left_register, right_register))
            instructions.append(LazyInstruction(instr_class, result_register))

        if result_register == self.register_manager.first_load_temp_register:
            variable = self.memory_manager.create_variable(None, 0)
            instructions.append(LazyInstruction(SaveWord, self.register_manager.first_load_temp_register, variable))
            return variable

        return result_register

    def _translate_unary_op(
        self,
        ast_node: UnaryOpTerm,
        instructions: List[LazyInstruction],
    ) -> Union[Register, Variable]:
        register_or_variable = self._translate_value_node(ast_node.expr, instructions)

        if isinstance(register_or_variable, Register):
            register = register_or_variable
        else:
            instructions.append(
                LazyInstruction(LoadWord, self.register_manager.first_load_temp_register, register_or_variable),
            )
            register = self.register_manager.first_load_temp_register

        if ast_node.op == ArithmeticOperator.SUB:
            instructions.append(LazyInstruction(Negative, register, register))
        elif ast_node.op == LogicalOperator.NOT:
            instructions.append(LazyInstruction(LogicalNot, register, register))
        else:
            self._throw_semantic_exception(ast_node.op)

        if isinstance(register_or_variable, Variable):
            instructions.append(LazyInstruction(SaveWord, register, register_or_variable))

        return register_or_variable

    def _translate_function_call(
        self,
        ast_node: FunctionCallTerm,
        instructions: List[LazyInstruction],
    ) -> List[LazyInstruction]:
        # TODO: add feature
        raise TranslateException("functions are not supported in this language version")

    def _get_ident_name(self, name: str) -> str:
        prefix = ""
        for section in self.sections_stack:
            prefix += section.prefix + "_"

        return prefix + name

    def _get_variable_location_by_name(self, variable_name: str) -> Union[Register, Variable]:
        register = self.register_manager.get_register_by_variable_label(variable_name)
        if register is not None:
            return register

        variable = self.memory_manager.get_variable(variable_name)
        if variable is not None:
            return variable

        raise TranslateException(f"variable {variable_name} is undefined")

    def _throw_semantic_exception(self, obj: object):
        raise TranslateException(
            f"unexpected object {obj}, perhaps the validator have missed that check or the translator is incorrect",
        )
