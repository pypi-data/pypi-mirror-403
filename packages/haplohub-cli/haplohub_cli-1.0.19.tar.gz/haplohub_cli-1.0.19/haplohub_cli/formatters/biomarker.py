from haplohub import (
    ResultListResponseBiomarkerResultSchema,
)
from rich.table import Table

from haplohub_cli.formatters import utils
from haplohub_cli.formatters.decorators import register


@register(ResultListResponseBiomarkerResultSchema)
def format_biomarker_result(data: ResultListResponseBiomarkerResultSchema):
    table = Table(title="Biomarker results", caption=f"Total: {len(data.items)}")
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("Lab")
    table.add_column("Result #")

    for item in data.items:
        table.add_row(utils.format_id(item.order.id), item.order.patient, item.order.laboratory, str(len(item.results)))

    return table
