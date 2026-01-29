import os

import yaml


def _bool(value: str) -> bool:
    return value.lower() in ("true", "t", "1", "on", "enabled", "yes", "y")


def _get_env_value(loader: yaml.Loader, name: str, *, default=None):
    value = os.environ.get(name, None)
    if value is None:
        return default
    if value == "":
        return value
    tag = loader.resolve(yaml.nodes.ScalarNode, value, (True, False))
    return loader.construct_object(yaml.nodes.ScalarNode(tag, value))


def _env_tag(loader: yaml.Loader, node: yaml.Node):
    if isinstance(node, yaml.nodes.ScalarNode):
        return _get_env_value(loader, loader.construct_scalar(node))

    if isinstance(node, yaml.nodes.MappingNode):
        mapping = loader.construct_mapping(node)
        try:
            _name = mapping["name"]
        except KeyError:
            raise yaml.constructor.ConstructorError(
                None,
                None,
                f'Missing "name" key in {node.id}',
                node.start_mark,
            )
        _default = mapping.get("default", None)
        return _get_env_value(loader, _name, default=_default)

    raise yaml.constructor.ConstructorError(
        None,
        None,
        f"Expected a scalar or mapping node, but found {node.id}.",
        node.start_mark,
    )


def get_yaml_loader():
    class Loader(yaml.SafeLoader):
        pass

    Loader.add_constructor("!env", _env_tag)
    return Loader
