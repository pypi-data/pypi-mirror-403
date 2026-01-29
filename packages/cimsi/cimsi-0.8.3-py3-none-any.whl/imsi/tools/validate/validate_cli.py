import click
from pathlib import Path
import sys

def schema_constructor(create_func, **kwargs):
    return create_func(**kwargs)


def check_path(path: Path):
    import imsi.user_interface.ui_manager as uim

    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Provided path {path} does not exist or is not a directory.")

    try:
        uim.validate_version_reqs(path)
    except FileNotFoundError:
        raise SystemExit(f"the path {path} is not a valid imsi-config folder")
    except ValueError as e:
        raise e

@click.group(
    short_help="Validate imsi configuration files.",
    help="Validate imsi configuration files."
)
@click.option(
    "--imsi-config-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=str(Path.cwd()),
    help="Path to the imsi-config directory.",
)
@click.pass_context
def validate(ctx, imsi_config_path):
    """A CLI tool to validate imsi configuration files"""
    from imsi.config_manager.config_manager import ConfigManager, database_factory

    # TIU still print help msg if passed if command invoked from any
    # location (otherwise will not print if check_path fails)
    if sys.argv[-1] in ctx.help_option_names:
        click.echo(ctx.command.get_command(ctx, ctx.invoked_subcommand).get_help(ctx))
        ctx.exit()

    check_path(Path(imsi_config_path))
    db = database_factory(imsi_config_path)
    cm = ConfigManager(db)
    ctx.ensure_object(dict)
    ctx.obj["cm"] = cm
    ctx.obj["imsi_config_path"] = imsi_config_path


@validate.command()
def syntax():
    """Validate the syntax of the imsi configuration files."""
    click.echo("\033[1;32m[✓] The config directory contains valid yaml.\033[0m")


@validate.command()
@click.argument("experiment", type=str)
@click.argument("model", type=str)
@click.pass_context
def experiment(ctx, experiment, model):
    """Validate an experiment configuration."""
    cm = ctx.obj["cm"]
    schema_constructor(
        cm.create_experiment,
        experiment_name=experiment,
        model_name=model,
    )

    click.echo(f"\033[1;32m[✓] Experiment {experiment} adheres to the imsi schema.\033[0m")


@validate.command()
@click.argument("model", type=str)
@click.pass_context
def model(ctx, model):
    """Validate a model configuration."""
    cm = ctx.obj["cm"]
    schema_constructor(cm.create_model, model_name=model)

    click.echo(f"\033[1;32m[✓] Model {model} adheres to the imsi schema.\033[0m")


@validate.command()
@click.argument("machine", type=str)
@click.pass_context
def machine(ctx, machine):
    """Validate a machine configuration."""
    cm = ctx.obj["cm"]
    schema_constructor(cm.create_machine, machine_name=machine)

    click.echo(f"\033[1;32m[✓] Machine {machine} adheres to the imsi schema.\033[0m")


@validate.command()
@click.argument("experiment", type=str)
@click.argument("model", type=str)
@click.pass_context
def components(ctx, experiment, model):
    """Validates an experiment configuration"""
    from imsi.utils.general import change_dir

    cm = ctx.obj['cm']
    with change_dir(ctx.obj["imsi_config_path"]):
        model_basemodel = schema_constructor(cm.create_model, model_name=model)
        experiment_basemodel = schema_constructor(
            cm.create_experiment,
            experiment_name=experiment,
            model_name=model,
        )

        schema_constructor(
            cm.create_components,
            model=model_basemodel,
            experiment=experiment_basemodel,
        )

    click.echo(f"\033[1;32m[✓] Components for experiment {experiment} and model {model} adhere to the imsi schema.\033[0m")


@validate.command()
@click.pass_context
def utilities(ctx):
    """Validate the utility configurations."""
    cm = ctx.obj["cm"]
    schema_constructor(cm.create_utilities)

    click.echo("\033[1;32m[✓] Utilities adheres to the imsi schema.\033[0m")


@validate.command()
@click.argument("sequencer_name", type=str)
@click.argument("machine_name", type=str)
@click.argument("model_name", type=str)
@click.argument("experiment_name", type=str)
@click.argument("flow_name", type=str, required=False, default="")
@click.pass_context
def sequencing(ctx, sequencer_name, machine_name, model_name, experiment_name,  flow_name):
    """Validate a sequencing configuration."""
    cm = ctx.obj["cm"]

    machine = schema_constructor(cm.create_machine, machine_name=machine_name)
    experiment = schema_constructor(
        cm.create_experiment,
        model_name=model_name,
        experiment_name=experiment_name,
    )

    schema_constructor(
        cm.create_sequencing,
        machine=machine,
        sequencer_name=sequencer_name,
        flow_name=flow_name,
        experiment=experiment
    )

    click.echo(f"\033[1;32m[✓] Sequencing {sequencer_name}, experiment {experiment_name}, model {model_name}, and machine {machine_name} adhere to the imsi schema.\033[0m")
