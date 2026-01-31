import sys
import numpy as np
if sys.stdin.isatty():
    print("No input provided. Please pipe data into this script.", file=sys.stderr)
    sys.exit(1)
data = np.array([float(x.strip().strip(",") or "nan") for x in sys.stdin])