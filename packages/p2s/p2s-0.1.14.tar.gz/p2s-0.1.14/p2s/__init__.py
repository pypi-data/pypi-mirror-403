from pathlib import Path
import sys

if Path(sys.argv[0]).name == "p2s":
    if len(sys.argv) == 2:
        from .flat import data
        import numpy as np
        format = sys.argv[1]
        while len(format) > 0:
            c = format[0]
            format = format[1:]
            if c == "c":
                print(f"Count: {np.count_nonzero(np.isnan(data) == False)}")
            elif c == "m":
                print(f"Mean: {np.nanmean(data)}")
            elif c == "s":
                print(f"Std: {np.nanstd(data)}")
            elif c == "q":
                c1 = format[0]
                c2 = format[1]
                assert c1.isdigit() and c2.isdigit()
                quantile_string = f"{c1}{c2}"
                quantile = int(quantile_string) / 100
                format = format[2:]
                print(f"Q{quantile_string}: {np.nanquantile(data, quantile)}")
            else:
                print(f"Unknown format modifier: {c}")
    else:
        from .stats import *


# for the entrypoint
def main():
    pass