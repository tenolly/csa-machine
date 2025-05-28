from enum import Enum
from typing import Dict, List, Optional, Type, Union

from ..tokenizer.tokens import (
    AndToken,
    AssignToken,
    AsteriskToken,
    BreakToken,
    ColonToken,
    CommaToken,
    ContinueToken,
    CurlyLparenToken,
    CurlyRparenToken,
    DataTypeToken,
    ElifToken,
    ElseToken,
    EqualToken,
    ForToken,
    GreaterOrEqualToken,
    GreaterToken,
    IdentifierToken,
    IfToken,
    InputToken,
    IntegerDataTypeToken,
    LessOrEqualToken,
    LessToken,
    LparenToken,
    MinusToken,
    NotEqualToken,
    NotToken,
    NumberToken,
    OrToken,
    PercentToken,
    PlusToken,
    PrintToken,
    ReturnToken,
    RparenToken,
    SemicolonToken,
    ShiftLeftToken,
    ShiftRightToken,
    SlashToken,
    SquareLparenToken,
    SquareRparenToken,
    StringDataTypeToken,
    StringToken,
    Token,
    VoidDataTypeToken,
)
from .exceptions import ParserException
from .terms import (
    ArithmeticOperator,
    BinOpTerm,
    BitwiseOperator,
    BranchTerm,
    BreakTerm,
    ComparisonOperator,
    ContinueTerm,
    DataTypes,
    ExpressionTerm,
    ForTerm,
    FunctionArgumentTerm,
    FunctionCallTerm,
    FunctionTerm,
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


class ParserContext(Enum):
    IN_FUNCTION = 0
    IN_CYCLE = 1


class Parser:
    def __init__(self, tokens: List[Token]):
        self._tokens: List[Token] = tokens

        self._current_index: int = -1
        self._current_token: Optional[Token] = None

        self._context: Dict[ParserContext, int] = {
            ParserContext.IN_FUNCTION: 0,
            ParserContext.IN_CYCLE: 0,
        }
        self._context_stack: List[ParserContext] = []

        self.terms: List[Term] = []

    def _enter_context(self, context: ParserContext) -> None:
        self._context[context] += 1
        self._context_stack.append(context)

    def _exit_context(self) -> None:
        self._context[self._context_stack.pop()] -= 1

    def _is_in_context(self, context: ParserContext) -> bool:
        return self._context[context] != 0

    def _is_in_direct_context(self, context: ParserContext) -> bool:
        return len(self._context_stack) != 0 and self._context_stack[-1] == context

    def _advance(self, n: int = 1) -> Optional[Token]:
        self._current_index += n

        if 0 <= self._current_index < len(self._tokens):
            self._current_token = self._tokens[self._current_index]
        else:
            self._current_token = None

        return self._current_token

    def _peek(self, n: int = 1) -> Optional[Token]:
        next_index = self._current_index + n

        if 0 <= next_index < len(self._tokens):
            return self._tokens[next_index]

    def _expect(self, token_type: Type[Token]) -> Token:
        token = self._current_token
        if not isinstance(token, token_type):
            self._throw_incorrect_term_error()

        self._advance()
        return token

    def parse(self) -> List[Term]:
        self._advance()
        while self._current_token is not None:
            self.terms.append(self._parse_term_node())

        return self.terms

    def _parse_term_node(self) -> Term:
        transitions = {
            DataTypeToken: self._parse_func_def,
            ForToken: self._parse_for,
            IfToken: self._parse_if,
            IdentifierToken: self._parse_identifier_node,
            PrintToken: self._parse_print,
        }

        if self._is_in_context(ParserContext.IN_FUNCTION):
            transitions.update({ReturnToken: self._parse_return})

        if self._is_in_direct_context(ParserContext.IN_CYCLE):
            transitions.update({ContinueToken: self._parse_continue, BreakToken: self._parse_break})

        for start_token_cls, parse_term_function in transitions.items():
            if isinstance(self._current_token, start_token_cls):
                return parse_term_function()

        self._throw_unexpected_token_error()

    def _parse_func_def(self) -> FunctionTerm:
        self._enter_context(ParserContext.IN_FUNCTION)

        data_type_token = self._expect(DataTypeToken)
        identifier_token = self._expect(IdentifierToken)
        list_of_args: List[FunctionArgumentTerm] = self._parse_list_of_func_args()
        body: List[Term] = self._parse_body()

        self._exit_context()

        return FunctionTerm(
            return_dtype=self._transform_data_type_token(data_type_token),
            name=identifier_token.value,
            args=list_of_args,
            body=body,
        )

    def _parse_list_of_func_args(self) -> List[FunctionArgumentTerm]:
        self._expect(SquareLparenToken)

        args = []
        while not isinstance(self._current_token, SquareRparenToken):
            args.append(self._parse_func_arg())

            if isinstance(self._current_token, SquareRparenToken):
                break

            self._expect(CommaToken)

        self._expect(SquareRparenToken)

        return args

    def _parse_func_arg(self) -> FunctionArgumentTerm:
        identifier_token = self._expect(IdentifierToken)
        self._expect(ColonToken)
        data_type_token = self._expect(DataTypeToken)

        return FunctionArgumentTerm(name=identifier_token.value, dtype=self._transform_data_type_token(data_type_token))

    def _parse_return(self) -> ReturnTerm:
        self._expect(ReturnToken)

        expr = None
        if isinstance(self._current_token, ColonToken):
            self._expect(ColonToken)
            expr = self._parse_expr()

        return ReturnTerm(expr=expr)

    def _parse_for(self) -> ForTerm:
        self._enter_context(ParserContext.IN_CYCLE)

        self._expect(ForToken)

        self._expect(SquareLparenToken)

        start = None
        if not isinstance(self._current_token, ColonToken):
            if isinstance(self._current_token, IdentifierToken) and isinstance(self._peek(), ColonToken):
                start = self._parse_variable_def()
            elif isinstance(self._current_token, IdentifierToken):
                start = self._parse_variable_assign()

        self._expect(SemicolonToken)

        condition = self._parse_expr()

        self._expect(SemicolonToken)

        end = None
        if not isinstance(self._current_token, ColonToken):
            if isinstance(self._current_token, IdentifierToken):
                end = self._parse_variable_assign()

        self._expect(SquareRparenToken)

        body = self._parse_body()

        self._exit_context()

        return ForTerm(start=start, condition=condition, end=end, body=body)

    def _parse_continue(self) -> ContinueTerm:
        self._expect(ContinueToken)
        return ContinueTerm()

    def _parse_break(self) -> BreakTerm:
        self._expect(BreakToken)
        return BreakTerm()

    def _parse_if(self) -> BranchTerm:
        self._expect(IfToken)
        return self._parse_branch_with_condition()

    def _parse_elif(self) -> BranchTerm:
        self._expect(ElifToken)
        return self._parse_branch_with_condition()

    def _parse_branch_with_condition(self) -> BranchTerm:
        condition: ExpressionTerm = self._parse_if_condition()
        body: List[Term] = self._parse_body()

        next_branch = None
        if isinstance(self._current_token, ElifToken):
            next_branch = self._parse_elif()
        elif isinstance(self._current_token, ElseToken):
            next_branch = self._parse_else()

        return BranchTerm(condition=condition, body=body, next_branch=next_branch)

    def _parse_else(self) -> BranchTerm:
        self._expect(ElseToken)
        body: List[Term] = self._parse_body()

        return BranchTerm(condition=None, body=body, next_branch=None)

    def _parse_if_condition(self) -> ExpressionTerm:
        self._expect(SquareLparenToken)
        condition: ExpressionTerm = self._parse_expr()
        self._expect(SquareRparenToken)

        return condition

    def _parse_body(self) -> List[Term]:
        self._expect(CurlyLparenToken)

        terms: List[Term] = []
        while not isinstance(self._current_token, CurlyRparenToken):
            terms.append(self._parse_term_node())

        self._expect(CurlyRparenToken)

        return terms

    def _parse_print(self) -> PrintTerm:
        self._expect(PrintToken)
        args = self._parse_list_of_exps()

        return PrintTerm(args=args)

    def _parse_identifier_node(self) -> Union[FunctionCallTerm, VariableAssignmentTerm, VariableDefinitionTerm]:
        transitions = {
            LparenToken: self._parse_function_call,
            AssignToken: self._parse_variable_assign,
            ColonToken: self._parse_variable_def,
        }

        next_token = self._peek()
        for start_token_cls, parse_term_function in transitions.items():
            if isinstance(next_token, start_token_cls):
                return parse_term_function()

        self._throw_unexpected_token_error(next_token)

    def _parse_function_call(self) -> FunctionCallTerm:
        variable_name_token = self._expect(IdentifierToken)
        args = self._parse_list_of_exps()

        return FunctionCallTerm(name=variable_name_token.value, args=args)

    def _parse_list_of_exps(self) -> List[ExpressionTerm]:
        self._expect(LparenToken)

        args = []
        while not isinstance(self._current_token, RparenToken):
            args.append(self._parse_expr())

            if isinstance(self._current_token, RparenToken):
                break

            self._expect(CommaToken)

        self._expect(RparenToken)

        return args

    def _parse_variable_assign(self) -> VariableAssignmentTerm:
        variable_name_token = self._expect(IdentifierToken)
        self._expect(AssignToken)

        return VariableAssignmentTerm(
            name=variable_name_token.value,
            value=self._parse_variable_value_node(),
        )

    def _parse_variable_def(self) -> VariableDefinitionTerm:
        variable_name_token = self._expect(IdentifierToken)
        self._expect(ColonToken)

        data_type_token = self._expect(DataTypeToken)
        self._expect(AssignToken)

        return VariableDefinitionTerm(
            name=variable_name_token.value,
            dtype=self._transform_data_type_token(data_type_token),
            value=self._parse_variable_value_node(),
        )

    def _parse_variable_value_node(self) -> Union[InputTerm, ExpressionTerm]:
        if isinstance(self._current_token, InputToken):
            return self._parse_input()

        return self._parse_expr()

    def _parse_input(self) -> InputTerm:
        self._expect(InputToken)
        self._expect(LparenToken)

        term = InputTerm()
        if not isinstance(self._current_token, RparenToken):
            term.count = int(self._expect(NumberToken).value)
            self._expect(RparenToken)
        else:
            self._advance()

        return term

    def _parse_expr(self) -> ExpressionTerm:
        return self._parse_boolean_or()

    def _parse_boolean_or(self) -> ExpressionTerm:
        expr = self._parse_boolean_and()

        while isinstance(self._current_token, OrToken):
            self._advance()
            right = self._parse_boolean_and()
            expr = BinOpTerm(left=expr, op=LogicalOperator.OR, right=right)

        return expr

    def _parse_boolean_and(self) -> ExpressionTerm:
        expr = self._parse_boolean_not()

        while isinstance(self._current_token, AndToken):
            self._advance()
            right = self._parse_boolean_not()
            expr = BinOpTerm(left=expr, op=LogicalOperator.AND, right=right)

        return expr

    def _parse_boolean_not(self) -> ExpressionTerm:
        if isinstance(self._current_token, NotToken):
            self._advance()
            expr = self._parse_boolean_not()
            return UnaryOpTerm(op=LogicalOperator.NOT, expr=expr)

        return self._parse_comparison()

    def _parse_comparison(self) -> ExpressionTerm:
        operations = {
            EqualToken: ComparisonOperator.EQ,
            NotEqualToken: ComparisonOperator.NEQ,
            LessToken: ComparisonOperator.LT,
            LessOrEqualToken: ComparisonOperator.LTE,
            GreaterToken: ComparisonOperator.GT,
            GreaterOrEqualToken: ComparisonOperator.GTE,
        }

        left = self._parse_arithmetic_expr()

        op = operations.get(type(self._current_token))
        if op is not None:
            self._advance()
            right = self._parse_arithmetic_expr()

            return BinOpTerm(left=left, op=op, right=right)

        return left

    def _parse_arithmetic_expr(self) -> ExpressionTerm:
        operations = {
            PlusToken: ArithmeticOperator.ADD,
            MinusToken: ArithmeticOperator.SUB,
        }

        if isinstance(self._current_token, MinusToken):
            self._advance()
            expr = self._parse_arithmetic_expr()
            return UnaryOpTerm(op=ArithmeticOperator.SUB, expr=expr)

        expr = self._parse_addendum()

        while (op := operations.get(type(self._current_token))) is not None:
            self._advance()
            right = self._parse_arithmetic_expr()

            expr = BinOpTerm(left=expr, op=op, right=right)

        return expr

    def _parse_addendum(self) -> ExpressionTerm:
        operations = {
            AsteriskToken: ArithmeticOperator.MUL,
            SlashToken: ArithmeticOperator.DIV,
            PercentToken: ArithmeticOperator.MOD,
        }

        expr = self._parse_factor()

        while (op := operations.get(type(self._current_token))) is not None:
            self._advance()
            right = self._parse_addendum()
            expr = BinOpTerm(left=expr, op=op, right=right)

        return expr

    def _parse_factor(self) -> ExpressionTerm:
        operations = {
            ShiftLeftToken: BitwiseOperator.SHL,
            ShiftRightToken: BitwiseOperator.SHR,
        }

        expr = self._parse_bitwise_operand()

        while (op := operations.get(type(self._current_token))) is not None:
            self._advance()
            right = self._parse_factor()
            expr = BinOpTerm(left=expr, op=op, right=right)

        return expr

    def _parse_bitwise_operand(self) -> ExpressionTerm:
        if isinstance(self._current_token, LparenToken):
            self._expect(LparenToken)
            expr = self._parse_expr()
            self._expect(RparenToken)
            return expr

        return self._parse_base_element()

    def _parse_base_element(self) -> ExpressionTerm:
        token = self._current_token

        if isinstance(self._current_token, IdentifierToken):
            if isinstance(self._peek(), LparenToken):
                return self._parse_function_call()

            return self._parse_variable()

        if isinstance(self._current_token, NumberToken):
            return self._parse_number_literal()

        if isinstance(self._current_token, StringToken):
            return self._parse_string_literal()

        self._throw_unexpected_token_error(token)

    def _parse_number_literal(self) -> NumberLiteralTerm:
        return NumberLiteralTerm(value=int(self._expect(NumberToken).value))

    def _parse_string_literal(self) -> StringLiteralTerm:
        return StringLiteralTerm(value=self._expect(StringToken).value)

    def _parse_variable(self) -> VariableTerm:
        return VariableTerm(name=self._expect(IdentifierToken).value)

    def _transform_data_type_token(self, data_type_token) -> DataTypes:
        dtypes = {
            StringDataTypeToken: DataTypes.STR,
            IntegerDataTypeToken: DataTypes.INT,
            VoidDataTypeToken: DataTypes.VOID,
        }

        return dtypes[type(data_type_token)]

    def _throw_unexpected_token_error(self, token: Optional[Token] = None):
        if token is None:
            token = self._current_token

        raise ParserException(
            f"unexpected token {token!r} (look at fragment {self._get_tokens_fragment()}).",
        )

    def _throw_incorrect_term_error(self, token: Optional[Token] = None):
        if token is None:
            token = self._current_token

        raise ParserException(
            f"incorrect token {token!r} (look at fragment {self._get_tokens_fragment()}).",
        )

    def _get_tokens_fragment(self, indent: int = 5) -> str:
        fragment_start = max(0, self._current_index - indent)
        fragment_end = min(len(self._tokens), self._current_index + 1)

        return repr(self._tokens[fragment_start:fragment_end])
