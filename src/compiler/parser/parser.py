from enum import Enum
from functools import wraps
from typing import Callable, Dict, List, Optional, Type, Union

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
    Integer32DataTypeToken,
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
from .exceptions import ContextStackException, ParserException
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
    FunctionDefinitionTerm,
    InputTerm,
    LogicalOperator,
    NumberLiteralTerm,
    PrintTerm,
    ProgramTerm,
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


def set_context(context: ParserContext):
    def decorator(function: Callable):
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            self._enter_context(context)
            result = function(self, *args, **kwargs)
            self._exit_context()

            return result

        return wrapper

    return decorator


class Parser:
    _DATA_TYPE_TOKEN_MAP = {
        StringDataTypeToken: DataTypes.STR,
        Integer32DataTypeToken: DataTypes.INT32,
        VoidDataTypeToken: DataTypes.VOID,
    }

    _BITWISE_OPERATIONS_MAP = {
        ShiftLeftToken: BitwiseOperator.SHL,
        ShiftRightToken: BitwiseOperator.SHR,
    }

    _MULTIPLICATIVE_OPERATIONS_MAP = {
        AsteriskToken: ArithmeticOperator.MUL,
        SlashToken: ArithmeticOperator.DIV,
        PercentToken: ArithmeticOperator.MOD,
    }

    _ADDITIVE_OPERATIONS_MAP = {
        PlusToken: ArithmeticOperator.ADD,
        MinusToken: ArithmeticOperator.SUB,
    }

    _COMPARE_OPERATIONS_MAP = {
        EqualToken: ComparisonOperator.EQ,
        NotEqualToken: ComparisonOperator.NEQ,
        LessToken: ComparisonOperator.LT,
        LessOrEqualToken: ComparisonOperator.LTE,
        GreaterToken: ComparisonOperator.GT,
        GreaterOrEqualToken: ComparisonOperator.GTE,
    }

    def __init__(self, tokens: List[Token]):
        self._tokens: List[Token] = tokens

        self._current_index: int = -1
        self._current_token: Optional[Token] = None

        self._context_stack: List[ParserContext] = []

        self.terms: List[Term] = []

    def _enter_context(self, context: ParserContext) -> None:
        self._context_stack.append(context)

    def _exit_context(self) -> None:
        if len(self._context_stack) == 0:
            raise ContextStackException("context stask is empty")

        self._context_stack.pop()

    def _is_in_context(self, context: ParserContext) -> bool:
        return context in self._context_stack

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

        return ProgramTerm(terms=self.terms)

    def _parse_term_node(self) -> Term:
        transitions = {
            DataTypeToken: self._parse_func_def,
            ForToken: self._parse_for,
            IfToken: self._parse_if,
            IdentifierToken: self._parse_identifier_node,
            PrintToken: self._parse_print,
        }

        if self._is_in_context(ParserContext.IN_FUNCTION):
            transitions[ReturnToken] = self._parse_return

        if self._is_in_direct_context(ParserContext.IN_CYCLE):
            transitions[ContinueToken] = self._parse_continue
            transitions[BreakToken] = self._parse_break

        for start_token_cls, parse_term_function in transitions.items():
            if isinstance(self._current_token, start_token_cls):
                return parse_term_function()

        self._throw_unexpected_token_error()

    @set_context(ParserContext.IN_FUNCTION)
    def _parse_func_def(self) -> FunctionDefinitionTerm:
        return FunctionDefinitionTerm(
            return_dtype=self._parse_data_type(),
            name=self._expect(IdentifierToken).value,
            args=self._parse_list_of_func_args(),
            body=self._parse_body(),
        )

    def _parse_list_of_func_args(self) -> List[FunctionArgumentTerm]:
        return self._parse_comma_separated_list(SquareLparenToken, SquareRparenToken, self._parse_func_arg)

    def _parse_func_arg(self) -> FunctionArgumentTerm:
        identifier_token = self._expect(IdentifierToken)
        self._expect(ColonToken)

        return FunctionArgumentTerm(
            name=identifier_token.value,
            dtype=self._parse_data_type(),
        )

    def _parse_return(self) -> ReturnTerm:
        self._expect(ReturnToken)

        expr = None
        if isinstance(self._current_token, ColonToken):
            self._expect(ColonToken)
            expr = self._parse_expr()

        return ReturnTerm(expr=expr)

    @set_context(ParserContext.IN_CYCLE)
    def _parse_for(self) -> ForTerm:
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

        return ForTerm(start=start, condition=condition, end=end, body=self._parse_body())

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
        condition = self._parse_if_condition()
        body = self._parse_body()

        next_branch = None
        if isinstance(self._current_token, ElifToken):
            next_branch = self._parse_elif()
        elif isinstance(self._current_token, ElseToken):
            next_branch = self._parse_else()

        return BranchTerm(condition=condition, body=body, next_branch=next_branch)

    def _parse_else(self) -> BranchTerm:
        self._expect(ElseToken)
        return BranchTerm(condition=None, body=self._parse_body(), next_branch=None)

    def _parse_if_condition(self) -> ExpressionTerm:
        self._expect(SquareLparenToken)
        condition = self._parse_expr()
        self._expect(SquareRparenToken)

        return condition

    def _parse_body(self) -> List[Term]:
        self._expect(CurlyLparenToken)

        terms = []
        while not isinstance(self._current_token, CurlyRparenToken):
            terms.append(self._parse_term_node())

        self._expect(CurlyRparenToken)

        return terms

    def _parse_print(self) -> PrintTerm:
        self._expect(PrintToken)
        return PrintTerm(args=self._parse_list_of_exprs())

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
        return FunctionCallTerm(
            name=self._expect(IdentifierToken).value,
            args=self._parse_list_of_exprs(),
        )

    def _parse_list_of_exprs(self) -> List[ExpressionTerm]:
        return self._parse_comma_separated_list(LparenToken, RparenToken, self._parse_expr)

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

        data_type = self._parse_data_type()
        self._expect(AssignToken)

        return VariableDefinitionTerm(
            name=variable_name_token.value,
            dtype=data_type,
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

    def _parse_binary_op_expression(
        self,
        parse_next_level: Callable[[], ExpressionTerm],
        operations_map: Dict[Token, Union[ArithmeticOperator, LogicalOperator, ComparisonOperator, BitwiseOperator]],
    ) -> ExpressionTerm:
        expr = parse_next_level()

        while (op_type := operations_map.get(type(self._current_token))) is not None:
            self._advance()
            right = parse_next_level()
            expr = BinOpTerm(left=expr, op=op_type, right=right)

        return expr

    def _parse_boolean_or(self) -> ExpressionTerm:
        return self._parse_binary_op_expression(self._parse_boolean_and, {OrToken: LogicalOperator.OR})

    def _parse_boolean_and(self) -> ExpressionTerm:
        return self._parse_binary_op_expression(self._parse_boolean_not, {AndToken: LogicalOperator.AND})

    def _parse_boolean_not(self) -> ExpressionTerm:
        if isinstance(self._current_token, NotToken):
            self._advance()
            expr = self._parse_boolean_not()
            return UnaryOpTerm(op=LogicalOperator.NOT, expr=expr)

        return self._parse_comparison()

    def _parse_comparison(self) -> ExpressionTerm:
        return self._parse_binary_op_expression(self._parse_arithmetic_expr, self._COMPARE_OPERATIONS_MAP)

    def _parse_arithmetic_expr(self) -> ExpressionTerm:
        return self._parse_binary_op_expression(self._parse_addendum, self._ADDITIVE_OPERATIONS_MAP)

    def _parse_addendum(self) -> ExpressionTerm:
        return self._parse_binary_op_expression(self._parse_factor, self._MULTIPLICATIVE_OPERATIONS_MAP)

    def _parse_factor(self) -> ExpressionTerm:
        return self._parse_binary_op_expression(self._parse_unary_expression, self._BITWISE_OPERATIONS_MAP)

    def _parse_unary_expression(self) -> ExpressionTerm:
        if isinstance(self._current_token, MinusToken):
            self._advance()
            expr = self._parse_unary_expression()
            return UnaryOpTerm(op=ArithmeticOperator.SUB, expr=expr)

        return self._parse_bitwise_operand()

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

    def _parse_comma_separated_list(
        self,
        start_token_type: Type[Token],
        end_token_type: Type[Token],
        parse_item_func: Callable,
    ) -> List[Term]:
        self._expect(start_token_type)

        items = []
        if not isinstance(self._current_token, end_token_type):
            items.append(parse_item_func())

            while isinstance(self._current_token, CommaToken):
                self._advance()
                items.append(parse_item_func())

        self._expect(end_token_type)

        return items

    def _parse_data_type(self) -> DataTypes:
        return self._DATA_TYPE_TOKEN_MAP[type(self._expect(DataTypeToken))]

    def _parse_number_literal(self) -> NumberLiteralTerm:
        return NumberLiteralTerm(value=int(self._expect(NumberToken).value))

    def _parse_string_literal(self) -> StringLiteralTerm:
        return StringLiteralTerm(value=self._expect(StringToken).value)

    def _parse_variable(self) -> VariableTerm:
        return VariableTerm(name=self._expect(IdentifierToken).value)

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
