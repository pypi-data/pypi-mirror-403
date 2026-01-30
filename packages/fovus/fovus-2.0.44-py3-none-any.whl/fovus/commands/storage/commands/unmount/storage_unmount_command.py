import logging
import os
import subprocess  # nosec

import click

from fovus.constants.cli_constants import PATH_TO_CONFIG_ROOT
from fovus.util.aws_credentials_util import remove_fovus_profile
from fovus.util.util import Util

logger = logging.getLogger(__name__)


def _remove_fovus_profile_from_credentials_unix():
    """Remove the [fovus-storage] profile from AWS credentials file on Unix systems."""
    logger.debug("Cleaning up AWS credentials")
    credentials_file_path = os.path.expanduser("~/.aws/credentials")

    if not os.path.exists(credentials_file_path):
        logger.debug("No AWS credentials file found, skipping cleanup")
        return

    with open(credentials_file_path, encoding="utf-8") as file:
        existing_content = file.read()

    updated_content, was_removed = remove_fovus_profile(existing_content)

    if not was_removed:
        logger.debug("No [fovus-storage] profile found in credentials file")
        return

    # Write back the updated content
    with open(credentials_file_path, "w", encoding="utf-8") as file:
        file.write(updated_content)


def _remove_fovus_profile_from_credentials_wsl():
    """Remove the [fovus-storage] profile from AWS credentials file in WSL."""
    logger.debug("Cleaning up AWS credentials (WSL)")

    # Read current credentials from WSL
    result = subprocess.run(
        [
            "wsl",
            "-d",
            "Fovus-Ubuntu",
            "-u",
            "root",
            "bash",
            "-c",
            "cat ~/.aws/credentials 2>/dev/null || echo ''",
        ],
        capture_output=True,
        text=True,
        check=False,
    )  # nosec

    existing_content = result.stdout

    if not existing_content.strip():
        logger.debug("No AWS credentials file found in WSL, skipping cleanup")
        return

    updated_content, was_removed = remove_fovus_profile(existing_content)

    if not was_removed:
        logger.debug("No [fovus-storage] profile found in WSL credentials file")
        return

    # Write back the updated content to WSL
    # Escape single quotes for bash
    escaped_credentials = updated_content.replace("'", "'\\''")
    subprocess.run(  # nosec
        [
            "wsl",
            "-d",
            "Fovus-Ubuntu",
            "-u",
            "root",
            "bash",
            "-c",
            f"echo '{escaped_credentials}' > ~/.aws/credentials",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


@click.command("unmount")
def storage_unmount_command():
    """Unmount Fovus Storage from your computer."""
    if Util.is_windows() or Util.is_unix():
        _unmount_storage()
    else:
        print(f"Fovus unmount storage is not available for your OS ({os.name}).")


def _unmount_storage():
    print("Unmounting Fovus Storage...")
    mount_storage_path = "/fovus-storage/"
    mounted_storage_script_path = os.path.join(os.path.expanduser(PATH_TO_CONFIG_ROOT), "mount_storage.path")
    if os.path.exists(mounted_storage_script_path):
        with open(mounted_storage_script_path, encoding="utf-8") as file:
            mount_storage_path = file.read().strip()

    if Util.is_windows():
        drive_name = "M"
        mounted_drive_script_path = os.path.join(os.path.expanduser(PATH_TO_CONFIG_ROOT), "mount_storage.drive")
        old_mounted_drive_script_path = os.path.join(os.path.expanduser(PATH_TO_CONFIG_ROOT), "mounted_drive.txt")
        if os.path.exists(mounted_drive_script_path):
            with open(mounted_drive_script_path, encoding="utf-8") as file:
                drive_name = file.read().strip()
        # Todo: Remove this after 2 months
        elif os.path.exists(old_mounted_drive_script_path):
            with open(old_mounted_drive_script_path, encoding="utf-8") as file:
                drive_name = file.read().strip()
        current_dir = os.getcwd()
        if current_dir and current_dir.startswith(f"{drive_name}:"):
            print("Current directory:", current_dir)
            print(
                f"Unmounting Fovus Storage cannot be performed under {drive_name}:\\. "
                f"This command must be issued from a path outside {drive_name}:\\. "
            )
            return
        error_count = 0
        for mount_dir in ["files", "jobs"]:
            result = subprocess.run(
                [
                    "wsl",
                    "-d",
                    "Fovus-Ubuntu",
                    "-u",
                    "root",
                    "bash",
                    "-c",
                    f"umount {mount_storage_path}{mount_dir}",
                ],
                capture_output=True,
                text=True,
                check=False,
                shell=True,
            )  # nosec
            if result.stderr:
                if "target is busy" in result.stderr.strip():
                    error_count += 1
                    print("Mount point is busy!")

        if error_count > 0:
            return

        subprocess.run(  # nosec
            [
                "wsl",
                "-d",
                "Fovus-Ubuntu",
                "-u",
                "root",
                "bash",
                "-c",
                "sudo rm /etc/profile.d/fovus-storage-init.sh",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        # Remove only the fovus-storage profile from credentials file
        _remove_fovus_profile_from_credentials_wsl()

        subprocess.run(  # nosec
            'schtasks /delete /tn "FovusMountStorageRefresh" /f',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=True,
        )

        launch_wsl_script_path = os.path.join(os.path.expanduser(PATH_TO_CONFIG_ROOT), "launch_wsl.vbs")
        subprocess.run(  # nosec
            f'del "{launch_wsl_script_path}"',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=True,
        )

        startup_folder = os.path.join(
            os.getenv("APPDATA"),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
            "Startup",
        )  # Use Win + R -> shell:startup
        mount_fovus_storage_script_path = os.path.join(startup_folder, "mount_fovus_storage.vbs")
        subprocess.run(  # nosec
            f'del "{mount_fovus_storage_script_path}"',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=True,
        )

        subprocess.run(  # nosec
            f"net use {drive_name}: /delete /persistent:yes",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=True,
        )
        subprocess.run(  # nosec
            f"powershell NET USE {drive_name}: /DELETE",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=True,
        )
        print("Fovus Storage successfully unmounted!")
    elif Util.is_unix():
        error_count = 0
        for mount_dir in ["files", "jobs"]:
            result = subprocess.run(
                f"sudo umount {mount_storage_path}{mount_dir}",
                capture_output=True,
                text=True,
                check=False,
                shell=True,
            )  # nosec
            if result.stderr:
                print(result.stderr.strip())
                if "target is busy" in result.stderr.strip():
                    error_count += 1
                    print("Mount point is busy!")

        if error_count > 0:
            return
        os.system("atq | cut -f 1 | xargs atrm > /dev/null 2>&1")  # nosec
        os.system("sudo rm /etc/profile.d/fovus-storage-init.sh > /dev/null 2>&1")  # nosec
        # Remove only the fovus-storage profile from credentials file
        _remove_fovus_profile_from_credentials_unix()
        print("Fovus Storage successfully unmounted!")
