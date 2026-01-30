import os
import pytest
from unittest.mock import patch
from click.testing import CliRunner

from git_smart_clone.smart_clone import git_smart_clone


class TestGitSmartClone:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_subprocess(self):
        with patch("git_smart_clone.smart_clone.subprocess") as mock:
            yield mock

    def test_clones_to_correct_path(self, runner, mock_subprocess, tmp_path):
        with patch.dict(os.environ, {"GIT_SMART_CLONE_BASE_PATH": str(tmp_path)}):
            result = runner.invoke(
                git_smart_clone, ["https://github.com/sam-phinizy/git-smart-clone"]
            )

            assert result.exit_code == 0
            expected_path = tmp_path / "github.com" / "sam-phinizy" / "git-smart-clone"
            assert expected_path.exists()

            mock_subprocess.run.assert_called_once()
            call_args = mock_subprocess.run.call_args[0][0]
            assert call_args[0] == "git"
            assert call_args[1] == "clone"
            assert "github.com/sam-phinizy/git-smart-clone" in call_args[2]

    def test_creates_nested_directories(self, runner, mock_subprocess, tmp_path):
        with patch.dict(os.environ, {"GIT_SMART_CLONE_BASE_PATH": str(tmp_path)}):
            result = runner.invoke(git_smart_clone, ["https://gitlab.com/org/project"])

            assert result.exit_code == 0
            expected_path = tmp_path / "gitlab.com" / "org" / "project"
            assert expected_path.exists()

    def test_passes_additional_args_to_git(self, runner, mock_subprocess, tmp_path):
        with patch.dict(os.environ, {"GIT_SMART_CLONE_BASE_PATH": str(tmp_path)}):
            result = runner.invoke(
                git_smart_clone,
                ["https://github.com/user/repo", "--depth", "1", "--branch", "main"],
            )

            assert result.exit_code == 0
            call_args = mock_subprocess.run.call_args[0][0]
            assert "--depth" in call_args
            assert "1" in call_args
            assert "--branch" in call_args
            assert "main" in call_args

    def test_uses_default_base_path_when_env_not_set(self, runner, mock_subprocess):
        with patch.dict(os.environ, {}, clear=True):
            if "GIT_SMART_CLONE_BASE_PATH" in os.environ:
                del os.environ["GIT_SMART_CLONE_BASE_PATH"]

            with patch("git_smart_clone.smart_clone.pathlib.Path.mkdir"):
                runner.invoke(git_smart_clone, ["https://github.com/user/repo"])

                call_args = mock_subprocess.run.call_args[0][0]
                dest_path = str(call_args[3])
                assert "src" in dest_path
                assert "github.com" in dest_path

    def test_ssh_url_clones_correctly(self, runner, mock_subprocess, tmp_path):
        with patch.dict(os.environ, {"GIT_SMART_CLONE_BASE_PATH": str(tmp_path)}):
            result = runner.invoke(git_smart_clone, ["git@github.com:user/repo.git"])

            assert result.exit_code == 0
            expected_path = tmp_path / "github.com" / "user" / "repo"
            assert expected_path.exists()

    def test_sourcehut_url_clones_correctly(self, runner, mock_subprocess, tmp_path):
        with patch.dict(os.environ, {"GIT_SMART_CLONE_BASE_PATH": str(tmp_path)}):
            result = runner.invoke(git_smart_clone, ["https://git.sr.ht/~user/repo"])

            assert result.exit_code == 0
            expected_path = tmp_path / "git.sr.ht" / "user" / "repo"
            assert expected_path.exists()
            mock_subprocess.run.assert_called_once()

    def test_codeberg_url_clones_correctly(self, runner, mock_subprocess, tmp_path):
        with patch.dict(os.environ, {"GIT_SMART_CLONE_BASE_PATH": str(tmp_path)}):
            result = runner.invoke(
                git_smart_clone, ["https://codeberg.org/org/project"]
            )

            assert result.exit_code == 0
            expected_path = tmp_path / "codeberg.org" / "org" / "project"
            assert expected_path.exists()
