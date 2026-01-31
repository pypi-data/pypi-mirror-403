import json

from haplohub import (
    AlgorithmResultSchema,
    PaginatedResponseAlgorithmResultSchema,
    ResultResponseAlgorithmResultSchema,
)
from rich.syntax import Syntax
from rich.table import Table

from haplohub_cli.formatters import utils
from haplohub_cli.formatters.decorators import register


@register(AlgorithmResultSchema)
def format_algorithm_result(data: AlgorithmResultSchema):
    table = Table(title="Algorithm Result", caption=f"Id: {utils.format_id(data.id)}")
    table.add_column("Id")
    table.add_column("Status")
    table.add_column("Input")
    table.add_column("Output")
    table.add_column("Created")
    table.add_column("Modified")
    table.add_row(
        utils.format_id(data.id),
        data.status,
        Syntax(json.dumps(data.input, indent=2), "json") if data.input else "N/A",
        Syntax(json.dumps(data.output, indent=2), "json") if data.output else "N/A",
        utils.format_dt(data.created),
        utils.format_dt(data.modified),
    )
    return table


@register(ResultResponseAlgorithmResultSchema)
def format_single_algorithm_result(data: ResultResponseAlgorithmResultSchema):
    return format_algorithm_result(data.result)


@register(PaginatedResponseAlgorithmResultSchema)
def format_algorithm_results(data: PaginatedResponseAlgorithmResultSchema):
    table = Table(title="Algorithm Results", caption=f"Total: {data.total_count}")
    table.add_column("Id")
    table.add_column("Status")
    table.add_column("Created")
    table.add_column("Modified")

    for item in data.items:
        table.add_row(
            utils.format_id(item.id),
            item.status,
            utils.format_dt(item.created),
            utils.format_dt(item.modified),
        )

    return table
