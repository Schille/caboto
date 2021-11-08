from typing import List

import networkx as nx
from entities import EntityClassFactory
from relations import RELATIONS


class K8sData(dict):
    def __init__(self, **entities):
        for entity, value in entities.items():
            if isinstance(value, dict):
                self.update({entity: K8sData(**value)})
            else:
                self.update({entity: value})

    def __getattr__(self, item):
        return self.get(item)


class CabotoGraph(nx.DiGraph):
    def __init__(self, manifests: List[K8sData] = None, *args, **kwargs):
        super(CabotoGraph, self).__init__(*args, **kwargs)
        if manifests:
            self.create_entities(manifests)

    def create_entities(self, manifests: List[K8sData]):
        for data in manifests:
            resource_kind = data.kind
            if data.kind is None:
                raise ValueError("This file does not contain a valid Kubernetes manifest.")
            AK8sResource = EntityClassFactory(resource_kind, [])
            AK8sResource(resource_kind, data).add_as_node(self)

    def discover_relations(self, exclude_relations=[]):
        for relation in list(filter(lambda x: x not in exclude_relations, RELATIONS.keys())):
            func = RELATIONS.get(relation)
            func(self)


def get_caboto_graph(manifests: List) -> CabotoGraph:
    """Create and returns a NetworkX DiGraph which contains all Kubernetes entities included"""
    cgraph = CabotoGraph(manifests)
    return cgraph
