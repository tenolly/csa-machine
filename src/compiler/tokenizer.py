from typing import NoReturn, List
from .tokens import (
    Token,
    StringToken,
    NumberToken,
    IdentifierToken,
    DataTypeToken,
    IfToken,
    ElifToken,
    ElseToken,
    ForToken,
    ContinueToken,
    BreakToken,
    ReturnToken,
    CommaToken,
    ColonToken,
    SemicolonToken,
    LparenToken,
    RparenToken,
    PlusToken,
    MinusToken,
    AsteriskToken,
    SlashToken,
    PercentToken,
    AndToken,
    OrToken,
    NotToken,
    InputToken,
    PrintToken,
    AssignToken,
    EqualToken,
    LessToken,
    LessOrEqualToken,
    ShiftLeftToken,
    NotEqualToken,
    GreaterOrEqualToken,
    ShiftRightToken,
    GreaterToken,
    SquareLparenToken,
    SquareRparenToken,
    CurlyLparenToken,
    CurlyRparenToken,
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

DATA_TYPES = ("str", "int", "void")

SINGLE_SIGNS = (
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
)

SINGLE_OR_DOUBLE_SIGNS = (
    ASSIGN := "=",
    EQUAL := "==",
    LESS := "<",
    LESS_OR_EQUAL := "<=",
    SHIFT_LEFT := "<<",
    GREATER := ">",
    GREATER_OR_EQUAL := ">=",
    SHIFT_RIGHT := ">>",
)

DOUBLE_SIGNS = (
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
    def __init__(self, program: str):
        self._program = program

        self._current_index = -1
        self._current_char = None

        self.tokens = []

    def _advance(self) -> str:
        self._current_index += 1

        if self._current_index < len(self._program):
            self._current_char = self._program[self._current_index]
        else:
            self._current_char = None

        return self._current_char

    def peek_next(self) -> str:
        next_index = self._current_index + 1

        if next_index < len(self._program):
            return self._program[next_index]

    def parse(self) -> List[Token]:
        transitions = {
            DIGITS: self._parse_number,
            QUOTES: self._parse_string,
            CHARACTERS: self._parse_word,
            SINGLE_SIGNS: self._parse_single_sign,
            SINGLE_OR_DOUBLE_SIGNS: self._parse_single_or_double_sign,
            tuple(sign[0] for sign in DOUBLE_SIGNS): self._parse_double_sign,
            COMMENT_MARK: self._skip_comment,
            SPACE_OPTIONS: self._skip_char,
        }

        while self._advance() is not None:
            for target_chars, parse_target_token in transitions.items():
                if self._current_char == "!":
                    print(target_chars)
                if self._current_char in target_chars:
                    parse_target_token()
                    break
            else:
                self._throw_unexpected_char_error()

        return self.tokens

    def _parse_single_sign(self) -> None:
        new_token = None

        if self._current_char == COMMA:
            new_token = CommaToken()
        elif self._current_char == COLON:
            new_token = ColonToken()
        elif self._current_char == SEMICOLON:
            new_token = SemicolonToken()
        elif self._current_char == LPAREN:
            new_token = LparenToken()
        elif self._current_char == RPAREN:
            new_token = RparenToken()
        elif self._current_char == SQUARE_LPAREN:
            new_token = SquareLparenToken()
        elif self._current_char == SQUARE_RPAREN:
            new_token = SquareRparenToken()
        elif self._current_char == CURLY_LPAREN:
            new_token = CurlyLparenToken()
        elif self._current_char == CURLY_RPAREN:
            new_token = CurlyRparenToken()
        elif self._current_char == PLUS:
            new_token = PlusToken()
        elif self._current_char == MINUS:
            new_token = MinusToken()
        elif self._current_char == ASTERISK:
            new_token = AsteriskToken()
        elif self._current_char == SLASH:
            new_token = SlashToken()
        elif self._current_char == PERCENT:
            new_token = PercentToken()

        if new_token is None:
            self._throw_undefined_token_error(self._current_char)

        self.tokens.append(new_token)

    def _parse_single_or_double_sign(self) -> None:
        new_token = None
        next_char = self.peek_next()

        if self._current_char == ASSIGN:
            if next_char == EQUAL[1]:
                new_token = EqualToken()
                self._advance()
            else:
                new_token = AssignToken()
        elif self._current_char == LESS:
            if next_char == LESS_OR_EQUAL[1]:
                new_token = LessOrEqualToken()
                self._advance()
            elif next_char == SHIFT_LEFT[1]:
                new_token = ShiftLeftToken()
                self._advance()
            elif next_char == NOT_EQUAL[1]:
                new_token = NotEqualToken()
                self._advance()
            else:
                new_token = LessToken()
        elif self._current_char == GREATER:
            if next_char == GREATER_OR_EQUAL[1]:
                new_token = GreaterOrEqualToken()
                self._advance()
            elif next_char == SHIFT_RIGHT[1]:
                new_token = ShiftRightToken()
                self._advance()
            else:
                new_token = GreaterToken()

        if new_token is None:
            self._throw_undefined_token_error(self._current_char)

        self.tokens.append(new_token)

    def _parse_double_sign(self) -> None:
        new_token = None
        next_char = self.peek_next()

        if self._current_char + next_char == NOT_EQUAL:
            new_token = NotEqualToken()

        if new_token is None:
            self._throw_undefined_token_error(self._current_char + next_char)

        self.tokens.append(new_token)

    def _parse_word(self) -> None:
        token = ""

        while self._current_char is not None:
            token += self._current_char

            if self.peek_next() not in CHARACTERS + DIGITS:
                break

            self._advance()

        new_token = None

        if token in DATA_TYPES:
            new_token = DataTypeToken(token)
        elif token in BRANCHES:
            if token == IF_BRANCH:
                new_token = IfToken()
            elif token == ELIF_BRANCH:
                new_token = ElifToken()
            elif token == ELSE_BRANCH:
                new_token = ElseToken()
        elif token in CYCLE_CONTROL:
            if token == FOR:
                new_token = ForToken()
            elif token == CONTINUE:
                new_token = ContinueToken()
            elif token == BREAK:
                new_token = BreakToken()
        elif token in FUNCTION_CONTROL:
            if token == RETURN:
                new_token = ReturnToken()
        elif token in LOGICAL_OPERATIONS:
            if token == AND:
                new_token = AndToken()
            elif token == OR:
                new_token = OrToken()
            elif token == NOT:
                new_token = NotToken()
        elif token in IO_OPERATIONS:
            if token == INPUT:
                new_token = InputToken()
            elif token == PRINT:
                new_token = PrintToken()
        else:
            new_token = IdentifierToken(token)

        if new_token is None:
            self._throw_undefined_token_error(token)

        self.tokens.append(new_token)

    def _parse_number(self) -> None:
        token = ""

        while self._current_char is not None:
            token += self._current_char

            if self.peek_next() not in DIGITS:
                break

            self._advance()

        self.tokens.append(NumberToken(token))

    def _parse_string(self) -> None:
        token = self._current_char

        while self._advance() is not None:
            token += self._current_char

            if self._current_char in QUOTES:
                break

        if token[-1] not in QUOTES:
            self._throw_incorrect_token_error(token)

        self.tokens.append(StringToken(token))

    def _skip_comment(self) -> None:
        while self._advance() is not None:
            if self._current_char == NEW_LINE:
                break

    def _skip_char(self) -> None:
        pass

    def _throw_unexpected_char_error(self) -> NoReturn:
        raise ValueError(
            f"unexpected char {repr(self._current_char)} at {self._current_index} index "
            f"(look at fragment {self._get_program_fragment()}).",
        )

    def _throw_undefined_token_error(self, token: str) -> NoReturn:
        raise ValueError(
            f"undefined token {token} at {self._current_index} index "
            f"(look at fragment {self._get_program_fragment()}).",
        )

    def _throw_incorrect_token_error(self, token: str) -> NoReturn:
        raise ValueError(
            f"incorrect token {token} at {self._current_index} index "
            f"(look at fragment {self._get_program_fragment()}).",
        )

    def _get_program_fragment(self, indent: int = 20) -> str:
        fragment_start = max(0, self._current_index - indent)
        fragment_end = min(len(self._program), self._current_index + indent)

        return repr(self._program[fragment_start:fragment_end])
