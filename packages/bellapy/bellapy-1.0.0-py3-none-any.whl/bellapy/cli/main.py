"""Main CLI entry point for bellapy"""

import click
from bellapy.cli import data_cli


@click.group()
@click.version_option(version="1.0.0", prog_name="bellapy")
def cli():
    """
    bellapy: The ML Data Toolkit You Wish Existed

    29 features for dataset processing, cleaning, and preparation.
    """
    pass


# Register subcommands
cli.add_command(data_cli.data)


if __name__ == "__main__":
    cli()
