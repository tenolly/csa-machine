import argparse

from . import compile_code

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The file with the source code")
    parser.add_argument("output", help="The file into which the source code will be compiled")
    args = parser.parse_args()

    print(compile_code(args.filename, args.output))
