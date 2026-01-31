import click

from haplohub_cli.core.api.client import client

from . import result


@click.group()
def algorithm():
    """
    Manage algorithms
    """
    pass


@algorithm.command()
def list():
    return client.algorithm.list_algorithms()


@algorithm.command()
@click.argument("id")
def get(id):
    return client.algorithm.get_algorithm(id)


algorithm.add_command(result.result)
