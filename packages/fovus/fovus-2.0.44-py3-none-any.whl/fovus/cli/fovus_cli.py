#!/usr/bin/env python3
import logging
import os
import sys
import time
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as importlib_version

import click
import requests
from packaging import version

from fovus.adapter.fovus_cognito_adapter import FovusCognitoAdapter
from fovus.cli.ssl import configure_ssl_env
from fovus.commands.auth.auth_command import auth_command
from fovus.commands.config.config_command import config_command
from fovus.commands.job.job_command import job_command
from fovus.commands.pipeline.pipeline_command import pipeline_command
from fovus.commands.projects.projects_command import projects_command
from fovus.commands.storage.storage_command import storage_command
from fovus.commands.storage_cached.storage_cached_command import storage_cached_command
from fovus.commands.task.task_command import task_command
from fovus.config.config import Config
from fovus.util.logger import get_fovus_logger, setup_fovus_logger

# By default, boto3 runs through credential provider chain to find the credentials and AWS-related configurations.
# This add 2-3 seconds overhead time at start up for the boto3's clients.
# Since we use boto3 for simple operations on users machines and no AWS credentials configuration is needed,
# we disable this behavior for faster CLI response time.
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"

OK_RETURN_STATUS = 0
ERROR_RETURN_STATUS = 1

logger = get_fovus_logger()

def _confirm_latest_version():
    try:
        response = requests.get("https://pypi.org/pypi/fovus/json", timeout=5)
        data = response.json()
        latest_version = data["info"]["version"]
    except (requests.RequestException, KeyError):
        logger.info("Unable to check for latest version.")
        return

    try:
        current_version = importlib_version("fovus")
    except PackageNotFoundError:
        logger.info("Unable to check for latest version.")
        return

    if version.parse(current_version) < version.parse(latest_version):
        logger.info(
            "===================================================\n"
            + f"  A new version of Fovus CLI ({latest_version}) is available.\n"
            + f"  Your current version is {current_version}\n"
            + "  Update using: pip install --upgrade fovus\n"
            + "==================================================="
        )


@click.group()
@click.option(
    "--silence",
    "-s",
    "_silence",
    is_flag=True,
    type=bool,
    help="Disable interactive CLI prompts and automatically dismiss warnings.",
)
@click.option(
    "--nextflow",
    "-nf",
    "_nextflow",
    is_flag=True,
    type=bool,
    help="Enable for nextflow job submission.",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    type=bool,
    help="Enable additional logs for debugging purposes.",
)
@click.option(
    "--log",
    "-l",
    type=str,
    help="Path to a file for saving CLI runtime logs.",
)
def cli(
    _silence: bool,
    _nextflow: bool,
    debug: bool,
    log: str,
):
    configure_ssl_env()
    setup_fovus_logger(is_debug=debug, log_path=log)

    _confirm_latest_version()

    is_gov = FovusCognitoAdapter.get_is_gov()
    Config.set_is_gov(is_gov)


cli.add_command(auth_command)
cli.add_command(storage_command)
cli.add_command(job_command)
cli.add_command(projects_command)
cli.add_command(config_command)
cli.add_command(pipeline_command)
cli.add_command(task_command)
cli.add_command(storage_cached_command)


def main() -> int:
    try:
        # pylint: disable=no-value-for-parameter
        cli()
        return OK_RETURN_STATUS
    except Exception as exc:  # pylint: disable=broad-except
        print(exc)
        logger.error("An unhandled exception occurred in main.")
        logger.exception(exc)
        return ERROR_RETURN_STATUS


if __name__ == "__main__":
    sys.exit(main())
