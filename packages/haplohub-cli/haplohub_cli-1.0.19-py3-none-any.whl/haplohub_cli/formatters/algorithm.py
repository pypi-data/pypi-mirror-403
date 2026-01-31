from haplohub import (
    AlgorithmSchema,
    PaginatedResponseAlgorithmSchema,
    ResultResponseAlgorithmSchema,
)
from rich.table import Table

from haplohub_cli.formatters import utils
from haplohub_cli.formatters.decorators import register


@register(AlgorithmSchema)
def format_algorithm(data: AlgorithmSchema):
    table = Table(title="Algorithm", caption=f"Id: {utils.format_id(data.id)}")
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Latest Version")
    table.add_row(utils.format_id(data.id), data.name, data.description)
    return table


@register(ResultResponseAlgorithmSchema)
def format_single_algorithm(data: ResultResponseAlgorithmSchema):
    return format_algorithm(data.result)


@register(PaginatedResponseAlgorithmSchema)
def format_algorithms(data: PaginatedResponseAlgorithmSchema):
    table = Table(title="Algorithms", caption=f"Total: {data.total_count}")
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Latest Version")
    table.add_column("Created")

    for item in data.items:
        table.add_row(
            utils.format_id(item.id),
            item.name,
            utils.truncate(item.description, 50),
            "%s (%s)" % (utils.format_id(item.latest_version.id), item.latest_version.version),
            utils.format_dt(item.created),
        )

    return table
