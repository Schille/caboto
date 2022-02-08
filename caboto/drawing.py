import matplotlib.pyplot as plt
import networkx as nx

WEIGHTS = {"pod": 450, "deployment": 200, "service": 220, "ingress": 120, "statefulset": 200, "namespace": 500}
DEFAULT_WEIGHT = 20

COLORS = {"pod": 1.223, "deployment": 0.571, "service": 0.33, "ingress": 0.942, "statefulset": 0.571}
DEFAULT_COLOR = 0.25


def draw_graph(graph, exclude_node_types=[]):
    req_nodes = [x for x, y in graph.nodes(data=True) if y.get("type") not in exclude_node_types]
    subgraph = graph.subgraph(req_nodes)
    node_weights = [WEIGHTS.get(data.get("type").lower(), DEFAULT_WEIGHT) for node, data in subgraph.nodes.items()]
    node_colors = [COLORS.get(data.get("type").lower(), DEFAULT_COLOR) for node, data in subgraph.nodes.items()]
    node_labels = {node: node for node, data in subgraph.nodes.items()}
    pos = nx.random_layout(subgraph)
    nx.draw_networkx_nodes(subgraph, pos, cmap=plt.get_cmap("jet"), node_size=node_weights, node_color=node_colors)
    nx.draw_networkx_labels(subgraph, pos, labels=node_labels)

    labels = {edge: data["label"] for edge, data in subgraph.edges.items()}
    nx.draw_networkx_edges(subgraph, pos)
    nx.draw_networkx_edge_labels(subgraph, pos, edge_labels=labels)

    plt.show()
