from typing import List, NoReturn, Optional

from .exceptions import TokenizeException
from .tokens import (
    AndToken,
    AssignToken,
    AsteriskToken,
    BreakToken,
    ColonToken,
    CommaToken,
    ContinueToken,
    CurlyLparenToken,
    CurlyRparenToken,
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

IO_OPERATIONS = (
    INPUT := "input",
    PRINT := "print",
)

FUNCTION_CONTROL = (
    RETURN := "return",
)

CYCLE_CONTROL = (
    FOR := "for",
    CONTINUE := "continue",
    BREAK := "break",
)

BRANCHES = (
    IF_BRANCH := "if",
    ELIF_BRANCH := "elif",
    ELSE_BRANCH := "else",
)

LOGICAL_OPERATIONS = (
    AND := "and",
    OR := "or",
    NOT := "not",
)

DATA_TYPES = (
    STR_DATA_TYPE := "str",
    INT_DATA_TYPE := "int",
    VOID_DATA_TYPE := "void",
)

SIGNS = (
    COMMA := ",",
    COLON := ":",
    SEMICOLON := ";",
    LPAREN := "(",
    RPAREN := ")",
    SQUARE_LPAREN := "[",
    SQUARE_RPAREN := "]",
    CURLY_LPAREN := "{",
    CURLY_RPAREN := "}",
    PLUS := "+",
    MINUS := "-",
    ASTERISK := "*",
    SLASH := "/",
    PERCENT := "%",
    ASSIGN := "=",
    EQUAL := "==",
    LESS := "<",
    LESS_OR_EQUAL := "<=",
    SHIFT_LEFT := "<<",
    GREATER := ">",
    GREATER_OR_EQUAL := ">=",
    SHIFT_RIGHT := ">>",
    NOT_EQUAL := "!=",
)

COMMENT_MARK = (
    "#",
)

QUOTES = (
    "\"",
)

SPACE_OPTIONS = (
    NEW_LINE := "\n",
    "\t",
    " ",
)

DIGITS = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")

CHARACTERS = (
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K",
    "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
    "W", "X", "Y", "Z", "a", "b", "c", "d", "e", "f", "g",
    "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r",
    "s", "t", "u", "v", "w", "x", "y", "z", "_",
)


class Tokenizer:
    _CHAR2_TO_TOKEN = {
        EQUAL: EqualToken,
        LESS_OR_EQUAL: LessOrEqualToken,
        SHIFT_LEFT: ShiftLeftToken,
        GREATER_OR_EQUAL: GreaterOrEqualToken,
        SHIFT_RIGHT: ShiftRightToken,
        NOT_EQUAL: NotEqualToken,
    }

    _CHAR_TO_TOKEN = {
        ASSIGN: AssignToken,
        LESS: LessToken,
        GREATER: GreaterToken,
        COMMA: CommaToken,
        COLON: ColonToken,
        SEMICOLON: SemicolonToken,
        LPAREN: LparenToken,
        RPAREN: RparenToken,
        SQUARE_LPAREN: SquareLparenToken,
        SQUARE_RPAREN: SquareRparenToken,
        CURLY_LPAREN: CurlyLparenToken,
        CURLY_RPAREN: CurlyRparenToken,
        PLUS: PlusToken,
        MINUS: MinusToken,
        ASTERISK: AsteriskToken,
        SLASH: SlashToken,
        PERCENT: PercentToken,
    }

    _DATA_TYPE_TO_TOKEN = {
        STR_DATA_TYPE: StringDataTypeToken,
        INT_DATA_TYPE: IntegerDataTypeToken,
        VOID_DATA_TYPE: VoidDataTypeToken,
    }

    _BRANCH_OPTION_TO_TOKEN = {
        IF_BRANCH: IfToken,
        ELIF_BRANCH: ElifToken,
        ELSE_BRANCH: ElseToken,
    }

    _CYCLE_CONTROL_TO_TOKEN = {
        FOR: ForToken,
        CONTINUE: ContinueToken,
        BREAK: BreakToken,
    }

    _FUNCTION_CONTROL_TO_TOKEN = {
        RETURN: ReturnToken,
    }

    _LOGICAL_OPERATION_TO_TOKEN = {
        AND: AndToken,
        OR: OrToken,
        NOT: NotToken,
    }

    _IO_OPERATION_TO_TOKEN = {
        INPUT: InputToken,
        PRINT: PrintToken,
    }

    def __init__(self, program: str):
        self._program: str = program

        self._current_index: int = -1
        self._current_char: Optional[str] = None

        self.tokens: List[Token] = []

    def _advance(self, n: int = 1) -> Optional[str]:
        self._current_index += n

        if 0 <= self._current_index < len(self._program):
            self._current_char = self._program[self._current_index]
        else:
            self._current_char = None

        return self._current_char

    def _peek(self, n: int = 1) -> Optional[str]:
        next_index = self._current_index + n

        if 0 <= next_index < len(self._program):
            return self._program[next_index]

    def tokenize(self) -> List[Token]:
        transitions = {
            DIGITS: self._parse_number,
            QUOTES: self._parse_string,
            CHARACTERS: self._parse_word,
            SIGNS: self._parse_sign,
            COMMENT_MARK: self._skip_comment,
            SPACE_OPTIONS: self._skip_char,
        }

        self._advance()
        while self._current_char is not None:
            for target_chars, parse_target_token in transitions.items():
                if (
                    self._current_char in target_chars or
                    self._peek() is not None and self._current_char + self._peek() in target_chars
                ):
                    parse_target_token()
                    break
            else:
                self._throw_unexpected_char_error()

        return self.tokens

    def _parse_sign(self) -> None:
        first_char = self._current_char
        second_char = self._advance()

        if second_char is not None:
            token_cls = self._CHAR2_TO_TOKEN.get(first_char + second_char)
            if token_cls is not None:
                self.tokens.append(token_cls())
                self._advance()
                return

        token_cls = self._CHAR_TO_TOKEN.get(first_char)
        if token_cls is None:
            self._throw_undefined_token_error(first_char)

        self.tokens.append(token_cls())

    def _parse_word(self) -> None:
        word = ""

        while self._current_char in CHARACTERS + DIGITS:
            word += self._current_char
            self._advance()

        token_cls = None
        if word in DATA_TYPES:
            token_cls = self._DATA_TYPE_TO_TOKEN[word]
        elif word in BRANCHES:
            token_cls = self._BRANCH_OPTION_TO_TOKEN[word]
        elif word in CYCLE_CONTROL:
            token_cls = self._CYCLE_CONTROL_TO_TOKEN[word]
        elif word in FUNCTION_CONTROL:
            token_cls = self._FUNCTION_CONTROL_TO_TOKEN[word]
        elif word in LOGICAL_OPERATIONS:
            token_cls = self._LOGICAL_OPERATION_TO_TOKEN[word]
        elif word in IO_OPERATIONS:
            token_cls = self._IO_OPERATION_TO_TOKEN[word]

        if token_cls is None:
            token = IdentifierToken(word)
        else:
            token = token_cls()

        self.tokens.append(token)

    def _parse_number(self) -> None:
        token = ""

        while self._current_char in DIGITS:
            token += self._current_char
            self._advance()

        self.tokens.append(NumberToken(token))

    def _parse_string(self) -> None:
        token = ""

        while True:
            self._advance()

            if self._current_char is None:
                self._throw_incorrect_token_error(token)

            if self._current_char in QUOTES:
                break

            token += self._current_char

        self._advance()
        self.tokens.append(StringToken(token))

    def _skip_comment(self) -> None:
        while self._advance() is not None:
            if self._current_char == NEW_LINE:
                self._advance()
                break

    def _skip_char(self) -> None:
        self._advance()

    def _throw_unexpected_char_error(self) -> NoReturn:
        raise TokenizeException(
            f"unexpected char {repr(self._current_char)} at {self._current_index} index "
            f"(look at fragment {self._get_program_fragment()}).",
        )

    def _throw_undefined_token_error(self, token: str) -> NoReturn:
        raise TokenizeException(
            f"undefined token {token} at {self._current_index} index "
            f"(look at fragment {self._get_program_fragment()}).",
        )

    def _throw_incorrect_token_error(self, token: str) -> NoReturn:
        raise TokenizeException(
            f"incorrect token {token} at {self._current_index} index "
            f"(look at fragment {self._get_program_fragment()}).",
        )

    def _get_program_fragment(self, indent: int = 20) -> str:
        fragment_start = max(0, self._current_index - indent)
        fragment_end = min(len(self._program), self._current_index + indent)

        return repr(self._program[fragment_start:fragment_end])
