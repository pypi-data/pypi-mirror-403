import logging
import subprocess
import typing as t
from pathlib import Path

import click

from cratedb_fivetran_destination.util import setup_logging

logger = logging.getLogger()


# Check for recent releases:
# https://console.cloud.google.com/artifacts/docker/build-286712/us/public-docker-us/sdktesters-v2%2Fsdk-tester?pli=1

SDK_TESTER_OCI = (
    "us-docker.pkg.dev/build-286712/public-docker-us/sdktesters-v2/sdk-tester:2.26.0113.001"
)


def get_sdk_tester_command(directory: t.Union[Path, str]) -> str:
    return f"""
    docker run --rm \
        --mount type=bind,source="{directory}",target=/data \
        -a STDIN -a STDOUT -a STDERR \
        -e WORKING_DIR="{directory}" \
        -e GRPC_HOSTNAME=host.docker.internal \
        --network=host \
        --add-host=host.docker.internal:host-gateway \
        {SDK_TESTER_OCI} \
        --tester-type destination \
        --port 50052
    """


@click.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True, path_type=Path),
    required=True,
    help="Directory containing test data",
)
def cli(directory: Path) -> None:  # pragma: nocover
    setup_logging()
    logger.info(f"Starting Fivetran SDK tester on directory: {directory}")
    subprocess.check_call(get_sdk_tester_command(directory=directory))  # noqa: S603
