from io import StringIO
import os

import yaml

from filerohr.utils import HttpUrlBuilder, get_yaml_loader, normalize_str, omit_falsy


def test_http_url_builder_accepts_path_components():
    base_url = HttpUrlBuilder("https://example.com?test=1")
    assert str(base_url / "foo" / "bar") == "https://example.com/foo/bar?test=1"


def test_http_url_builder_appends_trailing_slashes():
    url = HttpUrlBuilder("https://example.com/test?test=1", use_trailing_slash=True)
    assert str(url) == "https://example.com/test/?test=1"


def test_http_url_builder_generates_proper_origin():
    assert HttpUrlBuilder("https://example.com/test?test=1").origin == "https://example.com"
    assert HttpUrlBuilder("http://example.com/test?test=1").origin == "http://example.com"
    assert HttpUrlBuilder("https://example.com:81/test?test=1").origin == "https://example.com:81"


def test_omit_falsy():
    def _is_not_none(value) -> bool:
        return value is not None

    assert list(omit_falsy([0, None, "", [], {}])) == []
    assert list(omit_falsy([1, "a", "b"])) == [1, "a", "b"]
    assert list(omit_falsy([0, None, ""], is_truthy=_is_not_none)) == [0, ""]


def test_normalize_str():
    # treats None as an empty string
    assert normalize_str(None) == ""
    # casts to string
    assert normalize_str(0) == "0"
    # unescapes HTML entities
    assert normalize_str("&#8211;") == "–"
    # strips whitespace
    assert normalize_str(" Hi !  ") == "Hi !"


def test_yaml_loader():
    os.environ["TEST_INT"] = "5"
    os.environ["TEST_FLOAT"] = "5.5"
    os.environ["TEST_STR"] = "test"
    os.environ["TEST_BOOL"] = "true"
    os.environ["TEST_EMPTY"] = ""
    yaml_data = StringIO(
        """
        my_int: !env TEST_INT
        my_float: !env TEST_FLOAT
        my_str: !env TEST_STR
        my_bool: !env TEST_BOOL
        my_empty: !env TEST_EMPTY
        my_missing: !env TEST_MISSING
        my_default_match: !env { name: TEST_STR, default: "hello" }
        my_default_no_match: !env { name: TEST_MISSING, default: "hello" }
        my_default_no_match_type: !env { name: TEST_MISSING, default: 10 }
        """
    )
    data = yaml.load(yaml_data, Loader=get_yaml_loader())
    expected_data = {
        "my_int": 5,
        "my_float": 5.5,
        "my_str": "test",
        "my_bool": True,
        "my_empty": "",
        "my_missing": None,
        "my_default_match": "test",
        "my_default_no_match": "hello",
        "my_default_no_match_type": 10,
    }
    assert data == expected_data
