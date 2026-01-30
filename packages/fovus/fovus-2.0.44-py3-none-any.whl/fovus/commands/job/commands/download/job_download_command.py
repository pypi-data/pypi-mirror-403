import click
from typing_extensions import Tuple, Union

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.adapter.fovus_s3_adapter import FovusS3Adapter
from fovus.constants.cli_constants import JOB_COMPLETED_STATUSES
from fovus.util.file_util import FileUtil
from fovus.util.fovus_job_util import FovusJobUtil
from fovus.util.util import Util


@click.command("download")
@click.argument("job_directory", type=str)
@click.option(
    "--job-id",
    type=str,
    help=(
        "The ID of the job to download files from. This is only required if JOB_DIRECTORY has not been initialized by"
        " the Fovus CLI."
    ),
)
@click.option(
    "--include-paths",
    "include_paths_tuple",
    metavar="include_paths",
    type=str,
    multiple=True,
    help=r"""
        Relative path(s) to files or folders inside the JOB_DIRECTORY to download.

        Paths support Unix shell-style wildcards, unless the --range option is used.
        When downloading a byte range, only one explicit file path may be provided,
        and wildcards are not supported.

        You can only provide either --include-paths or --exclude-paths, not both.

        Supported wildcards:
        \* - matches any number of characters
        ? - matches any single character

        E.g. taskName/out?/\*.txt matches any .txt file in folders taskName/out1, taskName/out2, etc.

        E.g. taskName???/folder/file.txt matches taskName001/folder/file.txt, taskName123/folder/file.txt, etc.

        To specify multiple paths, this option may be provided multiple times or deliminated by a comma (``,``). To escape a comma, use two commas (``,,``).

        E.g. --include-paths "path1" --include-paths "path2"

        E.g. --include-paths "path1,path2"
        """,
)
@click.option(
    "--exclude-paths",
    "exclude_paths_tuple",
    metavar="exclude_paths",
    type=str,
    multiple=True,
    help=r"""
        The relative paths to files or folders inside the JOB_DIRECTORY that will not be downloaded. Paths are provided with support for Unix shell-style wildcards.

        You can only provide either --include-paths or --exclude-paths, not both.
        This option is not supported when downloading an exact byte range of a file.

        Supported wildcards:
        \* - matches any number of characters
        ? - matches any single character

        E.g. taskName/out?/\*.txt matches any .txt file in folders taskName/out1, taskName/out2, etc.

        E.g. taskName???/folder/file.txt matches taskName001/folder/file.txt, taskName123/folder/file.txt, etc.

        To specify multiple paths, this option may be provided multiple times or deliminated by a comma (``,``). To escape a comma, use two commas (``,,``).

        E.g. --exclude-paths "path1" --exclude-paths "path2"

        E.g. --exclude-paths "path1,path2"
        """,
)
@click.option(
    "--range",
    metavar="byte_range",
    type=str,
    help=(
        'The bytes range of the file to download. For example, --range="0-1024" downloads the first 1025 bytes'
        " (positions 0 through 1024). This option is only supported when downloading a single file."
    ),
)
@click.option(
    "--wait-until-status-is",
    "wait_until_status_tuple",
    metavar="JOB_STATUS",
    type=str,
    multiple=True,
    help=" ".join(
        [
            "Wait until the job reaches the specified status(es) before downloading the files.\n\n",
            "Valid job statuses are:\n\n",
            f"{', '.join(JOB_COMPLETED_STATUSES)}\n\n",
            "To specify multiple statuses, this option may be provided multiple times or deliminated by a comma (``,``).\n\n",
            'E.g. --wait-until-status-is "Completed" --wait-until-status-is "Walltime Reached"\n\n',
            'E.g. --wait-until-status-is "Completed,Walltime Reached"\n\n',
            "If job completes with a status other than the specified statuses, the command will exit and no files will be downloaded.\n",
        ]
    ),
)
def job_download_command(
    job_id: Union[str, None],
    job_directory: str,
    include_paths_tuple: Tuple[str, ...],
    exclude_paths_tuple: Tuple[str, ...],
    range: Union[str, None],
    wait_until_status_tuple: Tuple[str, ...],
):
    """
    Download job files from Fovus Storage.

    Only new or updated files will be downloaded. If the job is running,
    the files will be synced to Fovus Storage before being downloaded.

    JOB_DIRECTORY is the directory where the files will be downloaded.
    """
    job_id = FileUtil.get_job_id(job_id, job_directory)

    include_paths = Util.parse_include_exclude_paths(include_paths_tuple)
    exclude_paths = Util.parse_include_exclude_paths(exclude_paths_tuple)
    completion_statuses = parse_wait_until_status_tuple(wait_until_status_tuple)

    if range:
        if not include_paths or len(include_paths) == 0:
            raise ValueError("When downloading a byte range, an explicit file path must be provided.")
        elif len(include_paths) > 1 or exclude_paths:
            raise ValueError("When downloading a byte range, only one file path is allowed.")

    print("Authenticating...")
    fovus_api_adapter = FovusApiAdapter()
    if completion_statuses:
        print(
            f"Waiting for job to reach one of the following statuses before downloading files: {', '.join(completion_statuses)}..."
        )
        job_latest_status = FovusJobUtil.wait_for_job_until_completion(
            fovus_api_adapter, job_id, completion_statuses=completion_statuses
        )

        if job_latest_status not in completion_statuses:
            raise RuntimeError(
                f"Job completed with status {job_latest_status}, which is not one of the specified completion statuses: {', '.join(completion_statuses)}. "
                "No files will be downloaded."
            )

        print(f"Downloading job files...")

    fovus_s3_adapter = FovusS3Adapter(
        fovus_api_adapter,
        root_directory_path=job_directory,
        job_id=job_id,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    )
    fovus_api_adapter.sync_job_files(job_id, include_paths, exclude_paths)
    fovus_s3_adapter.download_files(byte_range=range)


def parse_wait_until_status_tuple(wait_until_status_tuple: Tuple[str, ...]) -> list[str]:
    user_input_values = list(wait_until_status_tuple)
    all_statuses: list[str] = []

    for input_value in user_input_values:
        statuses = input_value.split(",")
        for status in statuses:
            if status.strip():
                all_statuses.append(status.strip())

    # Remove duplicates and empty strings
    all_statuses = list(set(all_statuses))

    if any(status not in JOB_COMPLETED_STATUSES for status in all_statuses):
        invalid_statuses = [status for status in all_statuses if status not in JOB_COMPLETED_STATUSES]
        raise ValueError(
            f"One or more invalid job statuses were provided: {', '.join(invalid_statuses)}. Valid job statuses are: {', '.join(JOB_COMPLETED_STATUSES)}"
        )

    return all_statuses
