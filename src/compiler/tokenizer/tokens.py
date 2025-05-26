from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    value: str

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return repr(self.value)

    def info(self) -> str:
        return self.__class__.__name__.replace("Token", "").upper()


@dataclass(frozen=True)
class CommaToken(Token):
    value: str = ","


@dataclass(frozen=True)
class ColonToken(Token):
    value: str = ":"


@dataclass(frozen=True)
class SemicolonToken(Token):
    value: str = ";"


@dataclass(frozen=True)
class LparenToken(Token):
    value: str = "("


@dataclass(frozen=True)
class RparenToken(Token):
    value: str = ")"


@dataclass(frozen=True)
class SquareLparenToken(Token):
    value: str = "["


@dataclass(frozen=True)
class SquareRparenToken(Token):
    value: str = "]"


@dataclass(frozen=True)
class CurlyLparenToken(Token):
    value: str = "{"


@dataclass(frozen=True)
class CurlyRparenToken(Token):
    value: str = "}"


@dataclass(frozen=True)
class PlusToken(Token):
    value: str = "+"


@dataclass(frozen=True)
class MinusToken(Token):
    value: str = "-"


@dataclass(frozen=True)
class AsteriskToken(Token):
    value: str = "*"


@dataclass(frozen=True)
class SlashToken(Token):
    value: str = "/"


@dataclass(frozen=True)
class PercentToken(Token):
    value: str = "%"


@dataclass(frozen=True)
class AssignToken(Token):
    value: str = "="


@dataclass(frozen=True)
class EqualToken(Token):
    value: str = "=="


@dataclass(frozen=True)
class NotEqualToken(Token):
    value: str = "!="


@dataclass(frozen=True)
class LessToken(Token):
    value: str = "<"


@dataclass(frozen=True)
class GreaterToken(Token):
    value: str = ">"


@dataclass(frozen=True)
class LessOrEqualToken(Token):
    value: str = "<="


@dataclass(frozen=True)
class GreaterOrEqualToken(Token):
    value: str = ">="


@dataclass(frozen=True)
class ShiftLeftToken(Token):
    value: str = "<<"


@dataclass(frozen=True)
class ShiftRightToken(Token):
    value: str = ">>"


@dataclass(frozen=True)
class ForToken(Token):
    value: str = "for"


@dataclass(frozen=True)
class ContinueToken(Token):
    value: str = "continue"


@dataclass(frozen=True)
class BreakToken(Token):
    value: str = "break"


@dataclass(frozen=True)
class IfToken(Token):
    value: str = "if"


@dataclass(frozen=True)
class ElifToken(Token):
    value: str = "elif"


@dataclass(frozen=True)
class ElseToken(Token):
    value: str = "else"


@dataclass(frozen=True)
class AndToken(Token):
    value: str = "and"


@dataclass(frozen=True)
class OrToken(Token):
    value: str = "or"


@dataclass(frozen=True)
class NotToken(Token):
    value: str = "not"


@dataclass(frozen=True)
class ReturnToken(Token):
    value: str = "return"


@dataclass(frozen=True)
class InputToken(Token):
    value: str = "input"


@dataclass(frozen=True)
class PrintToken(Token):
    value: str = "print"


@dataclass(frozen=True)
class StringToken(Token):
    value: str


@dataclass(frozen=True)
class NumberToken(Token):
    value: str


@dataclass(frozen=True)
class IdentifierToken(Token):
    value: str


@dataclass(frozen=True)
class DataTypeToken(Token):
    value: str


@dataclass(frozen=True)
class StringDataTypeToken(DataTypeToken):
    value: str = "str"


@dataclass(frozen=True)
class IntegerDataTypeToken(DataTypeToken):
    value: str = "int"


@dataclass(frozen=True)
class VoidDataTypeToken(DataTypeToken):
    value: str = "void"
