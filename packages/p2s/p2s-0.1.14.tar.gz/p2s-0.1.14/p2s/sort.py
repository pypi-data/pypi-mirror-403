import sys
import ast
import numpy as np
from functools import reduce


def main():
    if sys.stdin.isatty():
        print("No input provided. Please pipe data into this script.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("No lambda provided. Please provide a lambda as an argument. Example labmda a, c: a + c, just provide \"a+c\" where a is the accumulator and c is the current", file=sys.stderr)
        sys.exit(1)

    tree = ast.parse(f"lambda x: {sys.argv[1]}", mode='eval')
    f = eval(compile(tree, filename='<ast>', mode='eval'))
    for x in sorted(sys.stdin, key=lambda x: f(x[:-1])):
        print(x[:-1])
