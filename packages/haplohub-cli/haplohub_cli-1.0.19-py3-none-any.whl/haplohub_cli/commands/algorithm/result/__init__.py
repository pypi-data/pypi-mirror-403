import json
from typing import Optional

import click
from haplohub import CreateAlgorithmResultRequest

from haplohub_cli.core.api.client import client


@click.group()
def result():
    """
    Manage algorithm results
    """
    pass


@result.command()
def list(algorithm_version_id: Optional[str] = None, cohort_id: Optional[str] = None):
    return client.algorithm_result.list_algorithm_results(
        algorithm_version_id=algorithm_version_id,
        cohort_id=cohort_id,
    )


@result.command()
@click.argument("id")
def get(id):
    return client.algorithm_result.get_algorithm_result(id)


@result.command()
@click.option("--algorithm-version", "-a", type=click.STRING, required=True, help="The ID of the algorithm version")
@click.option("--cohort", "-c", type=click.STRING, required=True, help="The ID of the cohort")
@click.option("--input-json", "-i", type=click.STRING, required=False, help="The input JSON")
@click.option("--input-file", "-f", type=click.STRING, required=False, help="The input file")
def create(algorithm_version: str, cohort: str, input_json: Optional[str] = None, input_file: Optional[str] = None):
    if input_json is None and input_file is None:
        raise click.ClickException("Either --input-json or --input-file must be provided")

    if input_json is not None and input_file is not None:
        raise click.ClickException("Only one of --input-json or --input-file can be provided")

    if input_json is not None:
        input_data = json.loads(input_json)
    else:
        with open(input_file, "r") as f:
            input_data = json.load(f)

    request = CreateAlgorithmResultRequest(
        algorithm_version_id=algorithm_version,
        cohort_id=cohort,
        input=input_data,
    )

    result = client.algorithm_result.create_algorithm_result(request)

    return result
