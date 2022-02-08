import ast
import os
import pathlib
import re
from typing import List

import networkx as nx
import networkx_query

MEMORY_UNITS = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4, "P": 1024 ** 5, "E": 1024 ** 6}


def normalize_cpu(value: str) -> float:
    try:
        x = float(value)
    except ValueError:
        x = int(re.sub(r"milli|m", "", value))
        x = x / 1000
    return float("{:.2f}".format(x))


def normalize_memory_to_bytes(value: str) -> float:
    unit = re.sub("[0-9]", "", value)
    mul = MEMORY_UNITS.get(unit[0], 1)

    v = float(re.sub("[^0-9]", "", value))
    _bytes = v * mul
    return _bytes


def get_query(query_name: str) -> dict:
    """Loads a query by name from Caboto's library"""
    basedir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(basedir, "queries", f"{query_name}.cq")) as f:
        data = f.read()
        query = ast.literal_eval(data)
    return query


def replace_query(query, placeholder, value):
    if isinstance(query, dict):
        return {k: replace_query(v, placeholder, value) for k, v in query.items()}
    elif isinstance(query, list):
        return [replace_query(i, placeholder, value) for i in query]
    else:
        return value if query == placeholder else query


def get_sub_graph(graph, subgraph, node):
    """Returns a subgraph with the source node and all adjacent edges and nodes"""
    subgraph.add_node(node)
    for in_edge in graph.in_edges(node, data=True):
        subgraph.add_node(in_edge[0], **graph.nodes[in_edge[0]])
        subgraph.add_edge(in_edge[0], in_edge[1], data=in_edge[2])
    for out_edge in graph.out_edges(node, data=True):
        subgraph.add_node(out_edge[1], **graph.nodes[out_edge[1]])
        subgraph.add_edge(out_edge[0], out_edge[1], data=out_edge[2])
    return subgraph


def run_query(graph, query_args) -> List:
    source_graph = graph
    subgraph = nx.DiGraph()
    if "source" in query_args and query_args["source"].get("subquery"):
        source_result = run_query(graph, query_args["source"]["subquery"])
        if type(source_result) != list:
            raise ValueError("A subquery must return a list of graph nodes, please use the 'flatten' keyword")
        for rnode in source_result:
            subgraph = get_sub_graph(graph, subgraph, rnode)
        source_graph = subgraph
        query_args.pop("source")

    if "target" in query_args and query_args["target"].get("subquery"):
        target_result = run_query(graph, query_args["target"]["subquery"])
        if type(target_result) != list:
            raise ValueError("A subquery must return a list of graph nodes, please use the 'flatten' keyword")
        for rnode in target_result:
            subgraph = get_sub_graph(graph, subgraph, rnode)
        source_graph = subgraph
        query_args.pop("target")

    func = query_args.pop("func")
    flatten = query_args.pop("flatten", None)
    _func = getattr(networkx_query, func)
    query_args.update({"graph": source_graph})
    result = _func(**query_args)
    if type(flatten) == int:
        result = [_i[flatten] for _i in result]
    else:
        result = list(result)
    return result
