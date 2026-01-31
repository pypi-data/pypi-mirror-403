import sys
import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import argparse


def main():
    parser = argparse.ArgumentParser(description="Plot correlation matrix from CSV data")
    parser.add_argument("--variates", type=str, help="Comma-separated list of variate names to include in the correlation matrix. The semantics are: All to variates correlation (N_VARIATES x N_ALL)", default=None)
    parser.add_argument("--variate-startswith", type=str, help="filter variates that start with this substring", default=None)
    args = parser.parse_args()

    if "DEBUG" in os.environ:
        input = open(os.environ["DEBUG"], 'r')
    else:
        input = sys.stdin
    reader = csv.reader(input)
    header = next(reader)
    rows = [row for row in reader]

    data = []
    for row in rows:
        output_row = []
        for x in row:
            if x == "" or x.lower() == "nan" or x.lower() == "null" or x.lower() == "undefined" or x.lower() == "none":
                x = None
            else:
                try:
                    x = float(x)
                except ValueError:
                    if x == "True":
                        x = 1
                    elif x == "False":
                        x = 0
                    else:
                        x = None
            output_row.append(x)
        data.append(output_row)

    data = np.array(data)

    varying = data.std(axis=0) > 1e-10
    header = np.array(header)[varying]
    data = data[:, varying]

    corr = np.corrcoef(data, rowvar=False)

    EPS = 1e-5
    indices = [i for i in range(corr.shape[1]) if (not np.all(np.isnan(corr[:, i]))) and (not np.all(np.abs(corr[:, i]) < EPS)) and (not args.variate_startswith or any([header[i].startswith(x) for x in args.variate_startswith.split(",")])) or (args.variates and header[i] in args.variates.split(","))]
    if len(indices) < corr.shape[1]:
        corr = corr[:, indices]
        corr = corr[indices, :]
        header = np.array([header[i] for i in indices])

    if args.variates:
        variates = [x.strip() for x in args.variates.split(",")]
        variate_indices = [header.tolist().index(variate) for variate in variates if variate in header]
        if not variate_indices:
            print("No valid variates found in the header. Exiting.")
            return
        corr = corr[variate_indices]
        corr = corr[:, [i for i in range(corr.shape[1]) if i not in variate_indices]]
    


    fig, ax = plt.subplots()
    cax = ax.matshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    fig.colorbar(cax)

    xticklabels = [x for i, x in enumerate(header) if not args.variates or (i not in variate_indices)]
    ax.set_xticks(range(len(xticklabels)))
    if args.variates:
        yticklabels = variates
    else:
        yticklabels = header
    ax.set_yticks(range(len(yticklabels)))
    ax.set_xticklabels(xticklabels, rotation=90)
    ax.set_yticklabels(yticklabels)

    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    main()