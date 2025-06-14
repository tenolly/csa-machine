import argparse

from . import run_simulation

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("memory_filename", help="The memory dump file name")
    parser.add_argument("config_filename", help="The machine's config file name")
    args = parser.parse_args()

    run_simulation(args.memory_filename, args.config_filename)
