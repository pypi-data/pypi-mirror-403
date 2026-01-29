import os
import shutil
from pathlib import Path
import warnings

import yaml

from imsi.utils.dict_tools import update
from imsi.config_manager.config_manager import Configuration, ConfigManager


def _get_config_filename(serialized=False) -> str:
    # determine the filename from cwd or WRK_DIR for the user-facing or
    # serialized config file

    def _get_basename(dirname, serialized):
        if serialized:
            stembase = f".imsi/.imsi_configuration_{dirname}.pickle"
        else:
            stembase = f"imsi_configuration_{dirname}.yaml"
        return stembase

    # First look in the PWD
    current_dir = './'   # potential work_dir, to check
    wrk_dir = current_dir  # TODO
    current_dir_resolved = Path(wrk_dir).resolve()
    current_dir_name = current_dir_resolved.name

    config_filename_base = _get_basename(current_dir_name, serialized)
    guessed = os.path.join(current_dir_resolved, config_filename_base)

    if not os.path.exists(guessed):
        # now assume that if the config file didnt match the name of the
        # cwd, then maybe WRK_DIR is set instead
        wrk_dir = os.getenv("WRK_DIR")

        cfg_type_msg = "serialized configuration" if serialized else "configuration"

        if wrk_dir:
            current_dir_name = Path(wrk_dir).name
            config_filename_base = _get_basename(current_dir_name, serialized)
            guessed = os.path.join(wrk_dir, config_filename_base)
            if os.path.exists(guessed):
                warnings.warn(f"\nNB: Using configuration defined by WRK_DIR at {guessed}\n")
            else:
                raise FileNotFoundError(
                    f"Cannot find the imsi {cfg_type_msg} file expected: "
                    f"{guessed}"
                    )
        else:
            raise FileNotFoundError(
                f"Cannot find the imsi {cfg_type_msg} file expected: {guessed} "
                "You must be in a valid imsi setup directory or WRK_DIR must be defined"
                )

    # by here, the guessed file is the confirmed imsi configuration file
    return guessed


def apply_options_overrides(config_dictionary: dict, options: list) -> dict:
    """Merge YAML option files into config_dictionary.

    Each item in options must be a single-key dict mapping a subdirectory name to
    a filename (without suffix). Example: [{"some_dir": "option_name"}, ...].

    If any loaded YAML defines keys whose full key-paths overlap with existing
    keys in config_dictionary, a warning is emitted listing the overlapping paths.
    """
    options_root = Path(config_dictionary["setup_params"]["work_dir"]) / "src" / "imsi-config"

    for option in options:
        parent_dir, filename = next(iter(option.items()))
        option_file = (options_root / parent_dir / filename).with_suffix(".yaml")

        if not option_file.exists():
            raise FileNotFoundError(f"Option file not found: {option_file}")

        with option_file.open() as stream:
            cfg = yaml.safe_load(stream) or {}

        config_dictionary = update(config_dictionary, cfg)

    return config_dictionary


def load_run_config(serialized=True):
    # relative to cwd/pwd
    config_file = _get_config_filename(serialized=serialized)
    config_manager = ConfigManager()
    if serialized:
        configuration = config_manager.load_state(config_file)
    else:
        configuration = config_manager.load_configuration(config_file)
    return configuration


def freeze_run_configuration(configuration: Configuration):
    """Copies the current imsi configuration file to the configuration folder
    as a dotfile.

    By convention:
        source:       {work_dir}/imsi_configuration_{runid}.yaml
        destination:  {run_config_path}/.imsi_configuration_{runid}.yaml
    """
    wrk_dir = configuration.setup_params.work_dir
    runid = configuration.setup_params.runid
    run_config_path = configuration.setup_params.run_config_path

    basename = f"imsi_configuration_{runid}.yaml"
    src = os.path.join(wrk_dir, basename)
    if not os.path.exists(src):
        raise FileNotFoundError(f"ERROR: missing imsi configuration file {src}")
    dst = os.path.join(run_config_path, f".{basename}")
    shutil.copy2(src, dst)

def save_setup_configuration(configuration: Configuration, save_config : bool = True):
    """Save the resolved imsi configuration state to files.
    A file will be written to the working directory (work_dir) and a copy
    will be made under the config directory (run_config_path) as a hidden
    file.

    By convention the basename of the file is imsi_configuration_{runid}.yaml
    """
    wrk_dir = configuration.setup_params.work_dir
    runid = configuration.setup_params.runid
    config_manager = ConfigManager()

    # create a .imsi folder if it does not exist
    Path(wrk_dir, ".imsi").mkdir(exist_ok=True)
    hidden_imsi_dir = Path(wrk_dir, ".imsi")

    config_manager.save_state(
        configuration,
        filepath=Path(wrk_dir)
        / hidden_imsi_dir
        / f".imsi_configuration_{runid}.pickle",
    )
    if save_config:
        config_manager.save_configuration(
            configuration,
            filepath=Path(wrk_dir) / f"imsi_configuration_{runid}.yaml",
        )
