import click

from fovus.commands.storage_cached.commands.mount.storage_cached_mount_command import (
    storage_cached_mount_command,
)


@click.group("storage-cached")
def storage_cached_command():
    """Contains commands related to storage-cached."""


storage_cached_command.add_command(storage_cached_mount_command)
