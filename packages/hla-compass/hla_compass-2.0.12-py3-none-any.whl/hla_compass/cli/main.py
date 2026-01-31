import click
import logging
# from .. import __version__
from .._version import __version__
from .utils import _enable_verbose

from .auth import auth
from .module import init, build, publish, publish_status, validate
from .dev import dev, serve, test, run
from .keys import keys

@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """HLA-Compass SDK"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if verbose:
        _enable_verbose(ctx)
    else:
        logging.getLogger().setLevel(logging.INFO)

# Register Auth commands
cli.add_command(auth)

# Register Module commands
cli.add_command(init)
cli.add_command(build)
cli.add_command(publish)
cli.add_command(publish_status)
cli.add_command(validate)

# Register Dev commands
cli.add_command(dev)
cli.add_command(serve)
cli.add_command(test)
cli.add_command(run)

# Register keys
cli.add_command(keys)

def main():
    cli()

if __name__ == "__main__":
    main()
