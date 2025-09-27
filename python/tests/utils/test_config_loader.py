"""Tests for ConfigLoader module."""

import os
import tempfile
import tomllib
from pathlib import Path
from unittest.mock import mock_open, patch

from adb_auto_player.models.pydantic.general_settings import GeneralSettings
from adb_auto_player.settings import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader class."""

    def setup_method(self):
        """Clear the LRU cache before each test."""
        ConfigLoader.working_dir.cache_clear()
        ConfigLoader.games_dir.cache_clear()
        ConfigLoader.user_games_dir.cache_clear()
        ConfigLoader.binaries_dir.cache_clear()
        ConfigLoader.general_settings.cache_clear()
        ConfigLoader.config_dir.cache_clear()

    def test_working_dir_normal_case(self):
        """Test working_dir returns current working directory in normal case."""
        mock_cwd_path = Path("home") / "user" / "project"

        with patch("pathlib.Path.cwd", return_value=mock_cwd_path):
            result = ConfigLoader.working_dir()
            assert result == mock_cwd_path

    def test_working_dir_from_tests_directory(self):
        """Test working_dir fallback when run from tests directory."""
        mock_cwd_path = Path("home") / "user" / "python" / "tests" / "unit"
        expected_path = Path("home") / "user" / "python"

        with patch("pathlib.Path.cwd", return_value=mock_cwd_path):
            result = ConfigLoader.working_dir()
            assert result == expected_path

    def test_working_dir_python_tests_not_consecutive(self):
        """Test working_dir when python and tests are not consecutive."""
        mock_cwd_path = Path("home") / "user" / "python" / "src" / "tests"

        with patch("pathlib.Path.cwd", return_value=mock_cwd_path):
            result = ConfigLoader.working_dir()
            # Should return original path since tests doesn't immediately follow python
            assert result == mock_cwd_path

    def test_working_dir_no_python_in_path(self):
        """Test working_dir when 'python' is not in path."""
        mock_cwd_path = Path("home") / "user" / "project" / "tests"

        with patch("pathlib.Path.cwd", return_value=mock_cwd_path):
            result = ConfigLoader.working_dir()
            assert result == mock_cwd_path

    def test_working_dir_no_tests_in_path(self):
        """Test working_dir when 'tests' is not in path."""
        mock_cwd_path = Path("home") / "user" / "python" / "src"

        with patch("pathlib.Path.cwd", return_value=mock_cwd_path):
            result = ConfigLoader.working_dir()
            assert result == mock_cwd_path

    def test_games_dir_first_candidate_exists(self):
        """games_dir should return first existing candidate from working dir."""
        with tempfile.TemporaryDirectory() as temp_dir:
            working_path = Path(temp_dir)
            target = working_path / "games"
            target.mkdir()

            with patch.object(ConfigLoader, "working_dir", return_value=working_path):
                with patch("platform.system", return_value="Windows"):
                    result = ConfigLoader.games_dir()
                    assert result == target

    def test_games_dir_fallback_to_first_candidate(self):
        """games_dir falls back to first candidate when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            working_path = Path(temp_dir)

            with patch.object(ConfigLoader, "working_dir", return_value=working_path):
                with patch("platform.system", return_value="Windows"):
                    with patch("pathlib.Path.exists", return_value=False):
                        result = ConfigLoader.games_dir()
                        assert result == working_path / "games"

    def test_user_games_dir_resides_under_config_dir(self):
        """user_games_dir should return <config_dir>/games and ensure it exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config-root"
            config_dir.mkdir(parents=True)

            with patch.object(ConfigLoader, "config_dir", return_value=config_dir):
                result = ConfigLoader.user_games_dir()
                expected = config_dir / "games"
                assert result == expected
                assert expected.exists()

    def test_user_games_dir_handles_creation_error(self):
        """user_games_dir should still return path even if creation fails."""
        config_dir = Path("/unwritable/config")

        with patch.object(ConfigLoader, "config_dir", return_value=config_dir):
            with patch("pathlib.Path.mkdir", side_effect=OSError("denied")):
                result = ConfigLoader.user_games_dir()
                assert result == config_dir / "games"

    def test_binaries_dir(self):
        """Test binaries_dir returns games_dir parent / binaries."""
        games_path = Path("home") / "user" / "project" / "games"
        expected = Path("home") / "user" / "project" / "binaries"

        with patch.object(ConfigLoader, "games_dir", return_value=games_path):
            result = ConfigLoader.binaries_dir()
            assert result == expected

    def test_config_dir_linux(self):
        """Linux config dir should live under ~/.config/adbautoplayer."""
        mock_home = Path("/home/testuser")

        with patch("platform.system", return_value="Linux"):
            with patch("pathlib.Path.home", return_value=mock_home):
                result = ConfigLoader.config_dir()
                assert result == mock_home / ".config" / "adbautoplayer"

    def test_config_dir_windows_with_appdata(self):
        """Windows config dir should use APPDATA when available."""
        mock_home = Path(r"C:\\Users\\TestUser")
        appdata_path = r"C:\\Users\\TestUser\\AppData\\Roaming"

        with patch("platform.system", return_value="Windows"):
            with patch("pathlib.Path.home", return_value=mock_home):
                with patch.dict(os.environ, {"APPDATA": appdata_path}, clear=True):
                    with patch("pathlib.Path.mkdir"):
                        result = ConfigLoader.config_dir()
                    expected = Path(appdata_path) / "AdbAutoPlayer"
                    assert result == expected

    def test_config_dir_windows_without_appdata(self):
        """Windows config dir should fall back to home/AppData/Roaming."""
        mock_home = Path(r"C:\\Users\\TestUser")

        with patch("platform.system", return_value="Windows"):
            with patch("pathlib.Path.home", return_value=mock_home):
                with patch.dict(os.environ, {}, clear=True):
                    with patch("pathlib.Path.mkdir"):
                        result = ConfigLoader.config_dir()
                    expected = mock_home / "AppData" / "Roaming" / "AdbAutoPlayer"
                    assert result == expected

    def test_config_dir_macos(self):
        """macOS config dir should use Application Support."""
        mock_home = Path("/Users/testuser")

        with patch("platform.system", return_value="Darwin"):
            with patch("pathlib.Path.home", return_value=mock_home):
                result = ConfigLoader.config_dir()
                expected = (
                    mock_home
                    / "Library"
                    / "Application Support"
                    / "AdbAutoPlayer"
                )
                assert result == expected

    def test_main_config_successful_load(self):
        """Test main_config successfully loads valid TOML file."""
        config_data = {"device": {"ID": "test"}}

        config_dir = Path("home") / "user" / ".config" / "adbautoplayer"

        with patch.object(ConfigLoader, "config_dir", return_value=config_dir):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open", mock_open()):
                    with patch("tomllib.load", return_value=config_data):
                        result = ConfigLoader.general_settings()
                        assert result.device.id == "test"

    def test_main_config_file_not_found(self):
        """Test main_config handles file not found gracefully."""
        config_dir = Path("home") / "user" / ".config" / "adbautoplayer"

        with patch.object(ConfigLoader, "config_dir", return_value=config_dir):
            with patch("pathlib.Path.exists", return_value=False):
                with patch("builtins.open", side_effect=FileNotFoundError()):
                    result = ConfigLoader.general_settings()
                    assert isinstance(result, GeneralSettings)

    def test_main_config_toml_decode_error(self):
        """Test main_config handles TOML parsing errors gracefully."""
        config_dir = Path("home") / "user" / ".config" / "adbautoplayer"

        with patch.object(ConfigLoader, "config_dir", return_value=config_dir):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open", mock_open()):
                    with patch(
                        "tomllib.load",
                        side_effect=tomllib.TOMLDecodeError("Invalid TOML", "", 0),
                    ):
                        result = ConfigLoader.general_settings()
                        assert isinstance(result, GeneralSettings)

    def test_main_config_permission_error(self):
        """Test main_config handles permission errors gracefully."""
        config_dir = Path("home") / "user" / ".config" / "adbautoplayer"

        with patch.object(ConfigLoader, "config_dir", return_value=config_dir):
            with patch("pathlib.Path.exists", return_value=True):
                with patch(
                    "builtins.open", side_effect=PermissionError("Permission denied")
                ):
                    result = ConfigLoader.general_settings()
                    assert isinstance(result, GeneralSettings)

    def test_integration_with_real_temp_directories(self):
        """Integration test using real temporary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a python/tests structure
            python_dir = temp_path / "python"
            tests_dir = python_dir / "tests"
            tests_dir.mkdir(parents=True)

            with patch("pathlib.Path.cwd", return_value=tests_dir):
                ConfigLoader.working_dir.cache_clear()
                result = ConfigLoader.working_dir()
                assert result == python_dir
