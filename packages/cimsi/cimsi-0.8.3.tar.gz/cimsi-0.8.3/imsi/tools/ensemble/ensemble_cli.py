import click


@click.group(
    help="""
        Commands to manage ensembles of imsi runs. To determine behaviour
        of each ensemble command, refer to the help message of the underlying imsi command.

        
        WARNING: Where the main IMSI tools may prompt 
        users for confirmation before taking action, the ensemble tool does not. 
        Users should take caution of the location of their working directories and 
        be aware of the underlying action the ensemble tool is taking.
    """,
    chain=True, invoke_without_command=True
)
@click.option(
    "--config-path",
    required=True,
    default='./config.yaml',  # note: overrides 'required=True'
    help="Path to the entry config.",
)
@click.option(
    "--show-diffs",
    is_flag=True,
    default=False,
    help="Summarize differences between ensemble members if they exist.",
)
@click.pass_context
def ensemble(ctx, config_path, show_diffs):
    """Manage ensemble runs."""

    from omegaconf import OmegaConf
    from pathlib import Path
    from imsi.tools.ensemble.config import load_config
    import sys

    # TIU still print help msg if help flag is passed,
    # regardless of options/subcommands invoked, and
    # print help for each subcommand:
    if sys.argv[-1] in ctx.help_option_names:
        cmd_line_argvs = sys.argv[2:]
        for name, cmd in ctx.command.commands.items():
            if name in cmd_line_argvs:
                subctx = click.Context(cmd, info_name=name, parent=ctx)
                click.echo('\n>>>> imsi ensemble\n' + cmd.get_help(subctx))
        ctx.exit()

    ctx.ensure_object(dict)

    config_path = Path(config_path).expanduser()

    if not config_path.exists():
        raise click.UsageError(f"Configuration file not found for --config-path: {config_path}")


    cfg = OmegaConf.load(config_path)
    click.echo(f"Attempting to use configuration file: {config_path}")
    ensemble_config, table = load_config(cfg, show_diffs=show_diffs)
    ctx.obj["ensemble_config"] = ensemble_config
    ctx.obj["table"] = table
    ctx.obj["diffs"] = show_diffs


@ensemble.command(help="Run imsi setup for each ensemble member. Overwrites existing setup directories in run_directory.")
@click.pass_context
def setup(ctx):
    """Setup an ensemble using a specific Hydra configuration."""
    from imsi.tools.ensemble import ensemble_manager

    ensemble_manager.run_setup_and_config(
        ensemble_config=ctx.obj["ensemble_config"], tables=ctx.obj["table"]
    )


@ensemble.command(help="Run imsi config for each ensemble member.")
@click.pass_context
def config(ctx):
    """Run imsi config for each ensemble member."""
    from imsi.tools.ensemble import ensemble_manager

    ensemble_manager.run_config(
        ensemble_config=ctx.obj["ensemble_config"], tables=ctx.obj["table"]
    )


@ensemble.command(help="Save the restart files for each ensemble member.")
@click.pass_context
def save_restarts(ctx):
    click.echo("Saving restart files for each ensemble member.")
    from imsi.tools.ensemble import ensemble_manager

    ensemble_manager.save_restarts_ensemble(
        ensemble_config=ctx.obj["ensemble_config"], tables=ctx.obj["table"]
    )


@ensemble.command(help="Compile the ensemble member directories.")
@click.pass_context
def build(ctx):
    click.echo("Compiling the ensemble member directories.")
    from imsi.tools.ensemble import ensemble_manager

    ensemble_manager.compile_ensemble(
        ensemble_config=ctx.obj["ensemble_config"], tables=ctx.obj["table"]
    )


@ensemble.command(help="Submit the ensemble jobs.")
@click.pass_context
def submit(ctx):
    click.echo("Submitting the ensemble jobs.")
    from imsi.tools.ensemble import ensemble_manager

    ensemble_manager.submit_ensemble(
        ensemble_config=ctx.obj["ensemble_config"], tables=ctx.obj["table"]
    )


@ensemble.command(help="Check the status of the ensemble jobs.")
@click.pass_context
def status(ctx):
    click.echo("Checking the status of the ensemble jobs.")
    from imsi.tools.ensemble import ensemble_manager

    ensemble_manager.status_ensemble(
        ensemble_config=ctx.obj["ensemble_config"], tables=ctx.obj["table"]
    )
