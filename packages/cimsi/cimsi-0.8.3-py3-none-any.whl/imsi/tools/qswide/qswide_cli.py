import click

@click.command(help="Wrapper around qstat to support wide format queue listing")
@click.option(
    '-m', '--machine', 
    default=None, 
    help="The machine to check."
)
@click.option(
    '-u', '--user', 
    default=None, 
    help="The name of a user to search queue by."
)
@click.option(
    '-n', '--ntimes', 
    default=1, 
    type=int, 
    help="The number of times to repeat query. Defaults to 1 query."
)
@click.option(
    '-f', '--freq', 
    default=30, 
    type=int, 
    help="If ntimes > 1, defines the frequency (in seconds) of the queries. Defaults to 30 seconds"
)

def qswide(machine, user, ntimes, freq):
    from imsi.tools.qswide.qswide import monitor_queue
    monitor_queue(user=user, machine=machine, ntimes=ntimes, freq=freq)