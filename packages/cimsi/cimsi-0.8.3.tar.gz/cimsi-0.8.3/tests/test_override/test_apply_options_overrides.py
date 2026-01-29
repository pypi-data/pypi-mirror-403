import yaml
from unittest.mock import patch

import pytest

from imsi.user_interface.ui_utils import apply_options_overrides   # adjust your import


def create_option_file(tmp_path, parent_dir, file_name, content):
    """Create an option YAML file under the correct directory structure."""
    folder = tmp_path / "src" / "imsi-config" / parent_dir
    folder.mkdir(parents=True, exist_ok=True)
    filepath = folder / f"{file_name}.yaml"
    with open(filepath, "w") as f:
        yaml.safe_dump(content, f)
    return filepath


@pytest.fixture
def base_config(tmp_path):
    """A base config dict with a valid setup_params.work_dir path."""
    return {
        "model": {"name": "original"},
        "setup_params": {"work_dir": tmp_path},
    }


def test_apply_single_option(base_config):
    """Applying one override should update the dict."""
    override_content = {"model": {"name": "updated"}}
    create_option_file(
        base_config["setup_params"]["work_dir"],
        parent_dir="p1",
        file_name="opt1",
        content=override_content,
    )

    defaults = [{"p1": "opt1"}]

    # simple update: merge dicts shallowly
    def fake_update(orig, new):
        orig.update(new)
        return orig

    with patch("imsi.user_interface.ui_utils.update", side_effect=fake_update) as mock_update:
        result = apply_options_overrides(base_config, defaults)

    assert result["model"]["name"] == "updated"
    mock_update.assert_called_once()


def test_apply_multiple_options(base_config):
    override1 = {"model": {"name": "first"}}
    override2 = {"foo": "bar"}

    create_option_file(base_config["setup_params"]["work_dir"], "p1", "o1", override1)
    create_option_file(base_config["setup_params"]["work_dir"], "p2", "o2", override2)

    defaults = [{"p1": "o1"}, {"p2": "o2"}]

    # merge dictionaries
    def fake_update(orig, new):
        orig.update(new)
        return orig

    with patch("imsi.user_interface.ui_utils.update", side_effect=fake_update) as mock_update:
        result = apply_options_overrides(base_config, defaults)

    assert result["model"]["name"] == "first"
    assert result["foo"] == "bar"
    assert mock_update.call_count == 2


def test_no_defaults_returns_same_dict(base_config):
    result = apply_options_overrides(base_config, [])
    assert result is base_config  # same dict returned (function mutates)
    assert result["model"]["name"] == "original"


def test_missing_option_file_raises(base_config):
    defaults = [{"nope": "missing"}]

    with pytest.raises(FileNotFoundError):
        apply_options_overrides(base_config, defaults)



def test_apply_does_not_support_nested_dict_items(base_config):
    """Document that nested keys are not supported."""
    override = {"a": 1}
    create_option_file(base_config["setup_params"]["work_dir"], "p", "o", override)

    defaults = [{"p": "o", "nested": "ignored"}]
    with patch("imsi.user_interface.ui_utils.update", return_value=base_config.copy()) as mock_update:
        # Only first key (p) should be used
        apply_options_overrides(base_config, defaults)
        mock_update.assert_called_once()
