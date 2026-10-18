"""The strict, text-only YAML layer keeps every value as exact text (WS-08, research
Pitfall 10)."""

import pytest
import yaml
from epb import yamlio

# YAML 1.1 coercion boundaries: each would load as a number, boolean, null, date or float
# through a default loader.
BOUNDARY_VALUES = [
    "12:30",
    "12:30:00",
    "0123",
    "no",
    "yes",
    "on",
    "off",
    "~",
    "null",
    "2017",
    "2020-09-17",
    "1e3",
    ".inf",
    "0x1F",
    "true",
]


def test_corpus_has_all_fifteen_boundary_values():
    assert len(set(BOUNDARY_VALUES)) == 15


@pytest.mark.parametrize("value", BOUNDARY_VALUES)
def test_boundary_value_round_trips_as_text(value):
    dumped = yamlio.dump_yaml({"value": value, "items": [value]})
    loaded = yamlio.load_text_yaml(dumped, source="test.yaml")
    assert loaded == {"value": value, "items": [value]}


@pytest.mark.parametrize("value", BOUNDARY_VALUES)
def test_plain_boundary_value_loads_as_text(value):
    loaded = yamlio.load_text_yaml(f"value: {value}\n", source="test.yaml")
    assert loaded == {"value": value}
    assert type(loaded["value"]) is str


def test_safe_loader_itself_is_untouched():
    assert yaml.safe_load("value: 0123\n") == {"value": 83}
    assert yaml.SafeLoader.yaml_implicit_resolvers


def test_empty_plain_value_is_an_empty_string():
    assert yamlio.load_text_yaml("value:\n", source="test.yaml") == {"value": ""}


def test_duplicate_keys_are_rejected():
    with pytest.raises(yamlio.YamlTextError, match="duplicate key 'title'"):
        yamlio.load_text_yaml("title: a\ntitle: b\n", source="case.yaml")


def test_duplicate_keys_in_a_nested_mapping_are_rejected():
    with pytest.raises(yamlio.YamlTextError, match="duplicate key"):
        yamlio.load_text_yaml("outer:\n  a: '1'\n  a: '2'\n", source="case.yaml")


@pytest.mark.parametrize(
    "text",
    [
        "value: !!int 5\n",
        "value: !!float 1.5\n",
        "value: !!bool yes\n",
        "value: !!null ''\n",
        "value: !!timestamp 2020-09-17\n",
        "value: !!binary aGVsbG8=\n",
        "items:\n  - a\n  - !!int 7\n",
        "? !!int 1\n: a\n",
    ],
)
def test_explicit_tags_that_give_non_text_are_rejected(text):
    with pytest.raises(yamlio.YamlTextError):
        yamlio.load_text_yaml(text, source="case.yaml")


def test_explicit_str_tag_is_text():
    assert yamlio.load_text_yaml("value: !!str 5\n", source="x") == {"value": "5"}


def test_python_object_tag_is_rejected():
    with pytest.raises(yamlio.YamlTextError):
        yamlio.load_text_yaml("value: !!python/object/apply:os.getcwd []\n", source="x")


@pytest.mark.parametrize("text", ["", "# only a comment\n", "   \n"])
def test_empty_documents_are_rejected(text):
    with pytest.raises(yamlio.YamlTextError):
        yamlio.load_text_yaml(text, source="case.yaml")


def test_malformed_yaml_names_the_source():
    with pytest.raises(yamlio.YamlTextError, match="case.yaml"):
        yamlio.load_text_yaml("title: [unclosed\n", source="case.yaml")


def test_assert_text_only_accepts_nested_text():
    yamlio.assert_text_only({"a": ["b", {"c": "d"}], "e": ""})


@pytest.mark.parametrize("value", [None, 1, 1.5, True, b"x", {1: "a"}, ["a", 2]])
def test_assert_text_only_rejects_non_text(value):
    with pytest.raises(yamlio.YamlTextError):
        yamlio.assert_text_only({"value": value})


def test_dump_keeps_non_ascii_literally_and_keeps_key_order():
    data = {"title": "Ölpumpe – Störfall 2026", "a": "1"}
    text = yamlio.dump_yaml(data)
    assert "Ölpumpe – Störfall 2026" in text
    assert text.index("title") < text.index("a:")
    assert yamlio.dump_yaml_bytes(data) == text.encode("utf-8")
    assert yamlio.load_text_yaml(text, source="x") == data


def test_dump_is_deterministic():
    data = {"b": "2", "a": ["x", "y"], "c": []}
    assert yamlio.dump_yaml(data) == yamlio.dump_yaml(dict(data))
    assert yamlio.dump_yaml(data) == "b: '2'\na:\n- x\n- y\nc: []\n"
