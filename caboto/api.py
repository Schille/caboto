from pathlib import Path
from typing import List

import yaml
from drawing import draw_graph
from graph import CabotoGraph, K8sData, get_caboto_graph

# the global Caboto graph structure which holds all Kubernetes entities and relations
CABOTO_GRAPH: CabotoGraph = None


# decorate api functions with this primer to make sure Caboto graph is loaded
def caboto_graph_required(func):
    def wrapper(*args, **kwargs):
        if CABOTO_GRAPH is None:
            raise ValueError("Caboto graph not yet loaded. Please run load_path(...) first.")
        return func(*args, **kwargs)

    return wrapper


#
# Functions to create and manage the Caboto graph
#


def create_graph_from_path(path: Path) -> None:
    """Loads recursively all Kubernetes manifests with a yaml file extension in the given directory and constructs a
    Caboto graph data structure."""
    manifests = []
    for p in path.rglob("*.yaml"):
        with open(p.absolute(), "r") as stream:
            try:
                file = yaml.safe_load_all(stream)
            except yaml.YAMLError as exc:
                print(exc)
            for doc in file:
                manifests.append(K8sData(**doc))
    if len(manifests) == 0:
        raise ValueError(f"Could not load a yaml file in {path.absolute()}")
    global CABOTO_GRAPH
    CABOTO_GRAPH = get_caboto_graph(manifests)


@caboto_graph_required
def discover_relations(excluded_relations: List[str] = []) -> None:
    """Discovers all relations between Kubernetes objects and integrates them into the Caboto graph."""
    CABOTO_GRAPH.discover_relations(exclude_relations=excluded_relations)


@caboto_graph_required
def plot_graph(excluded_types: List[str] = []) -> None:
    """Plot the Caboto graph with predefined settings using matplotlib."""
    draw_graph(CABOTO_GRAPH, excluded_types)


#
# Functions to investigate the Caboto graph
#


def _filter_nodes_(_type: str):
    return [(node, data) for node, data in CABOTO_GRAPH.nodes(data=True) if data["type"] == _type]


@caboto_graph_required
def list_applications(flat: bool = False) -> List[str]:
    """List all applications and all related Kubernetes objects"""

    nodes = _filter_nodes_("Application")
    if flat:
        applications = [data["data"].key for node, data in nodes]
    else:
        applications = []
        for appnode, data in dict(nodes).items():
            applications.append((data["data"].key, [edge[1] for edge in CABOTO_GRAPH.out_edges(appnode)]))
    return applications


@caboto_graph_required
def list_containerimages(flat: bool = False) -> List[str]:
    """List all container images and the Pods running them"""

    nodes = _filter_nodes_("ContainerImage")
    if flat:
        images = [data["data"].key for node, data in nodes]
    else:
        images = []
        for imgnodes, data in dict(nodes).items():
            images.append((data["data"].key, [edge[0] for edge in CABOTO_GRAPH.in_edges(imgnodes)]))
    return images


@caboto_graph_required
def list_services(flat: bool = False) -> List[str]:
    """List all service names and their serving Pod nodes"""
    nodes = _filter_nodes_("Service")
    if flat:
        services = [data["data"].name for node, data in nodes]
    else:
        services = []
        for pnode, data in dict(nodes).items():
            services.append(
                (
                    data["data"].name,
                    [edge[1] for edge in CABOTO_GRAPH.out_edges(pnode) if CABOTO_GRAPH.nodes[edge[1]]["type"] == "Pod"],
                )
            )
    return services
