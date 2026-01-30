import click
from typing_extensions import Union

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.constants.cli_action_runner_constants import GENERIC_SUCCESS, OUTPUTS
from fovus.constants.cli_constants import JOB_COMPLETED_STATUSES
from fovus.util.file_util import FileUtil
from fovus.util.fovus_job_util import FovusJobUtil


@click.command("status")
@click.option("--job-id", type=str, help="The ID of the job whose status will be retrieved.")
@click.option(
    "--job-directory",
    type=str,
    help=(
        "The directory of the job whose status will be fetched. The job directory must be initialized by the Fovus CLI."
    ),
)
@click.option("--wait", is_flag=True, help="\n".join([
    "Check the job status every 60 seconds until the job finishes with one of the following statuses:\n",
    f"{', '.join(JOB_COMPLETED_STATUSES)}\n",
    "Once the job completes, the latest job status will be returned.\n",
]))
@click.option("--exit-on-non-complete", is_flag=True, help="""
    This option is useful for building a simple workflow with Fovus CLI. When enabled, exit with a non-zero status code if the job status is not ``Completed``.
    
    Effectively, subsequent commands will not be executed.
""")
def job_status_command(job_id: Union[str, None], job_directory: Union[str, None], wait: bool = False, exit_on_non_complete: bool = False):
    """
    Get a job's status.

    Either --job-id or --job-directory is required.
    """
    job_id = FileUtil.get_job_id(job_id, job_directory)

    print("Getting job current status...")
    fovus_api_adapter = FovusApiAdapter()
    job_current_status = None
    if wait:
        job_current_status = FovusJobUtil.wait_for_job_until_completion(fovus_api_adapter, job_id, completion_statuses=JOB_COMPLETED_STATUSES)
    else:
        job_current_status = fovus_api_adapter.get_job_current_status(job_id)

    if exit_on_non_complete and job_current_status != "Completed":
        raise RuntimeError(f'Job {job_id} did not finish with "Completed". Exiting with non-zero status code.')

    print(GENERIC_SUCCESS)
    print(OUTPUTS)
    print("\n".join(("Job ID", job_id, "Job current status:", job_current_status)))
