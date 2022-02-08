from pathlib import Path
from typing import List

import yaml
from drawing import draw_graph
from graph import CabotoGraph, K8sData, get_caboto_graph
from utils import MEMORY_UNITS, get_query, normalize_cpu, normalize_memory_to_bytes, replace_query, run_query

# the global Caboto graph structure which holds all Kubernetes entities and relations
CABOTO_GRAPH: CabotoGraph


# decorate api functions with this primer to make sure Caboto graph is loaded
def caboto_graph_required(func):
    def wrapper(*args, **kwargs):
        if CABOTO_GRAPH is None:
            raise ValueError("Caboto graph not yet loaded. Please run load_path(...) first.")
        return func(*args, **kwargs)

    return wrapper


def add_to_caboto(manifests: List[K8sData]) -> None:
    global CABOTO_GRAPH
    if "CABOTO_GRAPH" in globals():
        CABOTO_GRAPH.create_entities(manifests)
    else:
        CABOTO_GRAPH = get_caboto_graph(manifests)


#
# Functions to create and manage the Caboto graph
#
def create_graph_from_dict(doc: dict) -> None:
    manifest = K8sData(**doc)
    add_to_caboto([manifest])


def create_graph_from_string(val: str) -> None:
    """Loads Kubernetes manifest from yaml formatted string input and constructs a Caboto graph. Extend the graph
    running this function multiple times."""
    try:
        file = yaml.safe_load_all(val)
    except yaml.YAMLError as exc:
        print(exc)
        raise exc
    else:
        for doc in file:
            create_graph_from_dict(doc)


def create_graph_from_path(path: Path) -> None:
    """Loads recursively all Kubernetes manifests with a yaml file extension in the given directory and constructs a
    Caboto graph data structure."""
    for p in path.rglob("*.yaml"):
        with open(p.absolute(), "r") as stream:
            try:
                file = yaml.safe_load_all(stream)
            except yaml.YAMLError as exc:
                print(exc)
                raise exc
            else:
                for doc in file:
                    create_graph_from_dict(doc)


@caboto_graph_required
def discover_relations(excluded_relations: List = []) -> None:
    """Discovers all relations between Kubernetes objects and integrates them into the Caboto graph."""
    CABOTO_GRAPH.discover_relations(exclude_relations=excluded_relations)


@caboto_graph_required
def plot_graph(excluded_types: List = []) -> None:
    """Plot the Caboto graph with predefined settings using matplotlib."""
    draw_graph(CABOTO_GRAPH, excluded_types)


#
# Functions to investigate the Caboto graph
#


def _filter_nodes_(_type: str):
    return [(node, data) for node, data in CABOTO_GRAPH.nodes(data=True) if data["type"] == _type]


@caboto_graph_required
def list_applications(flat: bool = False) -> List:
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
def list_containerimages(flat: bool = False) -> List:
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
def list_services(flat: bool = False) -> List:
    """List all service names and their serving Pod nodes"""
    nodes = _filter_nodes_("Service")
    if flat:
        services = [data["data"].name for node, data in nodes]
    else:
        services = []
        for pnode, data in dict(nodes).items():
            services.append(
                (
                    pnode,
                    [edge[1] for edge in CABOTO_GRAPH.out_edges(pnode) if CABOTO_GRAPH.nodes[edge[1]]["type"] == "Pod"],
                )
            )
    return services


@caboto_graph_required
def get_service_pods(service: str = None) -> List:
    """List all serving Pod for a service"""
    if service:
        try:
            CABOTO_GRAPH.nodes[service]
        except KeyError:
            return None
        pods = [edge[1] for edge in CABOTO_GRAPH.out_edges(service) if CABOTO_GRAPH.nodes[edge[1]]["type"] == "Pod"]
        return pods


@caboto_graph_required
def list_configmaps(flat: bool = False) -> List:
    """List all configmaps and their keys"""
    nodes = _filter_nodes_("ConfigMap")
    if flat:
        cm = [node[0] for node in nodes]
    else:
        cm = [(node[0], list(node[1]["data"].specs.data.keys())) for node in nodes if node[1]["data"].specs.data]
    return cm


@caboto_graph_required
def list_secrets(flat: bool = False) -> List:
    """List all secrets and their keys"""
    nodes = _filter_nodes_("Secret")
    if flat:
        secrets = [node[0] for node in nodes]
    else:
        secrets = [(node[0], list(node[1]["data"].specs.data.keys())) for node in nodes if node[1]["data"].specs.data]
    return secrets


@caboto_graph_required
def list_ingress(flat: bool = False) -> List:
    """List all ingress and their serving services and pods"""
    nodes = _filter_nodes_("Ingress")
    if flat:
        ingresss = [node[0] for node in nodes]
    else:
        ingresss = []
        for inode, data in dict(nodes).items():
            ingresss.append(
                (
                    inode,
                    [
                        (edge[0], get_service_pods(edge[0]))
                        for edge in CABOTO_GRAPH.in_edges(inode)
                        if CABOTO_GRAPH.nodes[edge[0]]["type"] == "Service"
                    ],
                )
            )
    return ingresss


@caboto_graph_required
def list_hosts(flat: bool = False) -> List:
    """List all hosts and the ingress serving them"""
    nodes = _filter_nodes_("Ingress")

    if flat:
        hosts = set()
        for inode, _ in dict(nodes).items():
            hosts = hosts.union(
                set(
                    [edge[1] for edge in CABOTO_GRAPH.out_edges(inode) if CABOTO_GRAPH.nodes[edge[1]]["type"] == "Host"]
                )
            )
    else:
        hosts = []
        for inode, data in dict(nodes).items():
            hosts.append(
                (
                    [
                        edge[1]
                        for edge in CABOTO_GRAPH.out_edges(inode)
                        if CABOTO_GRAPH.nodes[edge[1]]["type"] == "Host"
                    ],
                    inode,
                )
            )
    return list(hosts)


@caboto_graph_required
def sum_cpu_requests(default: str = "250m") -> str:
    """Returns the fractional amount of CPUs (normalized to 2 decimal places) requested across all Pods"""
    pods = exec_query("AllPods")
    cpu_requests = []
    for pod in pods:
        pnode = CABOTO_GRAPH.nodes[pod]
        if data := pnode.get("data"):
            for container in data.specs.spec.containers:
                try:
                    requests = container["resources"]["requests"]["cpu"]
                    cpu_requests.append(normalize_cpu(requests))
                except (KeyError, TypeError):
                    cpu_requests.append(normalize_cpu(default))
    return float(f"{sum(cpu_requests):.2f}")


@caboto_graph_required
def sum_memory_requests(default: str = "128M", unit: str = "M") -> str:
    """Returns the amount of memory requested across all Pods. Defaults to MB as unit."""
    pods = exec_query("AllPods")
    memory_requests = []
    for pod in pods:
        pnode = CABOTO_GRAPH.nodes[pod]
        if data := pnode.get("data"):
            for container in data.specs.spec.containers:
                try:
                    requests = container["resources"]["requests"]["memory"]
                    memory_requests.append(normalize_memory_to_bytes(requests))
                except (KeyError, TypeError):
                    memory_requests.append(normalize_memory_to_bytes(default))
    return f"{sum(memory_requests) / MEMORY_UNITS.get(unit):.2f}{unit}"


def exec_query(query_name: str, **kwargs) -> list:
    q = get_query(query_name)
    _qparams = q.get("params")

    if _args := q.get("args"):
        if set(_args) == set(kwargs.keys()):
            for k, v in kwargs.items():
                _qparams = replace_query(_qparams, f"<{k}>", v)
        else:
            raise ValueError(f"The following arguments are missing: {list(set(_args) - set(kwargs.keys()))}")

    result = run_query(CABOTO_GRAPH, _qparams)
    return result
