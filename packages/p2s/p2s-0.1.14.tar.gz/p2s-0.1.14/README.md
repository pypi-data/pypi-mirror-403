
```
pip install p2s
```

# General Stats
```
seq 0 100 | p2s
```

# Count
```
seq 0 100 | p2s.count
```

# Mean
```
seq 0 100 | p2s.mean
```

# Standard Deviation
```
seq 0 100 | p2s.std
```

# Quantile (in Percent)
```
seq 0 100 | p2s.q 25
```

# Map (lambda expression)
Each line is in `x`
```
seq 0 100 | p2s.map "int(x) + 1"
```

# Reduce
Accumulator `a` and current `c`. Usage `p2s.reduce <lambda> <initial_accumulator>`
seq 0 100 | p2s.reduce "float(a) + float(c)" "0"

# Histogram
seq 0 100 | p2s.hist --xlabel "Position" --output "hist.pdf"