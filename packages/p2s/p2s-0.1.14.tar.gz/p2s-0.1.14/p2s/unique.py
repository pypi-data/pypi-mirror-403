import sys
import numpy as np


def main():
    if sys.stdin.isatty():
        print("No input provided. Please pipe data into this script.", file=sys.stderr)
        sys.exit(1)
    for x in sorted(set([x[:-1] for x in sys.stdin])):
        print(x)