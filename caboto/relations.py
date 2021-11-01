from entities import Application, ContainerImage, Label, Namespace


def set_namespace(graph):
    for node, data in list(graph.nodes.items()):
        if hasattr(data["data"], "specs"):
            if data["data"].specs.metadata.namespace:
                nsnode = Namespace(name=data["data"].specs.metadata.namespace).add_as_node(graph)
                graph.add_edge(node, nsnode, label="in")


def set_labels(graph):
    for node, data in list(graph.nodes.items()):
        if hasattr(data["data"], "labels"):
            for label in data["data"].labels:
                lnode = Label(label[0], label[1]).add_as_node(graph)
                graph.add_edge(lnode, node, label="labels")


def set_annotations(graph):
    for node, data in list(graph.nodes.items()):
        if hasattr(data["data"], "annotations"):
            for label in data["data"].annotations:
                anode = Label(label[0], label[1]).add_as_node(graph)
                graph.add_edge(anode, node, label="annotates")


def set_selectors(graph):
    for node, data in list(graph.nodes.items()):
        if hasattr(data["data"], "specs"):
            specs = data["data"].specs.spec
            if specs and specs.selector:
                keys = list(data["data"].specs.spec.selector.keys())
                if keys[0] == "matchLabels":
                    selectors = data["data"].specs.spec.selector["matchLabels"]
                else:
                    selectors = data["data"].specs.spec.selector
                if selectors:
                    matched_label_nodes = []
                    for lnode, ldata in list(graph.nodes.items()):
                        if ldata["type"] != "Label":
                            continue
                        else:
                            if ldata["data"].key in selectors.keys():
                                if selectors[ldata["data"].key] == ldata["data"].value:
                                    matched_label_nodes.append(lnode)
                    matched_pod_nodes = None
                    if matched_label_nodes:
                        for mlnode in matched_label_nodes:
                            if matched_pod_nodes is not None:
                                matched_pod_nodes = set.intersection(
                                    matched_pod_nodes,
                                    (pod[1] for pod in graph.out_edges(mlnode) if graph.nodes[pod[1]]["type"] == "Pod"),
                                )
                            else:
                                matched_pod_nodes = set(
                                    pod[1] for pod in graph.out_edges(mlnode) if graph.nodes[pod[1]]["type"] == "Pod"
                                )
                    if matched_pod_nodes:
                        for matched_pod_node in matched_pod_nodes:
                            graph.add_edge(node, matched_pod_node, label="selects")


def set_applications(graph):
    # we get 'application' data from Kubernetes labels
    for node, data in list(graph.nodes.items()):
        if data["type"] != "Label":
            continue
        if data["data"].key == "app.kubernetes.io/name":
            anode = Application(data["data"].value).add_as_node(graph)
            for pnode in graph.out_edges(node):
                graph.add_edge(anode, pnode[1], label="contains")


def set_containerimages(graph):
    for node, data in list(graph.nodes(data=True)):
        if data["type"] != "Pod":
            continue
        containers = data["data"].specs.spec.containers
        if containers:
            for container in containers:
                image = container.get("image")
                if image:
                    cinode = ContainerImage(image).add_as_node(graph)
                    graph.add_edge(node, cinode, label="runs")


RELATIONS = {
    "namespace": set_namespace,
    "labels": set_labels,
    "annotations": set_annotations,
    "selectors": set_selectors,
    "applications": set_applications,
    "containerimages": set_containerimages,
}
