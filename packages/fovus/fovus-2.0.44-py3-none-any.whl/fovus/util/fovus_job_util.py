#
# job_util.py - Utilities for managing jobs

import time

from fovus.adapter.fovus_api_adapter import FovusApiAdapter
from fovus.constants.cli_constants import JOB_COMPLETED_STATUSES


class FovusJobUtil:
    @staticmethod
    def wait_for_job_until_completion(
        fovus_api_adapter: FovusApiAdapter,
        job_id: str,
        completion_statuses: list[str] = JOB_COMPLETED_STATUSES,
        check_interval: int = 60,
        max_retries: int = 3,
        timeout: int = None,
    ) -> str:
        is_timeout = False
        start_time = time.time()
        retries = 0
        job_current_status = None
        while retries <= max_retries and not is_timeout:
            job_current_status = fovus_api_adapter.get_job_current_status(job_id)

            if not job_current_status:
                retries += 1
                if retries > max_retries:
                    print(f"Job {job_id} status not found after {max_retries} retries.")
                    break
            elif job_current_status in completion_statuses:
                print(f"Job {job_id} completed with status: {job_current_status}")
                break
            else:
                print(f"Job {job_id} is still running with status: {job_current_status}")

            time.sleep(check_interval)

            current_time = time.time()
            is_timeout = timeout is not None and current_time - start_time > timeout
            if is_timeout:
                print(f"Timeout reached while waiting for job {job_id} to complete after {timeout} seconds.")
                break

        return job_current_status
