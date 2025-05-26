from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union, List


class ArithmeticOperator(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"


class LogicalOperator(Enum):
    AND = "and"
    OR = "or"
    NOT = "not"


class ComparisonOperator(Enum):
    EQ = "=="
    NEQ = "!="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="


class BitwiseOperator(Enum):
    SHL = "<<"
    SHR = ">>"


class DataTypes(Enum):
    STR = "str"
    INT = "int"
    VOID = "void"


class Term:
    pass


class ExpressionTerm(Term):
    pass


@dataclass
class InputTerm(Term):
    count: Optional[int] = None


@dataclass
class PrintTerm(Term):
    args: List[ExpressionTerm]


@dataclass
class FunctionCallTerm(ExpressionTerm):
    name: str
    args: List[ExpressionTerm]


@dataclass
class VariableDefinitionTerm(Term):
    name: str
    dtype: DataTypes
    value: Union[InputTerm, ExpressionTerm]


@dataclass
class VariableAssignmentTerm(Term):
    name: str
    value: Union[InputTerm, ExpressionTerm]


@dataclass
class VariableTerm(ExpressionTerm):
    name: str


@dataclass
class NumberLiteralTerm(ExpressionTerm):
    value: int


@dataclass
class StringLiteralTerm(ExpressionTerm):
    value: str


@dataclass
class BinOpTerm(ExpressionTerm):
    left: ExpressionTerm
    op: Union[ArithmeticOperator, LogicalOperator, ComparisonOperator, BitwiseOperator]
    right: ExpressionTerm


@dataclass
class UnaryOpTerm(ExpressionTerm):
    op: Union[ArithmeticOperator, LogicalOperator]
    expr: ExpressionTerm


@dataclass
class FunctionArgumentTerm(Term):
    name: str
    dtype: DataTypes


@dataclass
class ReturnTerm(Term):
    expr: Optional[ExpressionTerm]


@dataclass
class FunctionTerm(Term):
    return_dtype: DataTypes
    name: str
    args: List[FunctionArgumentTerm]
    body: List[Term]


@dataclass
class BranchTerm(Term):
    condition: Optional[ExpressionTerm]
    body: List[Term]
    next_branch: Optional[BranchTerm]


@dataclass
class ForTerm(Term):
    start: Union[VariableAssignmentTerm, VariableDefinitionTerm, None]
    condition: ExpressionTerm
    end: Union[VariableAssignmentTerm, None]
    body: List[Term]


@dataclass
class BreakTerm(Term):
    pass


@dataclass
class ContinueTerm(Term):
    pass
