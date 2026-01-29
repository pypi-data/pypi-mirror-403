"""
imsi CLI
--------

The entry-point console script that interfaces all users commands to imsi.

imsi has several categories of sub-commands. As this module develops further,
the sub-groups are implemented in the relevant downstream modules.
"""

import click
from imsi.cli.sectioned_group import SectionedGroup

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

DECO_HELP="""\b
     ___   _________   _________   ___
    |___| | __   __ | |   ______| |__ |
    | |   | | | | | | |_______ -.   | |
    | |   | | | | | |         | |   | |
 ___| |   | | |_| | |  _______| |   | |___
|___\\_|   |_|     |_| |_________|   |_____|

IMSI CLI — manage configs, builds, runs, and tools.
"""

ECHO_INVOKE_COMMAND_NAMES = [
    'config', 'reload', 'set', 'build', 'submit', 'save-restarts',
    'tapeload-rs', 'get-src'
    ]

@click.group(
    cls=SectionedGroup,
    invoke_without_command=True,
    context_settings=CONTEXT_SETTINGS,
    help=DECO_HELP,
)
@click.version_option(package_name="cimsi")
@click.option("-f", "--force", is_flag=True, help="Force the operation")
@click.pass_context
def cli(ctx, force):
    ctx.ensure_object(dict)
    ctx.obj["FORCE"] = force

    if ctx.invoked_subcommand is None:
        # print help if no subcommand entered
        click.echo(ctx.get_help())
    elif ctx.invoked_subcommand in ECHO_INVOKE_COMMAND_NAMES:
        click.echo(f"IMSI {ctx.invoked_subcommand}")


cli.add_lazy_command("imsi.cli.core_cli.setup")
cli.add_lazy_command("imsi.cli.core_cli.config")
cli.add_lazy_command(
    "imsi.cli.core_cli.save_restarts",
    name="save-restarts",
    context_settings={"ignore_unknown_options": True},
    )
cli.add_lazy_command(
    "imsi.cli.core_cli.tapeload_rs",
    name="tapeload-rs",
    context_settings={"ignore_unknown_options": True},
    add_help_option=False,  # Disable automatic help flag,
    )
cli.add_lazy_command(
    "imsi.cli.core_cli.build",
    short_help="Compile model components.",
    context_settings={"ignore_unknown_options": True},
    add_help_option=False,  # Disable automatic help flag
)
cli.add_lazy_command("imsi.cli.core_cli.submit")
cli.add_lazy_command("imsi.cli.core_cli.status")
cli.add_lazy_command("imsi.cli.core_cli.reload")
cli.add_lazy_command("imsi.cli.core_cli.set")
cli.add_lazy_command("imsi.cli.core_cli.get_src", name='get-src')
cli.add_lazy_command("imsi.cli.core_cli.override")
cli.add_lazy_command("imsi.tools.disk_tools.disk_tools_cli.clean")
cli.add_lazy_command("imsi.tools.list.list_cli.list")
cli.add_lazy_command("imsi.tools.menu.menu_cli.setup_menu", name="setup-menu")
cli.add_lazy_command("imsi.cli.core_cli.log_state", name="log-state")

cli.add_lazy_command("imsi.tools.ensemble.ensemble_cli.ensemble")
cli.add_lazy_command("imsi.tools.validate.validate_cli.validate", name="validate")
cli.add_lazy_command("imsi.tools.time_manager.timer_cli.chunk_manager", name="chunk-manager")
cli.add_lazy_command("imsi.tools.simple_sequencer.iss_cli.iss")

cli.add_lazy_command("imsi.tools.qswide.qswide_cli.qswide")