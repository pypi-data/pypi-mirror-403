import sys, os
import numpy as np
import re
if sys.stdin.isatty():
    print("No input provided. Please pipe data into this script.", file=sys.stderr)
    sys.exit(1)

if not "XY" in os.environ:
    print("XY not set", file=sys.stderr)

data = []
shortest_line_length = -1
for line in sys.stdin:
    parts = re.split(r'[^0-9.eE+\-]+', line)
    line_data = [float(x.strip().strip(",") or "nan") for x in parts if len(x) > 0]
    data.append(line_data)
    if shortest_line_length == -1:
        shortest_line_length = len(line_data)
    if shortest_line_length > len(line_data):
        shortest_line_length = len(line_data)
        print(f"Lines do not contain the same number of values. Truncating to {shortest_line_length} values", file=sys.stderr)

data = np.array([x[:shortest_line_length] for x in data])