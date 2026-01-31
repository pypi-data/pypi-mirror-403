import matplotlib.pyplot as plt
import argparse, os
import numpy as np

def main(method=plt.plot):
    parser = argparse.ArgumentParser(description="Example of an optional string argument")
    parser.add_argument("--title", type=str, help="Title", default="")
    parser.add_argument("--xlabel", type=str, help="Horizontal axis label", default="")
    parser.add_argument("--ylabel", type=str, help="Vertical axis label", default="")
    parser.add_argument("--output", type=str, help="Output file", default="")
    parser.add_argument("--labels", type=str, help="Labels", default="")
    args = parser.parse_args()

    plt.figure()
    if "X" in os.environ:
        x = int(os.environ["X"].strip())
    else:
        x = None
    if "Y" in os.environ:
        if os.environ["Y"] == "":
            cols = None
        else:
            cols = [int(x.strip()) for x in os.environ["Y"].split(",")]
    else:
        cols = None
    if "Z" in os.environ:
        if os.environ["Z"] == "":
            z = None
        else:
            z = int(os.environ["Z"].strip())
    else:
        z = None
    if args.labels == "":
        labels = None
    else:
        labels = [x.strip() for x in args.labels.split(",")]
    from .xy import data
    ys = cols if cols is not None else (np.arange(1, data.shape[1]) if data.shape[1] > 1 else [0])
    x = data[:, x] if x is not None else (data[:, 0] if data.shape[1] > 1 else np.arange(data.shape[0]))
    for i, col in enumerate(ys):
        method(x, data[:, col], label=labels[i] if (labels is not None) and i < len(labels) else None)
    if labels is not None:
        plt.legend(labels)
    if args.xlabel != "":
        plt.xlabel(args.xlabel)
    if args.ylabel != "":
        plt.ylabel(args.ylabel)
    if args.title != "":
        plt.title(args.title)
    if args.output == "":
        plt.show()
    else:
        plt.savefig(args.output)


if __name__ == "__main__":
    main()