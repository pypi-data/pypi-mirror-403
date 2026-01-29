"""Tests for the CLI module."""

import json
import os
import subprocess
import sys
from pathlib import Path


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_help_flag(self):
        """Test that --help shows usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "openapi_ts_client.cli", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "openapi-ts-client" in result.stdout.lower() or "usage" in result.stdout.lower()
        assert "--format" in result.stdout
        assert "--output" in result.stdout

    def test_version_flag(self):
        """Test that --version shows version."""
        result = subprocess.run(
            [sys.executable, "-m", "openapi_ts_client.cli", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Version should be in stdout or stderr (argparse puts it in different places)
        output = result.stdout + result.stderr
        assert "1.1.2" in output or "openapi-ts-client" in output.lower()


class TestFileInput:
    """Test file input handling."""

    def test_generate_from_file(self, tmp_path: Path):
        """Test generating client from a file."""
        output_dir = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "tests/fixtures/petstore/openapi.json",
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output_dir.exists()
        assert (output_dir / "index.ts").exists()

    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "nonexistent.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


class TestURLInput:
    """Test URL input handling."""

    def test_detect_url(self):
        """Test that URLs are detected correctly."""
        from openapi_ts_client.cli import is_url

        assert is_url("https://example.com/openapi.json")
        assert is_url("http://localhost:8080/spec.json")
        assert not is_url("./openapi.json")
        assert not is_url("/absolute/path.json")
        assert not is_url("-")

    def test_generate_from_url_mocked(self, tmp_path: Path, monkeypatch):
        """Test generating client from a URL with mocked HTTP."""
        import json

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        # Create a test file to simulate URL content
        spec_file = tmp_path / "url_spec.json"
        spec_file.write_text(json.dumps(spec))

        # Monkeypatch load_spec_from_url in the cli module
        from openapi_ts_client import cli

        def mock_load_spec_from_url(url):
            return spec

        monkeypatch.setattr(cli, "load_spec_from_url", mock_load_spec_from_url)

        output_dir = tmp_path / "output"
        result = cli.main(
            [
                "https://example.com/openapi.json",
                "-o",
                str(output_dir),
            ]
        )
        assert result == 0
        assert output_dir.exists()


class TestStdinInput:
    """Test stdin input handling."""

    def test_generate_from_stdin(self, tmp_path: Path):
        """Test generating client from stdin."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Stdin API", "version": "1.0.0"},
            "paths": {},
        }

        output_dir = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "-",
                "-o",
                str(output_dir),
            ],
            input=json.dumps(spec),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output_dir.exists()

    def test_empty_stdin(self, tmp_path: Path):
        """Test error on empty stdin."""
        output_dir = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "-",
                "-o",
                str(output_dir),
            ],
            input="",
            capture_output=True,
            text=True,
        )
        # Return code can be 1 (IO error) or 2 (validation error)
        assert result.returncode in (1, 2)
        assert "error" in result.stderr.lower()


class TestConfigFile:
    """Test config file handling."""

    def test_single_client_config(self, tmp_path: Path):
        """Test config with single client shorthand."""
        # Use absolute path for the spec file
        spec_path = Path.cwd() / "tests/fixtures/petstore/openapi.json"
        config = {
            "input": str(spec_path),
            "format": "axios",
            "output": str(tmp_path / "output"),
        }
        config_file = tmp_path / "openapi-ts-client.json"
        config_file.write_text(json.dumps(config))

        result = subprocess.run(
            [sys.executable, "-m", "openapi_ts_client.cli"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (tmp_path / "output" / "index.ts").exists()

    def test_multi_client_config(self, tmp_path: Path):
        """Test config with multiple clients."""
        # Use absolute path for the spec file
        spec_path = Path.cwd() / "tests/fixtures/petstore/openapi.json"
        config = {
            "clients": [
                {
                    "input": str(spec_path),
                    "format": "fetch",
                    "output": str(tmp_path / "fetch-client"),
                },
                {
                    "input": str(spec_path),
                    "format": "axios",
                    "output": str(tmp_path / "axios-client"),
                },
            ]
        }
        config_file = tmp_path / "openapi-ts-client.json"
        config_file.write_text(json.dumps(config))

        result = subprocess.run(
            [sys.executable, "-m", "openapi_ts_client.cli"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env={**os.environ, "PYTHONPATH": str(Path.cwd())},
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (tmp_path / "fetch-client").exists()
        assert (tmp_path / "axios-client").exists()

    def test_custom_config_path(self, tmp_path: Path):
        """Test --config flag for custom config path."""
        # Use absolute path for the spec file
        spec_path = Path.cwd() / "tests/fixtures/petstore/openapi.json"
        config = {
            "input": str(spec_path),
            "output": str(tmp_path / "output"),
        }
        config_file = tmp_path / "custom-config.json"
        config_file.write_text(json.dumps(config))

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "--config",
                str(config_file),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_explicit_input_ignores_config(self, tmp_path: Path):
        """Test that explicit input argument ignores config file."""
        # Use absolute path for the spec file
        spec_path = Path.cwd() / "tests/fixtures/petstore/openapi.json"
        config = {
            "input": "wrong-file.json",
            "output": str(tmp_path / "config-output"),
        }
        config_file = tmp_path / "openapi-ts-client.json"
        config_file.write_text(json.dumps(config))

        output_dir = tmp_path / "cli-output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                str(spec_path),
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output_dir.exists()
        assert not (tmp_path / "config-output").exists()

    def test_invalid_config_file(self, tmp_path: Path):
        """Test error on invalid config file."""
        config_file = tmp_path / "openapi-ts-client.json"
        config_file.write_text("not valid json")

        result = subprocess.run(
            [sys.executable, "-m", "openapi_ts_client.cli"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        assert result.returncode == 2
        assert "config" in result.stderr.lower() or "error" in result.stderr.lower()


class TestOutputFormatting:
    """Test output formatting options."""

    def test_quiet_mode_no_output(self, tmp_path: Path):
        """Test that --quiet suppresses output."""
        output_dir = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "tests/fixtures/petstore/openapi.json",
                "-o",
                str(output_dir),
                "-q",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Stdout should be empty (no progress messages)
        # Note: the debug logs go to stdout but we're checking for absence of "Generated"
        assert "Generated" not in result.stdout

    def test_default_output_shows_progress(self, tmp_path: Path):
        """Test that default output shows progress."""
        output_dir = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "tests/fixtures/petstore/openapi.json",
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Generated" in result.stdout or "generated" in result.stdout

    def test_verbose_mode_shows_details(self, tmp_path: Path):
        """Test that --verbose shows detailed output."""
        output_dir = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "tests/fixtures/petstore/openapi.json",
                "-o",
                str(output_dir),
                "-v",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Verbose should show more details - look for reading/generating/api details
        output = result.stdout.lower()
        assert (
            "reading" in output or "generating" in output or "petstore" in output or "api" in output
        )


class TestValidation:
    """Test validation options."""

    def test_no_validate_skips_validation(self, tmp_path: Path):
        """Test that --no-validate skips spec validation."""
        # Create an invalid spec (missing required info.title)
        invalid_spec = {
            "openapi": "3.0.0",
            "info": {"version": "1.0.0"},  # missing title
            "paths": {},
        }
        spec_file = tmp_path / "invalid.json"
        spec_file.write_text(json.dumps(invalid_spec))

        output_dir = tmp_path / "output"

        # Without --no-validate, should fail
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                str(spec_file),
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        # Validation errors return code 1 or 2 depending on error type
        assert result.returncode != 0

        # With --no-validate, should succeed (or at least get further)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                str(spec_file),
                "-o",
                str(output_dir),
                "--no-validate",
            ],
            capture_output=True,
            text=True,
        )
        # May still fail in generation, but not in validation
        # Check that it didn't fail with validation error
        if result.returncode != 0:
            assert "info.title" not in result.stderr.lower()


class TestCleanForceFlags:
    """Test --clean and --force CLI flags."""

    def test_clean_flag_clears_directory(self, tmp_path: Path):
        """Test that --clean clears the output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "old_file.ts").touch()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "tests/fixtures/petstore/openapi.json",
                "-o",
                str(output_dir),
                "--clean",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert not (output_dir / "old_file.ts").exists()
        assert (output_dir / "index.ts").exists()

    def test_force_flag_continues_without_clearing(self, tmp_path: Path):
        """Test that --force continues without clearing."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "keep_me.txt").touch()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "tests/fixtures/petstore/openapi.json",
                "-o",
                str(output_dir),
                "--force",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (output_dir / "keep_me.txt").exists()
        assert (output_dir / "index.ts").exists()

    def test_both_flags_error(self, tmp_path: Path):
        """Test that --clean and --force together gives error."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "tests/fixtures/petstore/openapi.json",
                "-o",
                str(output_dir),
                "--clean",
                "--force",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "mutually exclusive" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_nonempty_without_flags_error(self, tmp_path: Path):
        """Test that non-empty directory without flags gives error."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "existing.ts").touch()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "openapi_ts_client.cli",
                "tests/fixtures/petstore/openapi.json",
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "not empty" in result.stderr.lower() or "error" in result.stderr.lower()


class TestInteractivePrompt:
    """Test interactive TTY prompt."""

    def test_prompt_function_returns_clean(self, monkeypatch):
        """Test prompt_directory_action returns 'clean' for input '1'."""
        from openapi_ts_client import cli

        monkeypatch.setattr("builtins.input", lambda _: "1")
        result = cli.prompt_directory_action(Path("/tmp/test"), 5)
        assert result == "clean"

    def test_prompt_function_returns_force(self, monkeypatch):
        """Test prompt_directory_action returns 'force' for input '2'."""
        from openapi_ts_client import cli

        monkeypatch.setattr("builtins.input", lambda _: "2")
        result = cli.prompt_directory_action(Path("/tmp/test"), 5)
        assert result == "force"

    def test_prompt_function_returns_cancel(self, monkeypatch):
        """Test prompt_directory_action returns 'cancel' for input '3'."""
        from openapi_ts_client import cli

        monkeypatch.setattr("builtins.input", lambda _: "3")
        result = cli.prompt_directory_action(Path("/tmp/test"), 5)
        assert result == "cancel"

    def test_interactive_cancel_exits(self, tmp_path: Path, monkeypatch):
        """Test that cancel choice exits without generating."""
        from openapi_ts_client import cli

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "existing.ts").touch()

        # Mock isatty to return True
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        # Mock prompt to return cancel
        monkeypatch.setattr(cli, "prompt_directory_action", lambda p, c: "cancel")

        spec_path = Path.cwd() / "tests/fixtures/petstore/openapi.json"
        result = cli.main([str(spec_path), "-o", str(output_dir)])

        assert result == 1  # Cancelled
        assert (output_dir / "existing.ts").exists()  # Not cleared
        assert not (output_dir / "index.ts").exists()  # Not generated

    def test_interactive_clean_clears_and_generates(self, tmp_path: Path, monkeypatch):
        """Test that clean choice clears directory and generates."""
        from openapi_ts_client import cli

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "existing.ts").touch()

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr(cli, "prompt_directory_action", lambda p, c: "clean")

        spec_path = Path.cwd() / "tests/fixtures/petstore/openapi.json"
        result = cli.main([str(spec_path), "-o", str(output_dir)])

        assert result == 0
        assert not (output_dir / "existing.ts").exists()  # Cleared
        assert (output_dir / "index.ts").exists()  # Generated

    def test_interactive_force_continues_without_clearing(self, tmp_path: Path, monkeypatch):
        """Test that force choice continues without clearing the directory."""
        from openapi_ts_client import cli

        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "existing.ts").touch()

        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        monkeypatch.setattr(cli, "prompt_directory_action", lambda p, c: "force")

        spec_path = Path.cwd() / "tests/fixtures/petstore/openapi.json"
        result = cli.main([str(spec_path), "-o", str(output_dir)])

        assert result == 0
        assert (output_dir / "existing.ts").exists()  # Not cleared
        assert (output_dir / "index.ts").exists()  # Generated
