from haplohub import (
    PaginatedResponseSampleSchema,
    ResultResponseSampleSchema,
    SampleSchema,
)
from rich.table import Table

from haplohub_cli.formatters import utils
from haplohub_cli.formatters.decorators import register


@register(SampleSchema)
def format_sample(data: SampleSchema):
    table = Table(title="Sample", caption=f"Id: {utils.format_id(data.id)}")
    table.add_column("Id")
    table.add_column("Sample ID")
    table.add_column("Member ID")
    table.add_column("Created")
    table.add_row(utils.format_id(data.id), data.sample_id, utils.format_id(data.member_id), utils.format_dt(data.created))
    return table


@register(PaginatedResponseSampleSchema)
def format_samples(data: PaginatedResponseSampleSchema):
    table = Table(title="Samples", caption=f"Total: {data.total_count}")
    table.add_column("Id")
    table.add_column("Sample ID")
    table.add_column("Member ID")
    table.add_column("Created")

    for item in data.items:
        table.add_row(utils.format_id(item.id), item.sample_id, utils.format_id(item.member_id), utils.format_dt(item.created))

    return table


@register(ResultResponseSampleSchema)
def format_create_sample(data: ResultResponseSampleSchema):
    return format_sample(data.result)
