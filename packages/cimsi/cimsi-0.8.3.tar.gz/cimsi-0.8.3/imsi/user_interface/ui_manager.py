import os
import copy
from omegaconf import OmegaConf
from pathlib import Path
import subprocess
import shlex
import shutil
from typing import Dict
from pydantic import BaseModel, field_validator
from typing import Iterable

from imsi.config_manager import config_manager as cm
from imsi.sequencer_interface.sequencers import create_sequencer
from imsi.shell_interface import shell_interface_manager
from imsi.shell_interface.config_hooks_manager import call_hooks
from imsi.utils.dict_tools import parse_vars, update, load_json
from imsi.user_interface.ui_utils import save_setup_configuration, load_run_config, apply_options_overrides
from imsi.utils.general import is_broken_symlink, _return_with_message
from imsi.utils.git_tools import is_repo_clean
from imsi import __version__


def validate_version_reqs(source_config_path: Path = Path("src/imsi-config"), version_req_file: str = "version_requirements.yaml" ):
    """
    Checks the version requirements contained in the version controlled
    config files.

    The imsi minor version is toggled when there are config breaking changes, as such we
    only require the major and minor version match.

    TODO:
        - update output to better inform users on how to find/build the right environments
    """
    path_to_version_req_file = source_config_path/version_req_file
    current_version_no_patch = ".".join(__version__.split(".")[:2])

    # check that req file exists
    if not path_to_version_req_file.exists():
        raise FileNotFoundError(f"{path_to_version_req_file} doesn't exist! This is likely because your repo hasn't been setup"
                         f" to work with {current_version_no_patch}. Please update your config files or use an older version of imsi.")

    required_version = OmegaConf.load(path_to_version_req_file)["imsi_version_requirements"]

    # confirm major/minor version match
    if current_version_no_patch != required_version:
        raise ValueError(
            f"""IMSI VERSION MIS-MATCH! Your source repo's config files are setup to use
                -> {required_version}.* <-
            But you are using
                -> {__version__} <-
            The Major and Minor version must match!

            See https://imsi.readthedocs.io/en/main/config_breaking_changes.html for more information"""
        )


def create_imsi_configuration(
    imsi_config_path: str, setup_params: Dict
) -> (cm.Configuration, cm.ConfigDatabase):
    """Build and return configuration instance and config db given imsi_config_path"""
    if not os.path.isdir(imsi_config_path):
        raise FileNotFoundError(
            f"Could not find imsi config directory at: {imsi_config_path}"
        )

    # create a DB / cm
    db = cm.database_factory(imsi_config_path)
    config_manager = cm.ConfigManager(db)

    configuration = config_manager.create_configuration(**setup_params)
    # Save the configuration for future editing/reference
    save_setup_configuration(configuration, save_config=True)

    # Create a configuration based on user input from setup cli
    return (configuration, db)


def build_run_config_on_disk(
    configuration: cm.Configuration, db: cm.ConfigDatabase, track=True, force=False
):
    """This actually creates the physical config directory on disk, and extracts/modifies various relevant files"""
    # Build the actual config directory with contents for this configuration

    shell_interface_manager.build_config_dir(db, configuration, track=track, force=force)

    # Do scheduler/sequencer setup
    sequencer = create_sequencer(configuration.setup_params.sequencer_name)
    sequencer.setup(configuration, force=force)
    sequencer.config(configuration, force=force)

    # Do other config hooks (only if constraints are met as defined in current
    # config, which will be checked via call_hooks)
    call_hooks(configuration, "post-config", force=force)

    if track:
        run_config_path = configuration.get_unique_key_value('run_config_path')
        # hooks may have changed contents of config folder - track these
        clean, _ = is_repo_clean(run_config_path)
        if not clean:
            subprocess.run(shlex.split('git add -A'), cwd=run_config_path)
            subprocess.run(shlex.split('git commit -q -m "IMSI: config_hooks:post-hook"'), cwd=run_config_path)


def reload_config_from_source(force=False):
    """
    Build a new config directory from upstream imsi source

    This will re-extract everthing out of the cloned repository to re-create
    the config directory. I.e. if one made changes in the repo after setup, and
    wanted to apply them, they would call this update function.
    """
    original_configuration = load_run_config()

    # This will rebuild the config directory completely
    imsi_config_path = original_configuration.get_unique_key_value("imsi_config_path")
    new_configuration, db = create_imsi_configuration(
        imsi_config_path,
        original_configuration.setup_params.model_dump(),
    )
    build_run_config_on_disk(new_configuration, db, force=force)


def update_config_from_state(force=False):
    """Apply changes made in the "imsi_configuration_${runid}" state file
    to the configuration and update the config directory as appropriate.
    """
    # 1. Save configuration from the configuration object to .imsi...
    # 2. Load the configuration from the .imsi... file

    user_facing_configuration = load_run_config(serialized=False)

    save_setup_configuration(user_facing_configuration, save_config=False) # no need to instantly save again
    state_configuration = load_run_config()
    # This will rebuild the config directory completely based on what is in the configuration file.
    # It would be good if there were nominal validity testing.
    db = cm.database_factory(
        state_configuration.get_unique_key_value("imsi_config_path")
    )
    build_run_config_on_disk(state_configuration, db, force=force)


class Override(BaseModel):
    options: str

    @field_validator("options")
    def validate_options(cls, v):
        if "/" not in v:
            raise ValueError("Option must be in the format <group>/<option>")
        return v


def parse_override_options(options: Iterable[str]) -> list[dict]:
    return [Override(options=o).model_dump() for o in options]


def parse_override(options: Iterable[str], force=False):
    """Parse and apply command-line option overrides to the current IMSI run configuration.

    Parameters:
    - options: An iterable of option identifier strings. Each string must contain
        a '/' separating the group and option name (e.g. "group/option" or
        "group/option=value").
    - force: If True, forces rebuilding of on-disk run artifacts
        and other actions performed by build_run_config_on_disk even if not strictly
        necessary. Defaults to False.
    """

    # get existing simulation config
    configuration = load_run_config()
    db = cm.database_factory(configuration.get_unique_key_value("imsi_config_path"))

    print(f"Overriding configuration with: {options}")
    options_list = parse_override_options(options)

    configuration_with_overrides = apply_options_overrides(
        config_dictionary=configuration.model_dump(), options=options_list
    )
    new_configuration = cm.Configuration(**configuration_with_overrides)

    # Update the saved configuration file accordingly
    # (including triggering rebuilding of /sequencer folder too, running
    # hooks, etc):
    build_run_config_on_disk(new_configuration, db, force=force)

    # Update the saved configuration file accordingly
    save_setup_configuration(new_configuration, save_config=True)


def set_selections(parm_file=None, selections=None, force=False):
    """Parse key=value pairs of selection given on the command line
    Try to apply these to the imsi selections for the sim.
    """

    # get existing simulation config
    configuration = load_run_config()

    db = cm.database_factory(configuration.get_unique_key_value("imsi_config_path"))
    config_manager = cm.ConfigManager(db)

    updated_setup_params = copy.deepcopy(configuration.setup_params)

    if parm_file:
        file_values = load_json(
            parm_file
        )  # would actually be more valuable for options I think, since
        # selections are few bu options possibly many.
        # This is updating the ._config dict in place
        updated_setup_params = update(updated_setup_params, file_values)
    if selections:
        print(f"set selections: {selections}")
        values = parse_vars(selections, none_as_str=False)
        setup_params = configuration.setup_params

        # selections must match imsi setup cli options to match parts of config
        # (some but not all allowed)
        updated_setup_params.model_name = values.pop('model', setup_params.model_name)
        updated_setup_params.experiment_name = values.pop('exp', setup_params.experiment_name)
        updated_setup_params.machine_name = values.pop('machine', setup_params.machine_name)
        updated_setup_params.compiler_name = values.pop('compiler', setup_params.compiler_name)
        updated_setup_params.sequencer_name = values.pop('sequencer', setup_params.sequencer_name)
        updated_setup_params.flow_name = values.pop('flow', setup_params.flow_name)
        updated_setup_params.postproc_profile = values.pop('postproc', setup_params.postproc_profile)

        # warn for bad selections, and don't add them to setup params
        # TODO: would be better to do this via cli (early)
        for k,v in values.items():
            print(f"**WARNING**: selection '{k}={v}' not in setup params; not added to configuration")

    # Create a new simulation that we imbue with these properties
    new_configuration = config_manager.create_configuration(**updated_setup_params.model_dump())

    # Update the saved configuration file accordingly
    # (including triggering rebuilding of /sequencer folder too, running
    # hooks, etc):
    build_run_config_on_disk(new_configuration, db, force=force)

    # Update the saved configuration file accordingly
    save_setup_configuration(new_configuration, save_config=True)

def compile_model_execs(args, force=False):
    """
    Builds all component executables by calling an upstream script from the
    repository. Should be under /bin but not enforceable.
    """
    configuration = load_run_config()
    work_dir = configuration.get_unique_key_value("work_dir")
    runid = configuration.setup_params.runid

    if not os.path.isdir(work_dir):
        raise FileNotFoundError(
            f"Could not find the run working directory at: {work_dir}"
        )

    bin_dir = os.path.join(work_dir, 'bin')
    real_bin_dir = os.path.realpath(bin_dir)

    exe_storage_dir = configuration.machine.exe_storage_dir   # path|None

    if exe_storage_dir is None:
        real_exe_storage_dir = None
    else:
        exep_exe = os.path.expandvars(os.path.realpath(exe_storage_dir))
        if exep_exe == real_bin_dir:
            # pointing to itself
            exe_storage_dir = None
            real_exe_storage_dir = None
        else:
            # exe_storage_dir/{runid}/bin <- bin
            real_exe_storage_dir = os.path.join(
                os.path.expandvars(os.path.realpath(exe_storage_dir)),
                runid,
                'bin'
                )

    # nothing to build:
    NTB_MESSAGE = "Nothing to build. To clear the executable folder(s), try: imsi -f build"

    if force:
        # cleanup all bin folders
        if os.path.exists(real_bin_dir):
            if os.path.islink(real_bin_dir):
                os.path.unlink(real_bin_dir)
            else:
                shutil.rmtree(real_bin_dir)
        if (exe_storage_dir is not None):
            if os.path.exists(real_exe_storage_dir):
                shutil.rmtree(real_exe_storage_dir)

    # setup the bin folders - local (in work_dir) and storage (exe_storage_dir as the base)
    # and account for:
    #   - changing between inputs of exe_storage_dir and
    #   - re-running imsi build (preventing full builds when not needed)
    if (exe_storage_dir is None) or (real_bin_dir == real_exe_storage_dir):
        if is_broken_symlink(bin_dir):
            # self-pointing case
            os.unlink(bin_dir)
            if not os.path.exists(real_exe_storage_dir):
                os.makedirs(real_exe_storage_dir)
                os.symlink(real_exe_storage_dir, bin_dir)
            # build required
        elif os.path.exists(bin_dir):
            if os.path.islink(bin_dir) and (real_exe_storage_dir != real_bin_dir):
                # switch from ln to dir
                os.unlink(bin_dir)
                os.makedirs(bin_dir)
                # build required
        else:
            os.makedirs(bin_dir)
            # build required
    else:
        # linking required
        if is_broken_symlink(bin_dir):
            os.unlink(bin_dir)
        else:
            if os.path.exists(real_exe_storage_dir):
                if os.path.exists(bin_dir):
                    if os.path.islink(bin_dir):
                        return _return_with_message(NTB_MESSAGE)
                    else:
                        # relink (eg previously wasn't linked to storage)
                        shutil.rmtree(bin_dir)
                        os.symlink(real_exe_storage_dir, real_bin_dir)
                        return _return_with_message(NTB_MESSAGE)
                else:
                    if os.path.exists(real_exe_storage_dir):
                        os.symlink(real_exe_storage_dir, real_bin_dir)
                        return _return_with_message(NTB_MESSAGE)
                    else:
                        # switching or remake ln
                        os.makedirs(real_exe_storage_dir)
                        os.symlink(real_exe_storage_dir, real_bin_dir)
                        # build required
            elif real_exe_storage_dir == real_bin_dir:
                return _return_with_message(NTB_MESSAGE)
            else:
                os.makedirs(real_exe_storage_dir, exist_ok=True)
                if os.path.islink(bin_dir):
                    os.unlink(bin_dir)
                if os.path.exists(bin_dir) and os.path.isdir(bin_dir):
                    shutil.rmtree(bin_dir)
                os.symlink(real_exe_storage_dir, bin_dir)

    comp_script_basename = 'imsi-tmp-compile.sh'
    comp_script = os.path.join(work_dir, comp_script_basename)

    if not os.path.exists(comp_script):
        raise FileNotFoundError(
            f"Could not find compilation file {comp_script_basename} at: {work_dir}"
        )
    compile_task = subprocess.Popen([os.path.join('.', comp_script_basename)] + list(args), cwd=work_dir)
    compile_task.wait()
    streamdata = compile_task.communicate()[0]
    rc = compile_task.returncode
    if rc != 0:
        raise ValueError(f"Error: Compiling failed with {comp_script}")


def submit_run():
    """Instantiate the configuration object and submit job to queue"""
    configuration = load_run_config()
    setup_params = configuration.setup_params
    sequencer = create_sequencer(setup_params.sequencer_name)
    sequencer.submit(configuration)


def save_restarts(args):
    """Execute the save restarts script"""

    if Path("./save_restart_files.sh").exists():
        p = subprocess.Popen(["./save_restart_files.sh"] + list(args))
        p.wait()
    else:
        raise FileNotFoundError(
            "Could not find the save_restart_files.sh script. Are you in the correct directory?"
        )

def tapeload_rs(args):
    """Execute the tapeload rs script"""

    if Path("./tapeload_rs.sh").exists():
        p = subprocess.Popen(["./tapeload_rs.sh"] + list(args))
        p.wait()
    else:
        raise FileNotFoundError(
            "Could not find the tapeload_rs.sh script. Are you in the correct directory?"
        )

def get_sequencer_status():
    configuration = load_run_config()
    setup_params = configuration.setup_params
    sequencer = create_sequencer(setup_params.sequencer_name)
    sequencer.status(configuration, setup_params)


# WIP
def query_time():
    """Instantiate the configuration / SimulationTime instances and enable querying timers"""
    configuration = load_run_config()
    sequencing_config = configuration.sequencing
