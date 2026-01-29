import pytest
from pydantic import ValidationError

from imsi.user_interface.ui_manager import Override, parse_override_options


def test_override_single_valid():
    o = Override(options="group/option")
    assert o.model_dump() == {"options": "group/option"}


def test_parse_override_options_multiple():
    inputs = ["a/b", "x/y"]
    out = parse_override_options(inputs)
    assert out == [{"options": "a/b"}, {"options": "x/y"}]


def test_override_invalid_missing_slash():
    with pytest.raises(ValidationError):
        Override(options="nonsense")


def test_parse_override_options_invalid():
    inputs = ["valid/x", "invalid"]  # second is bad
    with pytest.raises(ValidationError):
        parse_override_options(inputs)


def test_override_empty_string():
    with pytest.raises(ValidationError):
        Override(options="")


def test_override_whitespace_only():
    with pytest.raises(ValidationError):
        Override(options="   ")


@pytest.mark.parametrize("bad_input", [123, None, ["a/b"], {"a": "b"}])
def test_override_non_string(bad_input):
    with pytest.raises(ValidationError):
        Override(options=bad_input)


def test_parse_override_options_output_type():
    out = parse_override_options(["g/o"])
    assert isinstance(out, list)
    assert isinstance(out[0], dict)
    assert out[0] == {"options": "g/o"}


def test_override_error_message():
    with pytest.raises(ValidationError) as excinfo:
        Override(options="badformat")

    assert "Option must be in the format <group>/<option>" in str(excinfo.value)
