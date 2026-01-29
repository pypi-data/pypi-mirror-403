
import click
from functools import wraps
import os
from pathlib import Path
import sys
import warnings


class CommandWithPassthroughEOO(click.Command):
    def format_usage(self, ctx, formatter):
        formatter.write_usage(ctx.command_path, "[OPTIONS] -- [PASSTHROUGH_ARGS]")


def showwarnings_msg_only(message, category, filename, lineno, file=None, line=None):
    print(f"{message}")
warnings.showwarning = showwarnings_msg_only


def passthrough_eoo_delimiter(ctx, param_args, value):
    # enforce requirement that end of options delimiter '--'
    # is entered before trailing args
    delim = '--'
    error_msg = f"Use '{delim}' before passthrough arguments."
    if value:
        try:
            cmd_index = sys.argv.index(ctx.info_name)
            rest_of_args = sys.argv[cmd_index+1:]
        except ValueError:
            # no other arguments after command
            return value
        if rest_of_args[0] != delim:
            raise click.UsageError(error_msg)
    return value


def force_dirs(
    path: Path = Path("src"),
):
    user_in_path = path.exists()
    wrk_dir_env_set = os.getenv("WRK_DIR") is not None

    if user_in_path and wrk_dir_env_set and Path.cwd().resolve() == Path(os.getenv("WRK_DIR")).resolve():
        return

    if wrk_dir_env_set and user_in_path:
        warnings.warn(
            f"WARNING: Both WRK_DIR and {path} directory found. Defaulting to CWD {path} at {Path('.').resolve()}\n",
            UserWarning
        )
        return

    if wrk_dir_env_set and not Path(os.getenv("WRK_DIR"), path).exists():
        sys.exit(
            f"⚠️  $WRK_DIR = {os.getenv('WRK_DIR')} is not a valid imsi directory. Either unset WRK_DIR, or check the path and try again."
        )

    if not any([user_in_path, wrk_dir_env_set]):
        sys.exit(
            f"⚠️  {path} directory not found. This is because:\n"
            "1. You are not currently in your setup directory or one hasn't been created.\n"
            "    or \n"
            "2. The environment variable WRK_DIR is not set to the correct directory."
        )


def log_cli(func=None, logger_name='cli'):
    from imsi.utils.git_tools import is_repo_clean, git_add_commit
    import imsi.cli.core_tracking as ct

    # decorator for logging imsi cli click commands
    def decorator_func(func):
        # the actual decorator
        @wraps(func)
        def wrapper_func(*args, **kwargs):
            # the actual function being wrapped

            track = True

            # hack - required to make sure that:
            #  - this logging isn't possible for all imsi functions (eg setup)
            #  - logs aren't written to files when imsi cli commands are invoked
            #    from the wrong location
            force_dirs()     # success -> pwd == work dir
            path = Path.cwd()

            if args:
                if isinstance(args[0], click.core.Context):
                    # get the cli func name from the context rather than
                    # func.__name__ (because of how click invokes func names)
                    ctx = args[0]
                    func_name = ctx.info_name
            else:
                # FIXME TODO fallback
                func_name = func.__name__

            # init log
            imsi_logger = ct.get_imsi_logger(logger_name, path)
            ct.imsi_log_prelude(func_name, imsi_logger)

            if track:
                config_dir = path / 'config'
                ct.imsi_state_snapshot(path, logger=imsi_logger)

                # force a clean repo for /config
                if logger_name == 'cli':
                    clean_config, _ = is_repo_clean(config_dir)
                    if not clean_config:
                        # always force the config dir to be clean
                        msg = f"IMSI pre-run commit cli:{func_name}"
                        git_add_commit(msg=msg, path=config_dir)
                        imsi_logger.info(msg)

            # invoke the wrapped function
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                imsi_logger.error(f'ERROR {func_name} {type(e).__name__}')
                raise e
            ct.imsi_log_postlude(func_name, imsi_logger)
            return result
        return wrapper_func
    if func:
        # hack to handle decorator without kwargs (style)
        return decorator_func(func)
    return decorator_func


@click.command(
    short_help="Get source code.",
    help="""Get source code.""",
    epilog="""
This command can be used to establish on-disk source repositories
and used with subsequent imsi commands, i.e.:

    imsi get-src --path=/this/path --name=local-src <args>

    imsi setup --repo=/this/path/local-src --fetch_method=<copy|link> <args>
.
"""
)
@click.option(
    "--fetch_method",
    default="clone",
    type=click.Choice(["clone", "clone-full", "link", "copy"]),
    show_default=True,
    help="Fetch method for source code."
)
@click.option("--repo", required=True, help="Git repository URL or path.")
@click.option("--ver", type=str, default=None,
              help="Version of the code to clone (clone* only).")
@click.option("--path", default=Path.cwd(), type=click.Path(),
              help="""Local path to where the source will be placed.
              [default: current directory]
              """)
@click.option("--name", default=None,
              help="Name of folder for the contents of repo. If not provided, the name of the repository is used.")
@click.option("--verbose", default=False, is_flag=True, help="More verbose output.")
@click.pass_context
def get_src(ctx, fetch_method, repo, ver, path, name, verbose):
    from imsi.user_interface.setup_manager import get_source
    get_source(
        fetch_method, repo,
        ver=ver,
        path=path, source_name=name,
        force=ctx.obj["FORCE"],
        verbose=verbose,
        )


SETUP_EPILOG = """\b
More information:

    valid parameter values for --model, --exp, --machine, --seq, --flow,
    --postproc are composed within the repo's imsi-config Configuration Files.
"""
@click.command(
    short_help="Set up a run directory and obtain model source code.",
    epilog=SETUP_EPILOG
    )
@click.option(
    "--runid", type=str,
    default=None,
    required=True,
    help='A unique identifier (<20 char, alphanumeric incl. hyphen, lower case)',
)
@click.option(
    "--repo",
    required=True,
    help="Git repository URL or file path.",
)
@click.option("--ver", type=str, default=None, help="Version of the code to clone (clone* only).")
@click.option("--exp", required=True, type=str, help="Experiment name.")
@click.option("--model", required=True, type=str, help="Model name.")
@click.option(
    "--fetch_method",
    default="clone", type=click.Choice(["clone", "clone-full", "link", "copy"]),
    help="Fetch method for source code.",
    show_default=True
)
@click.option("--seq", default=None, help='Sequencer to use, like "iss" or "maestro".')
@click.option("--machine", default=None, help="Machine to use.")
@click.option("--flow", default=None, help="Workflow to use.")
@click.option("--postproc", default=None, help="Postprocessing profile to use.")
@click.option("--no-src-storage", default=False, is_flag=True, help='Disables src_storage_dir if present in imsi-config')
@click.option("--verbose", default=False, is_flag=True, help="More verbose output.")
@click.pass_context
def setup(ctx, **kwargs):
    """Create a run directory, obtain the model source code, and resolve the configuration files.

    https://imsi.readthedocs.io/en/latest/usage.html#setting-up-a-run
    """
    from imsi.user_interface.setup_manager import (
        setup_run,
        ValidatedSetupOptions,
        InvalidSetupConfig,
    )
    import imsi.cli.core_tracking as ct

    # separate the kwargs
    setup_run_params = ValidatedSetupOptions.model_fields.keys()
    setup_kwargs = {k: kwargs[k] for k in kwargs if k in setup_run_params}
    ctrl_kwargs = {k:kwargs[k] for k in kwargs if k not in setup_run_params}

    try:
        setup_args = ValidatedSetupOptions(**setup_kwargs)
    except InvalidSetupConfig as e:
        click.echo(e)
        raise e

    setup_run(setup_args, force=ctx.obj["FORCE"], **ctrl_kwargs)

    ct.log_setup(sys.argv, setup_args)


@click.command(
    short_help="Log the imsi state.",
    help="Log the imsi state to the .imsi-cli.log.",
    epilog="""\b
    Note:
        This is nominally an imsi utility function. In particular,
        model developers may use this in their run-time code.
    """)
@click.option('-m', '--msg', default=None, required=False,
              help='Message to include in the log.')
@click.option('-p', '--path', type=click.Path(exists=True), default='.',
              required=True,
              help='Path to run folder.')
def log_state(msg, path):
    import imsi.cli.core_tracking as ct

    path = Path(path).resolve()
    logger = ct.get_imsi_logger('runtime', path)
    ct.imsi_log_prelude('log-state', logger)
    ct.imsi_state_snapshot(path, logger=logger)
    if msg is not None:
        logger.info(f'MESSAGE: {msg}')
    ct.imsi_log_postlude('log-state', logger)


@click.command(
    short_help="Apply configuration from the resolved configuration file.",
    help="Apply configuration from the resolved configuration file."
)
@click.pass_context
@log_cli
def config(ctx):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    uim.update_config_from_state(force=ctx.obj["FORCE"])


@click.command(
    short_help="Reload the imsi Configuration Files from the on-disk repo.",
    help="""Reload the imsi Configuration Files from the on-disk repo
    and update the run configuration.
    """
)
@click.pass_context
@log_cli
def reload(ctx):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    uim.reload_config_from_source(force=ctx.obj["FORCE"])


@click.command(
    short_help="Set (apply) the configuration from selectors.",
    help="Set (apply) the configuration from selectors.",
    )
@click.option(
    "-s",
    "--selections",
    metavar="SETUP_PARAM=VALUE",
    multiple=True,
    help="""A key-value pair for a setup parameter and it's value.
    [Example: exp=exp_y]"""
)
@click.option(
    "-o",
    "--options",
    is_flag=True,
    required=False,
    default=None,
    deprecated="See 'imsi override --help' for details.",)
@click.pass_context
@log_cli
def set(ctx, selections, options):
    import imsi.user_interface.ui_manager as uim

    if options or options is not None:
        sys.exit(1)

    if not selections:
        print(ctx.command.get_help(ctx))
        sys.exit(1)

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    # tmp disabling parm_file -> None
    uim.set_selections(None, selections, force=ctx.obj["FORCE"])


@click.command(
    short_help="Override settings.",
    help="Override configuration options from imsi-config."
)
@click.option(
    "-o", "--option",
    metavar="PATH/FILE.yaml",
    multiple=True,
    help="File paths under imsi-config/options. If specifying multiple paths, options are applied in the order provided."
)
@click.pass_context
@log_cli
def override(ctx, option):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    if option:
        uim.parse_override(option, force=ctx.obj["FORCE"])
    else:
        click.echo("Error: Provide at least one --option.", err=True)


@click.command(
    cls=CommandWithPassthroughEOO,
    context_settings=dict(ignore_unknown_options=True,),
    short_help="Compile model components.",
    help="Compile model components.",
    epilog="The script 'imsi-tmp-compile.sh' will be executed."
)
@click.option("--script-help", is_flag=True, help="Display the help message of the script.")
@click.argument("args", nargs=-1, callback=passthrough_eoo_delimiter)
@click.pass_context
@log_cli
def build(ctx, script_help, args):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    args = ['-h'] if script_help else args
    uim.compile_model_execs(args, force=ctx.obj['FORCE'])


@click.command(help="Submit the simulation to the sequencer.")
@log_cli
def submit():
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    uim.submit_run()


@click.command(
    cls=CommandWithPassthroughEOO,
    context_settings=dict(ignore_unknown_options=True,),
    short_help="Save model restart files.",
    help="Save model restart files.",
    epilog="The script 'save_restart_files.sh' will be executed."
)
@click.option("--script-help", is_flag=True, help="Display the help message of the script.")
@click.argument("args", nargs=-1, callback=passthrough_eoo_delimiter)
@log_cli
def save_restarts(script_help, args):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    args = ['-h'] if script_help else args
    uim.save_restarts(args)

@click.command(
    cls=CommandWithPassthroughEOO,
    context_settings=dict(ignore_unknown_options=True,),
    short_help="Retrieve the model restart files from tape.",
    help="Retrieve the model restart files from long-term storage (tape).",
    epilog="The script 'tapeload_rs.sh' will be executed."
)
@click.option("--script-help", is_flag=True, help="Display the help message of the script.")
@click.argument("args", nargs=-1, callback=passthrough_eoo_delimiter)
@log_cli
def tapeload_rs(script_help, args):
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    args = ['-h'] if script_help else args
    uim.tapeload_rs(args)

@click.command(help="Get sequencer status information.")
def status():
    import imsi.user_interface.ui_manager as uim

    force_dirs(Path("src"))
    uim.validate_version_reqs()
    uim.get_sequencer_status()
