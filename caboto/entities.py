# global entities set in order to keep track of already created entities
resource_entities = set()
kv_entities = set()
key_entities = set()


class K8sGraphEntity(object):
    registry = None

    def _get_code(self):
        raise NotImplementedError()

    def add_as_node(self, graph) -> str:
        if self._get_code() not in self.registry:
            graph.add_node(self._get_code(), type=self.__class__.__name__, data=self)
            resource_entities.add(self._get_code())
        return self._get_code()


class K8sResource(K8sGraphEntity):
    registry = resource_entities

    def __init__(self, type, data):
        self._raw_data = data
        self.name = data.metadata.name
        self.namespace = data.metadata.namespace or "default"
        self.type = type
        self._api_version = data.apiVersion

    def _get_code(self):
        return f"{self.type}:{self.name}"

    def get_labels(self):
        if self._raw_data.metadata.labels:
            return list(self._raw_data.metadata.labels.items())
        else:
            return []

    labels = property(get_labels)

    def get_annotations(self):
        if self._raw_data.metadata.annotations:
            return list(self._raw_data.metadata.annotations.items())
        else:
            return []

    annotations = property(get_annotations)

    def get_specification(self):
        return self._raw_data

    specs = property(get_specification)

    def add_as_node(self, graph) -> str:
        if self.specs.spec and self.specs.spec.template:
            replicas = self.specs.spec.replicas or 1
            pod_sepcification = self.specs.spec.template
            for i in range(1, replicas + 1):
                pod_klass = EntityClassFactory("Pod", [])
                pod_sepcification.metadata.name = f"{self.name}-{i}"
                pod_klass("Pod", pod_sepcification).add_as_node(graph)
        return super(K8sResource, self).add_as_node(graph)


def EntityClassFactory(name, argnames, BaseClass=K8sResource):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key not in argnames:
                raise TypeError(f"Argument {key} not valid for {self.__class__.__name__}")
            setattr(self, key, value)

    newclass = type(name, (BaseClass,), {})

    def __sub_init__(self, type, data):
        super(newclass, self).__init__(type, data)

    setattr(newclass, "__init__", __sub_init__)
    return newclass


class KVEntity(K8sGraphEntity):
    registry = kv_entities

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def _get_code(self):
        return f"{self.__class__.__name__}:{self.key}:{self.value}"


class Label(KVEntity):
    pass


class Annotation(KVEntity):
    pass


class Namespace(K8sGraphEntity):
    registry = resource_entities

    def __init__(self, name):
        self.name = name

    def _get_code(self):
        return f"Namespace:{self.name}"


class KeyEntity(K8sGraphEntity):
    registry = key_entities

    def __init__(self, key):
        self.key = key

    def _get_code(self):
        return f"{self.__class__.__name__}:{self.key}"


class Application(KeyEntity):
    pass


class ContainerImage(KeyEntity):
    pass


class Host(KeyEntity):
    pass
