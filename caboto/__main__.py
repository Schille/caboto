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
parser.add_argument("--plot", "-p", help="Plot the graph using matplotlib.", action="store_true")
parser.add_argument("--exclude", "-e", help="Exclude this entities from plotting")
parser.add_argument("--run", "-r", help="Run a function from the Caboto API module.")
parser.add_argument(
    "--args",
    "-a",
    help="Set function arguments comma separated in key-value style (e.g. key:value,key1:value)"
    " and only together with --run/-r",
)


if __name__ == "__main__":
    args = parser.parse_args()
    api.create_graph_from_path(args.manifests)
    api.discover_relations()
    print(f"Imported: {api.CABOTO_GRAPH.number_of_nodes()} nodes")
    print(f"Created: {api.CABOTO_GRAPH.number_of_edges()} edges")
    if args.run:
        func = getattr(api, args.run)
        if args.args:
            _args = {item.split(":")[0]: item.split(":", 1)[1] for item in str(args.args).split(",")}
            pprint(func(**_args))
        else:
            pprint(func())

    if args.plot:
        if args.exclude:
            excluded = args.exclude.split(",")
        else:
            excluded = []
        api.plot_graph(excluded)
