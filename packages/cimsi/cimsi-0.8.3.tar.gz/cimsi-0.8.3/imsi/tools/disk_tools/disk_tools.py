import os
import glob
import getpass
from pathlib import Path
import shutil
import sys
from textwrap import dedent

from imsi.user_interface.ui_manager import load_run_config, validate_version_reqs
from imsi.user_interface.setup_manager import get_imsi_config_path
from imsi.utils.general import change_dir, remove_folder
from imsi.cli.core_cli import force_dirs


PRINT_MESSAGE_TEMPLATE_CLEANED = "Cleaned space: {path}"

def get_assoc_paths(starting_path, runid):
    """Finds a path(s) given a runid and starting location. Returns all matches

    Max. depth is 2 to find matching folders for runid:
        starting_path/*/runid
    """
    dir_list = [Path(p) for p in glob.glob(f"{starting_path}/*/{runid}")] + [Path(p) for p in glob.glob(f"{starting_path}/{runid}")]
    return dir_list


def delete_run_folders_from_base(starting_path, runid, only_if_empty=False):
    """Deletes the runid folder from the starting location (base).

    Max. depth is 2 to find matching folders for runid:
        starting_path/*/runid

    only_if_empty: If True, the matched path directory is only
        deleted if already empty.
    """

    dirs_assoc = get_assoc_paths(starting_path, runid)

    if len(dirs_assoc) == 0:
        # no locations to delete
        return
    elif len(dirs_assoc) > 1:
        # multiple -> unclear what to delete, skip
        raise ValueError(f"Multiple subfolders with runid {runid} found under {starting_path}; skipping")
    dir_assoc_runid = dirs_assoc[0]  # safe

    if only_if_empty:
        try:
            remove_folder(dir_assoc_runid, force=False)
        except OSError:
            # if the folder is not empty, leave intact
            pass
        else:
            print(PRINT_MESSAGE_TEMPLATE_CLEANED.format(path=dir_assoc_runid))
    else:
        shutil.rmtree(dir_assoc_runid)
        print(PRINT_MESSAGE_TEMPLATE_CLEANED.format(path=dir_assoc_runid))


def _del_linked_storage_from_base(base, runid, subfolder):
    if base is not None:
        base = os.path.expandvars(base)
        base_runid = os.path.join(base, runid, subfolder)

        if os.path.exists(base_runid):
            shutil.rmtree(base_runid)
        print(PRINT_MESSAGE_TEMPLATE_CLEANED.format(path=base_runid))

        # delete the parent folder if empty only
        delete_run_folders_from_base(base, runid, only_if_empty=True)


def clean_run(runid_path, setup, temp, data):
    """Deletes folders associated with a run"""

    runid_path = Path(runid_path).resolve()
    # Check to see if WRK_DIR is set. If it is, make sure the path is the same as runid_path
    # If they are not the same we bail to prevent edge cases where you can accidentally clean
    # the wrong run
    if Path(os.getenv("WRK_DIR", runid_path)).resolve() != runid_path.resolve():
        sys.exit(dedent(f"""
            Error: 'WRK_DIR' is set to a location that differs from the runid_path provided:
              WRK_DIR: {os.getenv("WRK_DIR")}
              runid_path: {runid_path}

            unset 'WRK_DIR' before using imsi clean
              (use "unset WRK_DIR" to unset the environment variable)
            """)
        )

    runid = runid_path.name

    # Ensure correct version of imsi for configuration
    try:
        imsi_config_path = get_imsi_config_path(runid_path / 'src')
    except FileNotFoundError as e:
        sys.exit(e)
    validate_version_reqs(imsi_config_path)

    with change_dir(runid_path):
        # TODO DEV: force_dirs imported from cli -- slate for change of location
        # or new method needed that is built for purpose
        force_dirs(Path(f".imsi/.imsi_configuration_{runid}.pickle"))
        config = load_run_config(serialized=True)

    # Make an assumption that the run is being cleaned by the user who created the run.
    user_id = getpass.getuser()

    # deletes the information in the temp space
    if temp:
        temp_dir = config.machine.scratch_dir.replace('${USER}', user_id)
        delete_run_folders_from_base(temp_dir, runid)

    # deletes the data from the run
    if data:
        data_dir = config.machine.storage_dir.replace('${USER}', user_id)
        delete_run_folders_from_base(data_dir, runid)

    # deletes the setup directory.
    if setup:

        # deletes the dir that contains src
        # IMPORTANT: Use path from config; do *not* use realpath of src
        # as it may have been a run set up with 'link'.
        # (src_storage_dir is ignored when fetch_method=link)
        try:
            src_storage_dir = config.machine.setup.src_storage_dir
        except AttributeError:
            pass
        else:
            _del_linked_storage_from_base(src_storage_dir, runid, 'src')

        # deletes the dir that contains the exes
        try:
            exe_storage_dir = config.machine.exe_storage_dir
        except AttributeError:
            pass
        else:
            _del_linked_storage_from_base(exe_storage_dir, runid, 'bin')

        shutil.rmtree(runid_path)
        print(PRINT_MESSAGE_TEMPLATE_CLEANED.format(path=Path(runid_path).resolve()))
