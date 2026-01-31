import sys
import numpy as np
from .flat import data

if len(sys.argv) != 3:
    print("Usage: p2s.iqm <quantile in %>  <quantile in %> e.g. \"p2s.q 25 75\" for 25% - 75%")
    exit(1)
lower_quantile = float(sys.argv[1])
upper_quantile = float(sys.argv[2])


lower_threshold = np.nanquantile(data, lower_quantile / 100)
upper_threshold = np.nanquantile(data, upper_quantile / 100)

filtered_data = data[(data >= lower_threshold) & (data <= upper_threshold)]
print(f"{np.nanmean(filtered_data)}")

# for the entrypoint
def main():
    pass