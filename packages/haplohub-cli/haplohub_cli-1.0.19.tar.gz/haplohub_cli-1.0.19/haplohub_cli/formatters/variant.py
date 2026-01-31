from haplohub import ResultListResponseHgvsSchema, ResultListResponseVariantSchema
from rich.table import Table

from haplohub_cli.formatters.decorators import register


@register(ResultListResponseVariantSchema)
def format_variants(data: ResultListResponseVariantSchema):
    table = Table(title="Variants", caption=f"Total: {len(data.items)}")
    table.add_column("Accession")
    table.add_column("Position")
    table.add_column("Id")
    table.add_column("Reference")
    table.add_column("Alternate")
    table.add_column("Quality")

    for item in data.items:
        table.add_row(
            item.accession,
            str(item.position),
            item.id,
            item.reference,
            ", ".join(item.alternate),
            f"{item.quality:.4f}" if item.quality else "N/A",
        )

    return table


@register(ResultListResponseHgvsSchema)
def format_hgvs(data: ResultListResponseHgvsSchema):
    table = Table(title="HGVS", caption=f"Total: {len(data.items)}")
    table.add_column("HGVS")
    table.add_column("Is called")
    table.add_column("Dosage")
    table.add_column("Error")

    for item in data.items:
        error = "" if item.error_message is None else f"[red]{item.error_message}[/red]"
        is_called = "" if item.is_called is None else f"[green]{item.is_called}[/green]"
        dosage = "" if item.dosage is None else f"[blue]{item.dosage}[/blue]"
        table.add_row(item.hgvs, is_called, dosage, error)

    return table
