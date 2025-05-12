class Token:
    def __str__(self) -> str:
        return self._get_token_class_name()

    def _get_token_class_name(self) -> str:
        return self.__class__.__name__.replace("Token", "").upper()


class CommaToken(Token):
    def __repr__(self) -> str:
        return ","


class ColonToken(Token):
    def __repr__(self) -> str:
        return ":"


class SemicolonToken(Token):
    def __repr__(self) -> str:
        return ";"


class LparenToken(Token):
    def __repr__(self) -> str:
        return "("


class RparenToken(Token):
    def __repr__(self) -> str:
        return ")"


class SquareLparenToken(Token):
    def __repr__(self) -> str:
        return "["


class SquareRparenToken(Token):
    def __repr__(self) -> str:
        return "]"


class CurlyLparenToken(Token):
    def __repr__(self) -> str:
        return "{"


class CurlyRparenToken(Token):
    def __repr__(self) -> str:
        return "}"


class PlusToken(Token):
    def __repr__(self) -> str:
        return "+"


class MinusToken(Token):
    def __repr__(self) -> str:
        return "-"


class AsteriskToken(Token):
    def __repr__(self) -> str:
        return "*"


class SlashToken(Token):
    def __repr__(self) -> str:
        return "/"


class PercentToken(Token):
    def __repr__(self) -> str:
        return "%"


class AssignToken(Token):
    def __repr__(self) -> str:
        return "="


class EqualToken(Token):
    def __repr__(self) -> str:
        return "=="


class LessToken(Token):
    def __repr__(self) -> str:
        return "<"


class LessOrEqualToken(Token):
    def __repr__(self) -> str:
        return "<="


class ShiftLeftToken(Token):
    def __repr__(self) -> str:
        return "<<"


class NotEqualToken(Token):
    def __repr__(self) -> str:
        return "<>"


class GreaterToken(Token):
    def __repr__(self) -> str:
        return ">"


class GreaterOrEqualToken(Token):
    def __repr__(self) -> str:
        return ">="


class ShiftRightToken(Token):
    def __repr__(self) -> str:
        return ">>"


class ForToken(Token):
    def __repr__(self) -> str:
        return "for"


class ContinueToken(Token):
    def __repr__(self) -> str:
        return "continue"


class BreakToken(Token):
    def __repr__(self) -> str:
        return "break"


class IfToken(Token):
    def __repr__(self) -> str:
        return "if"


class ElifToken(Token):
    def __repr__(self) -> str:
        return "elif"


class ElseToken(Token):
    def __repr__(self) -> str:
        return "else"


class AndToken(Token):
    def __repr__(self) -> str:
        return "and"


class OrToken(Token):
    def __repr__(self) -> str:
        return "or"


class NotToken(Token):
    def __repr__(self) -> str:
        return "not"


class ReturnToken(Token):
    def __repr__(self) -> str:
        return "return"


class InputToken(Token):
    def __repr__(self) -> str:
        return "input"


class PrintToken(Token):
    def __repr__(self) -> str:
        return "print"


class StringToken(Token):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"{self._get_token_class_name()}({self.value})"

    def __repr__(self) -> str:
        return self.value


class NumberToken(Token):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"{self._get_token_class_name()}({self.value})"

    def __repr__(self) -> str:
        return self.value


class IdentifierToken(Token):
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return f"{self._get_token_class_name()}({self.name})"

    def __repr__(self) -> str:
        return self.name


class DataTypeToken(Token):
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return f"{self._get_token_class_name()}({self.name})"

    def __repr__(self) -> str:
        return self.name
