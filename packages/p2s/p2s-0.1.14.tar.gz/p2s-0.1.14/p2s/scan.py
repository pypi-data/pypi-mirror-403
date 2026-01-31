import sys
import ast
import numpy as np
from itertools import accumulate


def main():
    if sys.stdin.isatty():
        print("No input provided. Please pipe data into this script.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("No lambda provided. Please provide a lambda as an argument. Example labmda a, c: a + c, just provide \"a+c\" where a is the accumulator and c is the current", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 3:
        print("No initial accumulator value provided", file=sys.stderr)
        sys.exit(1)

    tree = ast.parse(f"lambda a, c: {sys.argv[1]}", mode='eval')
    f = eval(compile(tree, filename='<ast>', mode='eval'))
    initial = ast.literal_eval(sys.argv[2])
    for result in accumulate(map(lambda x: x[:-1], sys.stdin), f, initial=initial):
        print(result)

