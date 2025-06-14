import os

from .parser import Parser
from .tokenizer import Tokenizer
from .translator import Translator


def compile_code(filename: str, output: str) -> str:
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"unable to find {filename}")

    tokens = Tokenizer(open(filename, mode="r").read()).tokenize()
    terms = Parser(tokens).parse()
    translator = Translator(terms)
    compiled, string_representation = translator.translate()

    with open(output, mode="wb") as file:
        file.write(compiled)

    return string_representation
