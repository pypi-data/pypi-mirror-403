"""
Utility module for managing AWS credentials file operations.

Handles merging and removing the [fovus-storage] profile while preserving other profiles.
"""
from typing import List, Tuple

from fovus.util.logger import get_fovus_logger

logger = get_fovus_logger()

FOVUS_PROFILE_NAME = "[fovus-storage]"


def get_profiles_from_content(content: str) -> List[str]:
    """
    Extract all profile names from AWS credentials content.

    Returns the list of profile names (e.g., ['[default]', '[production]'])
    """
    return [line.strip() for line in content.split("\n") if line.strip().startswith("[") and line.strip().endswith("]")]


def remove_profile_from_content(content: str, profile_name: str) -> str:
    """
    Remove a specific profile section from AWS credentials content.

    Returns the updated content with the profile removed.
    """
    lines = content.split("\n")
    new_lines = []
    skip_section = False

    for line in lines:
        stripped = line.strip()
        # Check if we're entering the target profile section
        if stripped == profile_name:
            skip_section = True
            continue
        # Check if we're entering a different profile section
        if stripped.startswith("[") and stripped.endswith("]"):
            skip_section = False

        # Only add lines that are not part of the target profile section
        if not skip_section:
            new_lines.append(line)

    # Clean up trailing empty lines
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()

    # Reconstruct content
    updated_content = "\n".join(new_lines)
    if updated_content and not updated_content.endswith("\n"):
        updated_content += "\n"

    return updated_content


def merge_fovus_profile(new_fovus_credentials: str, existing_content: str = "") -> str:
    """
    Merge the [fovus-storage] profile with existing AWS credentials content.

    Preserves existing profiles and removes old fovus-storage profile if it exists.
    Returns the updated credentials content with fovus-storage profile added/updated.
    """
    # Check if old profile exists
    existing_profiles = get_profiles_from_content(existing_content)
    found_old_profile = FOVUS_PROFILE_NAME in existing_profiles

    if found_old_profile:
        logger.debug("Removing old [fovus-storage] profile and replacing with new credentials")
        # Remove old fovus-storage profile
        updated_content = remove_profile_from_content(existing_content, FOVUS_PROFILE_NAME)
    else:
        updated_content = existing_content

    # Clean up trailing empty lines
    updated_content = updated_content.rstrip("\n")

    # Add fovus-storage profile at the end
    if updated_content:
        updated_content += "\n\n"
    updated_content += new_fovus_credentials

    return updated_content


def remove_fovus_profile(existing_content: str) -> Tuple[str, bool]:
    """
    Remove the [fovus-storage] profile from AWS credentials content.

    Returns the tuple of (updated_content, was_removed) where updated_content is the
    content with fovus-storage profile removed, and was_removed indicates if the profile
    was found and removed.
    """
    existing_profiles = get_profiles_from_content(existing_content)
    has_fovus_profile = FOVUS_PROFILE_NAME in existing_profiles

    if not has_fovus_profile:
        return existing_content, False

    logger.debug("Found %d profile(s) in credentials file", len(existing_profiles))

    # Remove fovus-storage profile
    updated_content = remove_profile_from_content(existing_content, FOVUS_PROFILE_NAME)

    # Count remaining profiles
    remaining_profiles = get_profiles_from_content(updated_content)

    logger.debug("Removed [fovus-storage] profile from credentials file")
    if remaining_profiles:
        logger.debug("Preserved %d existing profile(s): %s", len(remaining_profiles), ", ".join(remaining_profiles))
    else:
        logger.debug("No other AWS profiles remain in credentials file")

    return updated_content, True
