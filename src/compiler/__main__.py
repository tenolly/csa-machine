import argparse
import os

from .parser import Parser
from .tokenizer import Tokenizer
from .translator import Translator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The file with the source code")
    parser.add_argument("output", help="The file into which the source code will be compiled")
    parser.parse_args()

    args = parser.parse_args()

    if not os.path.isfile(args.filename):
        raise FileNotFoundError(f"unable to find {args.filename}")

    tokens = Tokenizer(open(args.filename, mode="r").read()).tokenize()
    terms = Parser(tokens).parse()
    translator = Translator(terms)
    compiled = translator.translate()

    with open(args.output, mode="wb") as file:
        file.write(compiled)
