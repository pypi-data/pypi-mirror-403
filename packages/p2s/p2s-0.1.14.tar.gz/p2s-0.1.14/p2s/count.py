
import numpy as np
from .flat import data

print(f"{np.count_nonzero(np.isnan(data) == False)}")


# for the entrypoint
def main():
    pass