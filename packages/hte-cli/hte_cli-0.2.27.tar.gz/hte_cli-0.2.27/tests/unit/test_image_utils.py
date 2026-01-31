"""Unit tests for hte_cli/image_utils.py."""

import subprocess
from unittest.mock import MagicMock, patch


from hte_cli.image_utils import (
    check_image_exists_locally,
    extract_images_from_compose,
    prepull_compose_images,
    pull_image_with_progress,
)


class TestExtractImagesFromCompose:
    """Tests for extract_images_from_compose."""

    def test_extracts_image_names(self):
        """Extracts all image names from services."""
        compose_yaml = """
services:
  default:
    image: jackpayne123/nyuctf-agent:v2
  db:
    image: postgres:15
  cache:
    image: redis:7-alpine
"""
        images = extract_images_from_compose(compose_yaml)
        assert len(images) == 3
        assert "jackpayne123/nyuctf-agent:v2" in images
        assert "postgres:15" in images
        assert "redis:7-alpine" in images

    def test_handles_missing_services(self):
        """Returns empty list for compose without services key."""
        compose_yaml = """
version: "3"
networks:
  default:
"""
        images = extract_images_from_compose(compose_yaml)
        assert images == []

    def test_handles_malformed_yaml(self):
        """Returns empty list for invalid YAML."""
        compose_yaml = "this is not: valid: yaml: {{{{"
        images = extract_images_from_compose(compose_yaml)
        assert images == []

    def test_handles_empty_yaml(self):
        """Returns empty list for empty/null YAML."""
        assert extract_images_from_compose("") == []
        assert extract_images_from_compose("null") == []

    def test_handles_services_without_image(self):
        """Skips services that use 'build:' instead of 'image:'."""
        compose_yaml = """
services:
  app:
    build: ./app
  db:
    image: postgres:15
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
"""
        images = extract_images_from_compose(compose_yaml)
        assert images == ["postgres:15"]

    def test_handles_empty_services(self):
        """Returns empty list when services dict is empty."""
        compose_yaml = "services: {}"
        images = extract_images_from_compose(compose_yaml)
        assert images == []

    def test_handles_services_with_null_config(self):
        """Handles services where config is null/None."""
        compose_yaml = """
services:
  app:
  db:
    image: postgres:15
"""
        images = extract_images_from_compose(compose_yaml)
        assert images == ["postgres:15"]


class TestCheckImageExistsLocally:
    """Tests for check_image_exists_locally."""

    @patch("subprocess.run")
    def test_returns_true_when_exists(self, mock_run):
        """True when docker inspect succeeds (returncode=0)."""
        mock_run.return_value = MagicMock(returncode=0)

        result = check_image_exists_locally("nginx:latest")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "docker" in call_args[0][0]
        assert "inspect" in call_args[0][0]
        assert "nginx:latest" in call_args[0][0]

    @patch("subprocess.run")
    def test_returns_false_when_not_exists(self, mock_run):
        """False when docker inspect fails."""
        mock_run.return_value = MagicMock(returncode=1)

        result = check_image_exists_locally("nonexistent:image")

        assert result is False

    @patch("subprocess.run")
    def test_returns_false_on_timeout(self, mock_run):
        """False when subprocess times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=10)

        result = check_image_exists_locally("nginx:latest")

        assert result is False

    @patch("subprocess.run")
    def test_returns_false_when_docker_missing(self, mock_run):
        """False when docker command not found."""
        mock_run.side_effect = FileNotFoundError("docker not found")

        result = check_image_exists_locally("nginx:latest")

        assert result is False


class TestPullImageWithProgress:
    """Tests for pull_image_with_progress (with PTY mocking)."""

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_calls_docker_pull(self, mock_openpty, mock_popen, mock_select, mock_read, mock_close):
        """Invokes correct docker pull command."""
        mock_openpty.return_value = (3, 4)  # master_fd, slave_fd

        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 0]  # Running, then done
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_select.return_value = ([], [], [])  # No data ready
        mock_read.return_value = b""

        result = pull_image_with_progress("nginx:latest")

        assert result is True
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["docker", "pull", "nginx:latest"]

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_progress_callback_receives_output(
        self, mock_openpty, mock_popen, mock_select, mock_read, mock_close
    ):
        """Progress callback called with output lines."""
        mock_openpty.return_value = (3, 4)

        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, None, 0]
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Simulate output
        mock_select.side_effect = [([3], [], []), ([3], [], []), ([], [], [])]
        mock_read.side_effect = [
            b"abc123: Pulling from library/nginx\r\n",
            b"abc123: Downloading  10MB/50MB\r\n",
            b"",
        ]

        progress_lines = []

        def on_progress(image, line):
            progress_lines.append((image, line))

        result = pull_image_with_progress("nginx:latest", on_progress=on_progress)

        assert result is True
        assert len(progress_lines) > 0
        assert progress_lines[0][0] == "nginx:latest"

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_returns_true_on_success(
        self, mock_openpty, mock_popen, mock_select, mock_read, mock_close
    ):
        """True when pull succeeds."""
        mock_openpty.return_value = (3, 4)

        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Immediate success
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_select.return_value = ([], [], [])

        result = pull_image_with_progress("nginx:latest")

        assert result is True

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_returns_false_on_failure(
        self, mock_openpty, mock_popen, mock_select, mock_read, mock_close
    ):
        """False when pull fails."""
        mock_openpty.return_value = (3, 4)

        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Failure
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        mock_select.return_value = ([], [], [])

        result = pull_image_with_progress("nonexistent:image")

        assert result is False

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_complete_callback_called(
        self, mock_openpty, mock_popen, mock_select, mock_read, mock_close
    ):
        """on_complete callback called with result."""
        mock_openpty.return_value = (3, 4)

        mock_process = MagicMock()
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_select.return_value = ([], [], [])

        complete_calls = []

        def on_complete(image, success):
            complete_calls.append((image, success))

        pull_image_with_progress("nginx:latest", on_complete=on_complete)

        assert len(complete_calls) == 1
        assert complete_calls[0] == ("nginx:latest", True)

    @patch("hte_cli.image_utils.pty.openpty")
    def test_returns_false_on_exception(self, mock_openpty):
        """False when exception raised."""
        mock_openpty.side_effect = OSError("PTY creation failed")

        complete_calls = []

        def on_complete(image, success):
            complete_calls.append((image, success))

        result = pull_image_with_progress("nginx:latest", on_complete=on_complete)

        assert result is False
        assert len(complete_calls) == 1
        assert complete_calls[0] == ("nginx:latest", False)


class TestPrepullComposeImages:
    """Tests for prepull_compose_images."""

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.check_image_exists_locally")
    def test_skips_cached_images(self, mock_check, mock_pull):
        """Skips images that are already cached."""
        mock_check.return_value = True  # All cached

        compose_yaml = """
services:
  app:
    image: nginx:latest
  db:
    image: postgres:15
"""
        complete_calls = []

        def on_complete(image, success, reason):
            complete_calls.append((image, success, reason))

        pulled, failed = prepull_compose_images(compose_yaml, on_image_complete=on_complete)

        assert pulled == 2
        assert failed == 0
        mock_pull.assert_not_called()  # No pulls needed
        assert all(c[2] == "cached" for c in complete_calls)

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.check_image_exists_locally")
    def test_pulls_missing_images(self, mock_check, mock_pull):
        """Pulls images that are not cached."""
        mock_check.return_value = False  # Not cached
        mock_pull.return_value = True  # Pull succeeds

        compose_yaml = """
services:
  app:
    image: nginx:latest
"""
        start_calls = []
        complete_calls = []

        def on_start(image, idx, total):
            start_calls.append((image, idx, total))

        def on_complete(image, success, reason):
            complete_calls.append((image, success, reason))

        pulled, failed = prepull_compose_images(
            compose_yaml,
            on_image_start=on_start,
            on_image_complete=on_complete,
        )

        assert pulled == 1
        assert failed == 0
        mock_pull.assert_called_once()
        assert start_calls[0] == ("nginx:latest", 1, 1)
        assert complete_calls[0] == ("nginx:latest", True, "pulled")

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.check_image_exists_locally")
    def test_counts_failed_pulls(self, mock_check, mock_pull):
        """Counts failed pull attempts."""
        mock_check.return_value = False
        mock_pull.return_value = False  # Pull fails

        compose_yaml = """
services:
  app:
    image: nonexistent:image
"""
        complete_calls = []

        def on_complete(image, success, reason):
            complete_calls.append((image, success, reason))

        pulled, failed = prepull_compose_images(compose_yaml, on_image_complete=on_complete)

        assert pulled == 0
        assert failed == 1
        assert complete_calls[0] == ("nonexistent:image", False, "failed")

    def test_handles_empty_compose(self):
        """Returns (0, 0) for compose with no images."""
        compose_yaml = "services: {}"

        pulled, failed = prepull_compose_images(compose_yaml)

        assert pulled == 0
        assert failed == 0

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.check_image_exists_locally")
    def test_mixed_cached_and_pulled(self, mock_check, mock_pull):
        """Handles mix of cached and pulled images."""
        # First image cached, second not
        mock_check.side_effect = [True, False]
        mock_pull.return_value = True

        compose_yaml = """
services:
  cached:
    image: nginx:latest
  new:
    image: postgres:15
"""
        pulled, failed = prepull_compose_images(compose_yaml)

        assert pulled == 2
        assert failed == 0
        mock_pull.assert_called_once()  # Only one pull
