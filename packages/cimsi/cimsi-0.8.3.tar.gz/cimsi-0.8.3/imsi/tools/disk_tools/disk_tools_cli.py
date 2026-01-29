import click

@click.command(
    short_help="Deletes a run's directories.",
    help="""Deletes a run's directories.

    Default (no flags): contents of scratch_dir and storage_dir are deleted.
    """
    )
@click.option(
    "--runid_path",
    required=True,
    type=click.Path(),
    help="Path to a valid run setup directory.",
)
@click.option("-s", "--setup/--no-setup", default=False,
              help="Clean setup directory.", show_default=True)
@click.option("-t", "--scratch-dir/--no-scratch-dir", "temp", default=True,
              help="Clean scratch data directory.", show_default=True)
@click.option("-d", "--storage-dir/--no-storage-dir", "data", default=True,
              help="Clean storage data directory.", show_default=True)
@click.option("-a", "--all", "clean_all", is_flag=True, help="Clean all locations.")
def clean(runid_path, setup, temp, data, clean_all):
    # If no options selected by default cleans data and temp directories
    from imsi.tools.disk_tools.disk_tools import clean_run

    if clean_all:
        setup, temp, data = (True, True, True)

    if not any((setup, temp, data)):
        click.echo("Nothing to clean")
    else:
        clean_run(runid_path, setup, temp, data)
