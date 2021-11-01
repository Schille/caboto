#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
from pprint import pprint

import api


def dir_path(_path):
    if os.path.isdir(_path):
        return Path(_path)
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{_path} is not a valid path")


parser = argparse.ArgumentParser(description="Caboto Kubernetes semantic analysis tool.")
parser.add_argument("--manifests", "-m", type=dir_path, default=".", help="Path to the manifests directory.")
parser.add_argument("--plot", "-p", action="store_true", help="Plot the graph using matplotlib.")
parser.add_argument("--run", "-r", help="Run a function from the Caboto API module.")


if __name__ == "__main__":
    args = parser.parse_args()
    api.create_graph_from_path(args.manifests)
    api.discover_relations()
    if args.run:
        func = getattr(api, args.run)
        pprint(func())
    if args.plot:
        api.plot_graph()
