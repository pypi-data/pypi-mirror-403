import click

from haplohub_cli.config.config_manager import config_manager


@click.group()
def config():
    """
    Manage configuration
    """
    pass


@config.command()
def show():
    return config_manager.config


@config.command()
@click.argument("key")
@click.argument("value")
def set(key, value):
    setattr(config_manager.config, key, value)
    config_manager.save()
    return config_manager.config


@config.command()
@click.argument("api_url", type=click.STRING)
def switch(api_url):
    config_manager.switch_environment(api_url)
    return config_manager.config


@config.command()
def reset():
    config_manager.reset()
    config_manager.save()
    return config_manager.config
