import numpy as np
from .flat import data

print(f"Count: {np.count_nonzero(np.isnan(data) == False)}")
print(f"Minimum: {np.nanmin(data)}")
print(f"Maximum: {np.nanmax(data)}")
print(f"Mean: {np.nanmean(data)}")
print(f"Sum: {np.nansum(data)}")
print(f"Std: {np.nanstd(data)}")
print(f"Q05: {np.nanquantile(data, 0.05)}")
print(f"Q25: {np.nanquantile(data, 0.25)}")
print(f"Q50/median: {np.nanquantile(data, 0.50)}")
print(f"Q75: {np.nanquantile(data, 0.75)}")
print(f"Q95: {np.nanquantile(data, 0.95)}")

# for the entrypoint
def main():
    pass
