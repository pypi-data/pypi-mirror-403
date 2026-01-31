"""Docker image utilities for pre-pulling compose images."""

import logging
import os
import pty
import re
import select
import subprocess
from collections.abc import Callable

import yaml

logger = logging.getLogger(__name__)


def extract_images_from_compose(compose_yaml: str) -> list[str]:
    """
    Extract Docker image names from a compose.yaml string.

    Args:
        compose_yaml: Docker Compose YAML content

    Returns:
        List of image names (e.g., ["jackpayne123/nyuctf-agent:v2", "ctf-game:latest"])
    """
    try:
        compose_data = yaml.safe_load(compose_yaml)
        if not compose_data or "services" not in compose_data:
            return []

        images = []
        for service_name, service_config in compose_data.get("services", {}).items():
            if isinstance(service_config, dict) and "image" in service_config:
                images.append(service_config["image"])
        return images
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse compose.yaml: {e}")
        return []


def extract_image_platforms_from_compose(compose_yaml: str) -> dict[str, str | None]:
    """
    Extract Docker image names and their platforms from a compose.yaml string.

    Args:
        compose_yaml: Docker Compose YAML content

    Returns:
        Dict mapping image names to their platform (or None if no platform specified)
    """
    try:
        compose_data = yaml.safe_load(compose_yaml)
        if not compose_data or "services" not in compose_data:
            return {}

        image_platforms = {}
        for service_name, service_config in compose_data.get("services", {}).items():
            if isinstance(service_config, dict) and "image" in service_config:
                image = service_config["image"]
                platform = service_config.get("platform")
                image_platforms[image] = platform
        return image_platforms
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse compose.yaml: {e}")
        return {}


def check_image_exists_locally(image: str) -> bool:
    """
    Check if a Docker image exists locally.

    Args:
        image: Image name (e.g., "jackpayne123/nyuctf-agent:v2")

    Returns:
        True if image exists locally, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def pull_image_with_progress(
    image: str,
    platform: str | None = None,
    on_progress: Callable[[str, str], None] | None = None,
    on_complete: Callable[[str, bool], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
) -> bool:
    """
    Pull a Docker image with progress callbacks using PTY for real progress output.

    Args:
        image: Image name to pull
        platform: Optional platform to pull (e.g., "linux/amd64")
        on_progress: Callback(image, status_line) called for each progress update
        on_complete: Callback(image, success) called when pull completes
        on_error: Callback(image, error_message) called when pull fails

    Returns:
        True if pull succeeded, False otherwise
    """
    try:
        # Use PTY to get real progress output from docker
        master_fd, slave_fd = pty.openpty()

        cmd = ["docker", "pull", image]
        if platform:
            cmd.extend(["--platform", platform])

        process = subprocess.Popen(
            cmd,
            stdout=slave_fd,
            stderr=slave_fd,
            stdin=slave_fd,
            close_fds=True,
        )

        os.close(slave_fd)  # Close slave in parent

        # Read output from master with timeout
        output_buffer = ""
        # Regex to parse docker progress: "abc123: Downloading [===>  ] 10.5MB/50MB"
        progress_pattern = re.compile(
            r"([a-f0-9]+):\s*(Downloading|Extracting|Verifying Checksum|Download complete|Pull complete|Already exists|Waiting)(?:\s+\[.*?\]\s+)?(\d+\.?\d*\s*[kMG]?B)?(?:/(\d+\.?\d*\s*[kMG]?B))?"
        )

        while True:
            # Check if process is done
            ret = process.poll()
            if ret is not None:
                # Read any remaining output
                try:
                    while True:
                        ready, _, _ = select.select([master_fd], [], [], 0.1)
                        if not ready:
                            break
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break
                except OSError:
                    pass
                break

            # Read available output
            try:
                ready, _, _ = select.select([master_fd], [], [], 0.1)
                if ready:
                    chunk = os.read(master_fd, 4096)
                    if chunk:
                        output_buffer += chunk.decode("utf-8", errors="replace")

                        # Parse and report progress
                        # Docker uses carriage returns to update lines in place
                        lines = output_buffer.replace("\r", "\n").split("\n")
                        output_buffer = lines[-1]  # Keep incomplete line

                        for line in lines[:-1]:
                            line = line.strip()
                            # Strip ANSI escape codes
                            line = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", line)
                            if line and on_progress:
                                on_progress(image, line)
            except OSError:
                break

        os.close(master_fd)
        success = process.returncode == 0

        if on_complete:
            on_complete(image, success)

        return success

    except (FileNotFoundError, OSError) as e:
        logger.error(f"Failed to pull {image}: {e}")
        if on_complete:
            on_complete(image, False)
        return False


def prepull_compose_images(
    compose_yaml: str,
    on_image_start: Callable[[str, int, int], None] | None = None,
    on_image_progress: Callable[[str, str], None] | None = None,
    on_image_complete: Callable[[str, bool, str], None] | None = None,
) -> tuple[int, int]:
    """
    Pre-pull all images from a compose.yaml file.

    Args:
        compose_yaml: Docker Compose YAML content
        on_image_start: Callback(image, current_idx, total) when starting an image
        on_image_progress: Callback(image, status_line) for pull progress
        on_image_complete: Callback(image, success, reason) when image completes

    Returns:
        Tuple of (images_pulled, images_failed)
    """
    images = extract_images_from_compose(compose_yaml)
    if not images:
        return (0, 0)

    pulled = 0
    failed = 0

    for idx, image in enumerate(images):
        # Check if already cached
        if check_image_exists_locally(image):
            if on_image_complete:
                on_image_complete(image, True, "cached")
            pulled += 1
            continue

        # Need to pull
        if on_image_start:
            on_image_start(image, idx + 1, len(images))

        success = pull_image_with_progress(
            image,
            on_progress=on_image_progress,
        )

        if success:
            if on_image_complete:
                on_image_complete(image, True, "pulled")
            pulled += 1
        else:
            if on_image_complete:
                on_image_complete(image, False, "failed")
            failed += 1

    return (pulled, failed)
