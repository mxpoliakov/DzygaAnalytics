"""This module contains entry point to manually update donation source from CSV"""
import argparse
import pathlib

from sources.manual import Manual

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--donation_source", type=str, required=True)
    parser.add_argument("-f", "--filepath", type=pathlib.Path, required=True)
    args = parser.parse_args()
    Manual(args.donation_source, args.filepath).write_new_data()
