import sys
import numpy as np
from .flat import data

if len(sys.argv) != 2:
    print("Usage: p2s.q <quantile in %> e.g. \"p2s.q 25\" for 25%")
    exit(1)
quantile = float(sys.argv[1])
print(f"{np.nanquantile(data, quantile/100)}")


# for the entrypoint
def main():
    pass