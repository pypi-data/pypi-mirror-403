from imsi.utils.general import change_dir, delete_or_abort, get_active_venv
from imsi.utils import git_tools
from imsi.user_interface.ui_manager import (
    create_imsi_configuration,
    build_run_config_on_disk,
    validate_version_reqs
)

from pydantic import BaseModel, field_validator, Field, model_validator
from typing import Optional
from pathlib import Path
import shutil
import sys
import os
import subprocess
import sys
import re
import warnings


# runid can contain one or more of the following characters:
#   - Lowercase letters (`a-z`).
#   - Digits (`0-9`).
#   - Hyphens (`-`).
RUNID_PATTERN = re.compile(r"^[a-z0-9-]+$")


class InvalidSetupConfig(Exception):
    """Used to catch invalid setup configurations and provide
    useful feedback to user"""

    pass


class SetupConfigWarning(UserWarning):
    pass


class GitRemoteRepositoryValidator(BaseModel):
    repo_url: str
    remote_branch: Optional[str] = None

    @field_validator("repo_url", mode="after")
    def is_valid_repo_url(url: str) -> bool:
        """Check if a given URL is a valid Git repository."""
        result = subprocess.run([
                    "git", "ls-remote", url
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            raise InvalidSetupConfig(f"Invalid Git repository URL: '{url}'.")
        return url

    @model_validator(mode="after")
    def is_valid_remote_ref(self):
        """Validate that self.remote_branch is a valid branch or tag in the remote repo.
        Skip validation if it looks like a SHA-1 hash."""

        # Skip validation for anything that looks like a SHA-1
        if git_tools.is_sha1(self.remote_branch):
            return self

        # Check if 'branch' is in the remote branches/tags
        proc = subprocess.run([
                    'git', 'ls-remote', '--exit-code', self.repo_url,
                    '--heads', '--tags', self.remote_branch
                    ],
                    capture_output=True
                    )
        if proc.returncode != 0:
            raise InvalidSetupConfig(
                f"'{self.remote_branch}' is not a valid remote branch or tag in {self.repo_url}."
            )

        return self


class SetupSourceOptions(BaseModel):
    repo: str
    ver: Optional[str] = None
    fetch_method: str

    @field_validator("fetch_method")
    def validate_fetch_method(cls, value):
        valid_fetch = ["clone", "clone-full", "link", "copy"]
        if value not in valid_fetch:
            raise InvalidSetupConfig(
                f"'{value}' is not a valid fetch method. Must in {valid_fetch}."
            )
        return value

    @model_validator(mode="after")
    def error_if_version_unused(self):
        if self.fetch_method in ["clone", "clone-full"] and self.ver is None:
            raise InvalidSetupConfig(
                "\n\n**ERROR**: When --fetch_method is clone, --ver must be specified."
            )
        return self

    @model_validator(mode="after")
    def error_if_version_used(self):
        if self.fetch_method in ["copy", "link"] and self.ver is not None:
            raise InvalidSetupConfig(
                "\n\n**ERROR**: When --fetch_method is copy or link, --ver cannot be specified."
            )
        return self

    @field_validator("repo")
    def validate_git_or_path(cls, value):
        if not Path(value).exists() and not re.match(git_tools.GIT_URL_PATTERN, value):
            raise InvalidSetupConfig(
                f"Check that the repository or path exists: {value}. Ensure remote patterns match: git@<remote>:<project>/<repo> or is a valid URL if using https."
            )
        else:
            return value

    @model_validator(mode="after")
    def error_if_bad_git(self):
        if self.fetch_method in ["clone", "clone-full"]:
            GitRemoteRepositoryValidator(repo_url=self.repo, remote_branch=self.ver)
        if (self.fetch_method == "clone") and git_tools.is_sha1(self.ver):
            # using a hash for setting up a repo as a shallow clone (fetch_method=clone)
            # is problematic for repos with submodules; use the full depth clone
            # instead
            warnings.warn(
                "Can't use --fetch_method=clone and --ver=sha1; continuing with --fetch_method=clone-full",
                SetupConfigWarning
                )
            self.fetch_method = 'clone-full'
        return self


def overwrite_or_abort(path: str, force: bool):
    """Overwrite path if exists or abort.

    The path is relative to cwd. This can be useful for run setup
    folders, where the path is equivalent to the runid.
    """
    if Path(path).exists():
        if force:
            shutil.rmtree(path)
        else:
            print(f"\n\n**WARNING**: The directory for {Path(path).name} already exists.")
            delete_or_abort(path)


def get_imsi_config_path(path):
    imsi_config_path = Path(path) / "imsi-config"
    if not imsi_config_path.exists():
        raise FileNotFoundError(
                f"\n\n **ERROR**: 'imsi-config' directory not found at the top level of the repo provided."
        )
    return imsi_config_path


class ValidatedSetupOptions(SetupSourceOptions):
    """Validate setup inputs early in single location."""

    runid: str = Field(..., max_length=21)
    exp: str | None
    model: Optional[str]
    seq: Optional[str] = None
    machine: Optional[str] = None
    flow: Optional[str] = None
    compiler: Optional[str] = None
    postproc: Optional[str] = None

    @field_validator("runid", mode="before")
    def validate_runid(cls, value):
        if RUNID_PATTERN.match(value) and len(value) < 20:
            return value
        elif len(value) >= 20:
            raise InvalidSetupConfig(
                f"Your runid ---> {value} <--- is too long at {len(value)} chars! It must be less than 20 characters."
            )

        raise InvalidSetupConfig(
            f"Your runid ---> {value} <--- contains unsupported characters! "
            "You must use a runid containing only lowercase alphanumeric characters 'a-z0-9', or hyphens '-'"
            "Also, remember to make it short (<20chars) and unique to you"
            "Examples: runid=ncs-tst-ctrl-01"
        )


def get_source(fetch_method, repo, ver=None,
               path: str = None, source_name: str | None = None,
               force: bool = False, strict: bool = False, verbose: bool = False
               ):
    """Get source repository.

    Inputs
    ------
    fetch_method: str [clone, clone-full, copy, link]
        Fetch method for source code
    repo: str
        URL or path to repository of source code.
    ver : str, None
        Version of source code (for clone* fetch methods only), i.e. the
        git branch.
    path: str, Path
        Base path to where the source folder is placed
    source_name: str, Path
        Name of destination folder in the base path. If None, uses the
        name of the repo (if clone*) or basename of the source folder
        (if copy|link).
    force: bool
        Overrides interactive prompt if the folder (path/source_name)
        already exists.
    strict: bool
        If True, will raise a FileNotFoundError if the 'imsi-config' is
        missing at the top-level of the folder. If False, prints a warning.
    verbose: bool
        Display verbose information. This will display the output from
        git operations.

    Outputs
    -------
        Returns the path to the source that was requested.
    """
    quiet = not verbose

    try:
        src_args = SetupSourceOptions(fetch_method=fetch_method, ver=ver, repo=repo)
    except InvalidSetupConfig as e:
        raise e

    # now use the src_args values, as they have been validated

    if path is None:
        path = Path.cwd()

    if source_name is None:
        if src_args.fetch_method in ['clone', 'clone-full']:
            source_name = git_tools.get_repo_name(repo)
        elif src_args.fetch_method in ['copy', 'link']:
            source_name = Path(src_args.repo).name

    target = path / Path(source_name)

    # make sure that target is not the same as source repo (copy/link)
    if src_args.fetch_method in ['copy', 'link']:
        if target.resolve().absolute() == Path(src_args.repo).resolve().absolute():
            sys.exit(
                f"**ERROR**: source and destination repository represent the same path: {target}"
            )

    overwrite_or_abort(target, force)

    os.makedirs(path, exist_ok=True)

    # Clone, soft link or copy the source code
    if src_args.fetch_method == "clone":
        print(f"Cloning (shallow) {src_args.ver} from {src_args.repo}")
        git_tools.clone(src_args.repo, src_args.ver,
                                       local_name=source_name, path=path,
                                       depth=1, quiet=quiet)
    elif src_args.fetch_method == 'clone-full':
        print(f"Cloning {src_args.ver} from {src_args.repo}")
        git_tools.clone(src_args.repo, src_args.ver,
                                       local_name=source_name, path=path,
                                       depth=None, quiet=quiet)
    elif src_args.fetch_method == "link":
        print(f"Soft linking source from {src_args.repo}")
        os.symlink(Path(src_args.repo).resolve(), target)
    elif src_args.fetch_method == "copy":
        print(f"Copying source from {src_args.repo}")
        shutil.copytree(src_args.repo, target, symlinks=True, ignore_dangling_symlinks=True)

    try:
        get_imsi_config_path(target)
    except FileNotFoundError:
        if strict:
            raise FileNotFoundError
        else:
            print(f"\n**WARNING**: The source does not contain an imsi-config folder under: {target}\n")

    return target


def setup_run(setup_args: ValidatedSetupOptions, force: bool = False, verbose=False, **kwargs):
    """
    Create a run directory, clone in the source code, and checkout version ver

    Inputs:
    -------
    setup_args : ValidatedSetupOptions
        A validated set of setup options for the run
    force: bool
        Force the operation (if the folder exists, delete it, then run the operation).
    verbose : bool
        Display verbose information. This will display the output from
        git operations.

    Outputs:
    --------
        Creates the run directory (named for setup_args.runid) where the
        source (src) contains the contents of the setup_args.repo using
        setup_args.ver and resolved for the imsi setup parameters.
    """

    move_src_to_storage = not kwargs.pop('no_src_storage', False)

    overwrite_or_abort(setup_args.runid, force)

    work_dir = Path(setup_args.runid).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    super_repo_source = 'src'   # strict requirement

    src_dir = get_source(
        setup_args.fetch_method, setup_args.repo,
        ver=setup_args.ver, path=work_dir,
        source_name=super_repo_source,
        verbose=verbose,
        force=True,          # always True, due to overwrite_or_abort
        strict=False         # handle this below
        )

    # Requirement that imsi-config appears at the highest setup_args.repo
    try:
        imsi_config_path = get_imsi_config_path(src_dir)
    except FileNotFoundError as e:
        sys.exit(e)

    validate_version_reqs(imsi_config_path)

    imsi_venv = get_active_venv()

    setup_params = {
        "model_name": setup_args.model,               # user
        "experiment_name": setup_args.exp,            # user
        "machine_name": setup_args.machine,           # user - optional
        "compiler_name": setup_args.compiler,         # user - optional
        "runid": setup_args.runid,                    # user
        "work_dir": str(work_dir),                    # user - implicit
        "source_path": str(src_dir),                  # convention
        "source_repo": setup_args.repo,               # tracking
        "source_version": setup_args.ver,             # tracking
        "run_config_path": str(work_dir / "config"),  # convention
        "imsi_config_path": str(imsi_config_path),    # convention
        "fetch_method": setup_args.fetch_method,      # tracking
        "sequencer_name": setup_args.seq,             # user - optional
        "flow_name": setup_args.flow,                 # user - optional
        "imsi_venv": imsi_venv,                       # functional
        "postproc_profile": setup_args.postproc       # user - optional
    }

    with change_dir(work_dir):
        configuration, db = create_imsi_configuration(imsi_config_path, setup_params)

        try:
            src_storage_dir = configuration.machine.setup.src_storage_dir
        except AttributeError:
            src_storage_dir = None

        if move_src_to_storage:
            if (src_storage_dir is not None) and (setup_args.fetch_method != 'link'):
                # move the src to the desired location, link back to local /src

                src_storage_exp = os.path.realpath(os.path.expandvars(src_storage_dir))
                src_storage_runid = os.path.join(src_storage_exp, setup_args.runid)
                ss = os.path.join(src_storage_runid, super_repo_source)

                # but only create the src_storage_dir if it is not the same
                # path as the src under the setup folder
                if Path(ss).resolve() != Path(src_dir).resolve():
                    if os.path.exists(ss):
                        shutil.rmtree(ss)
                    os.makedirs(src_storage_runid, exist_ok=True)

                    try:
                        shutil.move(setup_params['source_path'], ss)
                    except PermissionError:
                        # src left in place
                        warnings.warn(
                            f"Can't move source to {src_storage_exp}: Permission denied.\n"
                            f"source left in place under {setup_args.runid}/{super_repo_source}"
                            )
                    except OSError as e:
                        raise e
                    else:
                        print(f'Soft linking source {setup_args.runid}/{super_repo_source} to {ss}')
                        os.symlink(ss, setup_params['source_path'])

        build_run_config_on_disk(configuration, db)
        print(
            f"\nIMSI setup complete. You can now: \n\n\t\t cd {setup_args.runid} \n"
            f"to continue with configuration/compilation/submission, see:\n\t\t imsi -h"
        )
