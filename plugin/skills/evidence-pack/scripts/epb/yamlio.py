"""Strict, text-only YAML reading and deterministic YAML writing (WS-08).

YAML 1.1 turns many plain values into other types: ``12:30`` becomes a number of seconds,
``0123`` an octal number, ``no`` a boolean and ``2020-09-17`` a date. Case settings must keep
exactly the text the user gave, so ``TextLoader`` has no implicit resolvers at all: every
plain scalar is a string. Explicit tags such as ``!!int 5`` still produce other types
(research Pitfall 10), so ``load_text_yaml`` walks the result and rejects anything that is not
a string, a list or a mapping. Duplicate keys are rejected as well.

``dump_yaml`` writes with ``yaml.safe_dump``, which quotes every string that would otherwise
be read back as another type, so a dump and load round trip keeps every value as exact text.
"""

import yaml


class YamlTextError(ValueError):
    """The YAML text is malformed, has duplicate keys or holds a value that is not text."""


class TextLoader(yaml.SafeLoader):
    """A ``SafeLoader`` that resolves every plain scalar to a string and refuses duplicate
    or non-text mapping keys."""


# A class-level copy: SafeLoader itself keeps its resolvers.
TextLoader.yaml_implicit_resolvers = {}


def _mapping_without_duplicates(loader, node, deep=False):
    if not isinstance(node, yaml.MappingNode):
        raise yaml.constructor.ConstructorError(
            None, None, f"expected a mapping, found {node.id}", node.start_mark
        )
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(
                None, None, "mapping keys must be text", key_node.start_mark
            )
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


TextLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping_without_duplicates
)


def _describe(value) -> str:
    if value is None:
        return "an empty value (null)"
    return f"a value of type {type(value).__name__}"


def assert_text_only(data, *, where: str = "/") -> None:
    """Raise ``YamlTextError`` unless ``data`` holds only strings, lists and mappings with
    text keys."""
    if isinstance(data, str):
        return
    if isinstance(data, list):
        for index, item in enumerate(data):
            assert_text_only(item, where=f"{where.rstrip('/')}/{index}")
        return
    if isinstance(data, dict):
        for key, item in data.items():
            if not isinstance(key, str):
                raise YamlTextError(f"{where} has a key that is not text")
            assert_text_only(item, where=f"{where.rstrip('/')}/{key}")
        return
    raise YamlTextError(f"{where} holds {_describe(data)}, not text")


def load_text_yaml(text: str, *, source: str):
    """Parse ``text`` with ``TextLoader`` and check that it holds only text.

    ``source`` names the file in error messages. Raises ``YamlTextError`` for malformed
    YAML, duplicate keys, explicit tags that give non-text values and an empty document.
    """
    try:
        data = yaml.load(text, Loader=TextLoader)  # noqa: S506 - custom safe loader
    except yaml.YAMLError as exc:
        raise YamlTextError(f"{source} is not valid YAML: {exc}") from None
    try:
        assert_text_only(data)
    except YamlTextError as exc:
        raise YamlTextError(f"{source}: {exc}") from None
    return data


def dump_yaml(data) -> str:
    """Deterministic YAML text: keys in insertion order, block style, non-ASCII kept."""
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)


def dump_yaml_bytes(data) -> bytes:
    """``dump_yaml`` encoded as UTF-8."""
    return dump_yaml(data).encode("utf-8")
