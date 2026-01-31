import matplotlib.pyplot as plt
import argparse, os
import numpy as np

def main(method=plt.plot):
    parser = argparse.ArgumentParser(description="Example of an optional string argument")
    parser.add_argument("--title", type=str, help="Title", default="")
    parser.add_argument("--xlabel", type=str, help="Horizontal axis label", default="")
    parser.add_argument("--output", type=str, help="Output file", default="")
    parser.add_argument("--labels", type=str, help="Labels", default="")
    parser.add_argument("--bins", type=int, help="Number of bins", default=10)
    args = parser.parse_args()

    plt.figure()
    if "Y" in os.environ:
        y = int(os.environ["Y"].strip())
    else:
        y = None
    if "X" in os.environ:
        if os.environ["X"] == "":
            cols = None
        else:
            cols = [int(x.strip()) for x in os.environ["X"].split(",")]
    else:
        cols = None
    if args.labels == "":
        labels = None
    else:
        labels = [x.strip() for x in args.labels.split(",")]
    from .xy import data
    xs = cols if cols is not None else np.arange(data.shape[1])
    for i, col in enumerate(xs):
        plt.hist(data[:, col], label=labels[i] if (labels is not None) and i < len(labels) else None, bins=args.bins)
    if labels is not None:
        plt.legend(labels)
    if args.xlabel != "":
        plt.xlabel(args.xlabel)
    plt.ylabel("Count")
    if args.title != "":
        plt.title(args.title)
    if args.output == "":
        plt.show()
    else:
        plt.savefig(args.output)


if __name__ == "__main__":
    main()