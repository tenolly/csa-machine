from typing import List

import pytest

from src.compiler.parser import Parser
from src.compiler.parser.terms import (
    ArithmeticOperator,
    BinOpTerm,
    BitwiseOperator,
    BranchTerm,
    BreakTerm,
    ComparisonOperator,
    ContinueTerm,
    DataTypes,
    ForTerm,
    FunctionArgumentTerm,
    FunctionCallTerm,
    FunctionDefinitionTerm,
    InputTerm,
    LogicalOperator,
    NumberLiteralTerm,
    PrintTerm,
    ReturnTerm,
    StringLiteralTerm,
    Term,
    UnaryOpTerm,
    VariableAssignmentTerm,
    VariableDefinitionTerm,
    VariableTerm,
)
from src.compiler.tokenizer import Tokenizer
from src.compiler.tokenizer.tokens import Token


def get_tokens(program: str) -> List[Token]:
    return Tokenizer(program).tokenize()


def parse_first_term(program: str) -> Term:
    return Parser(get_tokens(program)).parse().terms[0]


test_cases = [
    # Print
    ("print()", PrintTerm(args=[])),
    (
        "print(a(), 3, 2 + 1, \"qqq\")",
        PrintTerm(
            args=[
                FunctionCallTerm(name="a", args=[]),
                NumberLiteralTerm(value=3),
                BinOpTerm(
                    left=NumberLiteralTerm(value=2),
                    op=ArithmeticOperator.ADD,
                    right=NumberLiteralTerm(value=1),
                ),
                StringLiteralTerm(value="qqq"),
            ],
        ),
    ),

    # Variable Definitions
    (
        "variable:int = input()",
        VariableDefinitionTerm(name="variable", dtype=DataTypes.INT, value=InputTerm(count=None)),
    ),
    (
        "variable:str = input(3)",
        VariableDefinitionTerm(name="variable", dtype=DataTypes.STR, value=InputTerm(count=3)),
    ),

    # Variable Assignments
    ("variable = input()", VariableAssignmentTerm(name="variable", value=InputTerm(count=None))),
    ("variable = input(10)", VariableAssignmentTerm(name="variable", value=InputTerm(count=10))),

    # Function Calls
    ("a()", FunctionCallTerm(name="a", args=[])),
    (
        "func(1, \"231\", re, q())",
        FunctionCallTerm(
            name="func", args=[
                NumberLiteralTerm(value=1),
                StringLiteralTerm(value="231"),
                VariableTerm(name="re"),
                FunctionCallTerm(name="q", args=[]),
            ],
        ),
    ),

    # Expressions
    (
        "v = 1 + 2 * 3",
        VariableAssignmentTerm(
            name="v",
            value=BinOpTerm(
                left=NumberLiteralTerm(value=1),
                op=ArithmeticOperator.ADD,
                right=BinOpTerm(
                    left=NumberLiteralTerm(value=2),
                    op=ArithmeticOperator.MUL,
                    right=NumberLiteralTerm(value=3),
                ),
            ),
        ),
    ),
    (
        "v = not not 3 - (1 + -2)",
        VariableAssignmentTerm(
            name="v",
            value=UnaryOpTerm(
                op=LogicalOperator.NOT,
                expr=UnaryOpTerm(
                    op=LogicalOperator.NOT,
                    expr=BinOpTerm(
                        left=NumberLiteralTerm(value=3),
                        op=ArithmeticOperator.SUB,
                        right=BinOpTerm(
                            left=NumberLiteralTerm(value=1),
                            op=ArithmeticOperator.ADD,
                            right=UnaryOpTerm(
                                op=ArithmeticOperator.SUB,
                                expr=NumberLiteralTerm(value=2),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
    (
        "v = not ((1 << 3) + (1 >> 3)) and 4",
        VariableAssignmentTerm(
            name="v",
            value=BinOpTerm(
                left=UnaryOpTerm(
                    op=LogicalOperator.NOT,
                    expr=BinOpTerm(
                        left=BinOpTerm(
                            left=NumberLiteralTerm(value=1),
                            op=BitwiseOperator.SHL,
                            right=NumberLiteralTerm(value=3),
                        ),
                        op=ArithmeticOperator.ADD,
                        right=BinOpTerm(
                            left=NumberLiteralTerm(value=1),
                            op=BitwiseOperator.SHR,
                            right=NumberLiteralTerm(value=3),
                        ),
                    ),
                ),
                op=LogicalOperator.AND,
                right=NumberLiteralTerm(value=4),
            ),
        ),
    ),
    (
        "v = -1 == 3 * 7 << 2",
        VariableAssignmentTerm(
            name="v",
            value=BinOpTerm(
                left=UnaryOpTerm(
                    op=ArithmeticOperator.SUB,
                    expr=NumberLiteralTerm(value=1),
                ),
                op=ComparisonOperator.EQ,
                right=BinOpTerm(
                    left=NumberLiteralTerm(value=3),
                    op=ArithmeticOperator.MUL,
                    right=BinOpTerm(
                        left=NumberLiteralTerm(value=7),
                        op=BitwiseOperator.SHL,
                        right=NumberLiteralTerm(value=2),
                    ),
                ),
            ),
        ),
    ),

    # Functions
    (
        "int sum[a:int, b:int] { return: a + b }",
        FunctionDefinitionTerm(
            return_dtype=DataTypes.INT,
            name="sum",
            args=[
                FunctionArgumentTerm(
                    name="a",
                    dtype=DataTypes.INT,
                ),
                FunctionArgumentTerm(
                    name="b",
                    dtype=DataTypes.INT,
                ),
            ],
            body=[
                ReturnTerm(
                    expr=BinOpTerm(
                        left=VariableTerm(name="a"),
                        op=ArithmeticOperator.ADD,
                        right=VariableTerm(name="b"),
                    ),
                ),
            ],
        ),
    ),
    (
        "void print10[] { print(10) }",
        FunctionDefinitionTerm(
            return_dtype=DataTypes.VOID,
            name="print10",
            args=[],
            body=[
                PrintTerm(
                    args=[
                        NumberLiteralTerm(value=10),
                    ],
                ),
            ],
        ),
    ),
    (
        "void do_nothing[string:str] { }",
        FunctionDefinitionTerm(
            return_dtype=DataTypes.VOID,
            name="do_nothing",
            args=[
                FunctionArgumentTerm(
                    name="string",
                    dtype=DataTypes.STR,
                ),
            ],
            body=[],
        ),
    ),

    # Branches
    (
        "if [v > 1] { print(\"v > 1\") }",
        BranchTerm(
            condition=BinOpTerm(
                left=VariableTerm(name="v"),
                op=ComparisonOperator.GT,
                right=NumberLiteralTerm(value=1),
            ),
            body=[
                PrintTerm(
                    args=[
                        StringLiteralTerm(value="v > 1"),
                    ],
                ),
            ],
            next_branch=None,
        ),
    ),
    (
        "if [n() << 1 == 2] { res = res + 2 } else { res = res + 1 }",
        BranchTerm(
            condition=BinOpTerm(
                left=BinOpTerm(
                    left=FunctionCallTerm(name="n", args=[]),
                    op=BitwiseOperator.SHL,
                    right=NumberLiteralTerm(value=1),
                ),
                op=ComparisonOperator.EQ,
                right=NumberLiteralTerm(value=2),
            ),
            body=[
                VariableAssignmentTerm(
                    name="res",
                    value=BinOpTerm(
                        left=VariableTerm(name="res"),
                        op=ArithmeticOperator.ADD,
                        right=NumberLiteralTerm(value=2),
                    ),
                ),
            ],
            next_branch=BranchTerm(
                condition=None,
                body=[
                    VariableAssignmentTerm(
                        name="res",
                        value=BinOpTerm(
                            left=VariableTerm(name="res"),
                            op=ArithmeticOperator.ADD,
                            right=NumberLiteralTerm(value=1),
                        ),
                    ),
                ],
                next_branch=None,
            ),
        ),
    ),
    (
        "if [a() + b()] { print(\"a\", \"b\") } elif [c() + d] { print(\"c\", d) }",
        BranchTerm(
            condition=BinOpTerm(
                left=FunctionCallTerm(name="a", args=[]),
                op=ArithmeticOperator.ADD,
                right=FunctionCallTerm(name="b", args=[]),
            ),
            body=[
                PrintTerm(
                    args=[
                        StringLiteralTerm(value="a"),
                        StringLiteralTerm(value="b"),
                    ],
                ),
            ],
            next_branch=BranchTerm(
                condition=BinOpTerm(
                    left=FunctionCallTerm(name="c", args=[]),
                    op=ArithmeticOperator.ADD,
                    right=VariableTerm(name="d"),
                ),
                body=[
                    PrintTerm(
                        args=[
                            StringLiteralTerm(value="c"),
                            VariableTerm(name="d"),
                        ],
                    ),
                ],
                next_branch=None,
            ),
        ),
    ),

    # For
    (
        "for [i: int = 1; i < 5; i = i + 1] { break }",
        ForTerm(
            start=VariableDefinitionTerm(
                name="i",
                dtype=DataTypes.INT,
                value=NumberLiteralTerm(value=1),
            ),
            condition=BinOpTerm(
                left=VariableTerm(name="i"),
                op=ComparisonOperator.LT,
                right=NumberLiteralTerm(value=5),
            ),
            end=VariableAssignmentTerm(
                name="i",
                value=BinOpTerm(
                    left=VariableTerm(name="i"),
                    op=ArithmeticOperator.ADD,
                    right=NumberLiteralTerm(value=1),
                ),
            ),
            body=[BreakTerm()],
        ),
    ),
    (
        "for [; v != 5 ;] { v = input() print(v + 1) }",
        ForTerm(
            start=None,
            condition=BinOpTerm(
                left=VariableTerm(name="v"),
                op=ComparisonOperator.NEQ,
                right=NumberLiteralTerm(value=5),
            ),
            end=None,
            body=[
                VariableAssignmentTerm(name="v", value=InputTerm(count=None)),
                PrintTerm(
                    args=[
                        BinOpTerm(
                            left=VariableTerm(name="v"),
                            op=ArithmeticOperator.ADD,
                            right=NumberLiteralTerm(value=1),
                        ),
                    ],
                ),
            ],
        ),
    ),
    (
        "for [; a + b < 100 ; a = a + b + 1] { if [(a + b) % 2 == 0] { continue } print(a + b) }",
        ForTerm(
            start=None,
            condition=BinOpTerm(
                left=BinOpTerm(
                    left=VariableTerm(name="a"),
                    op=ArithmeticOperator.ADD,
                    right=VariableTerm(name="b"),
                ),
                op=ComparisonOperator.LT,
                right=NumberLiteralTerm(value=100),
            ),
            end=VariableAssignmentTerm(
                name="a",
                value=BinOpTerm(
                    left=BinOpTerm(
                        left=VariableTerm(name="a"),
                        op=ArithmeticOperator.ADD,
                        right=VariableTerm(name="b"),
                    ),
                    op=ArithmeticOperator.ADD,
                    right=NumberLiteralTerm(value=1),
                ),
            ),
            body=[
                BranchTerm(
                    condition=BinOpTerm(
                        left=BinOpTerm(
                            left=BinOpTerm(
                                left=VariableTerm(name="a"),
                                op=ArithmeticOperator.ADD,
                                right=VariableTerm(name="b"),
                            ),
                            op=ArithmeticOperator.MOD,
                            right=NumberLiteralTerm(value=2),
                        ),
                        op=ComparisonOperator.EQ,
                        right=NumberLiteralTerm(value=0),
                    ),
                    body=[
                        ContinueTerm(),
                    ],
                    next_branch=None,
                ),
                PrintTerm(
                    args=[
                        BinOpTerm(
                            left=VariableTerm(name="a"),
                            op=ArithmeticOperator.ADD,
                            right=VariableTerm(name="b"),
                        ),
                    ],
                ),
            ],
        ),
    ),
]


class TestParser:
    @pytest.mark.parametrize("program,expected_term", test_cases)
    def test_correct_parse_terms(self, program: str, expected_term: Term) -> None:
        assert parse_first_term(program) == expected_term
