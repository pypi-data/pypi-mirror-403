"""
Video playback functionality for yt-mpv
"""

import logging
import shutil

from yt_mpv.utils.fs import run_command
from yt_mpv.utils.notify import notify

# Configure logging
logger = logging.getLogger("yt-mpv")


def is_installed() -> bool:
    """Check if mpv is installed."""
    return shutil.which("mpv") is not None


def play(url: str, additional_args: list = None) -> bool:
    """Play a video with mpv."""
    if not is_installed():
        logger.error("mpv is not installed")
        notify("mpv not found. Please install it.")
        return False

    # Build mpv command
    cmd = [
        "mpv",
        "--ytdl=yes",
        f"--term-status-msg=Playing: {url}",
    ]

    # Add additional args if provided
    if additional_args:
        cmd.extend(additional_args)

    # Add the URL
    cmd.append(url)

    # Run mpv
    status, _, stderr = run_command(
        cmd,
        desc=f"Playing {url} with mpv",
        check=False,
    )

    if status != 0:
        logger.error(f"Failed to play video: {stderr}")
        notify("Failed to play video")
        return False

    return True
