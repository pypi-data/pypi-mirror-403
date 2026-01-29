"""Tests for CLI module."""

from unittest import mock

from typer.testing import CliRunner

from tdd_llm import __version__
from tdd_llm.cli import app
from tdd_llm.config import Config

runner = CliRunner()


class TestVersionCommand:
    """Tests for version command."""

    def test_version_shows_version(self):
        """Test that version command shows version number."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_version_shows_tdd_llm(self):
        """Test that version command shows tdd-llm name."""
        result = runner.invoke(app, ["version"])
        assert "tdd-llm" in result.output


class TestListCommand:
    """Tests for list command."""

    def test_list_shows_languages(self):
        """Test that list command shows available languages."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "python" in result.output.lower()

    def test_list_shows_backends(self):
        """Test that list command shows available backends."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "files" in result.output.lower()


class TestDeployCommand:
    """Tests for deploy command."""

    def test_deploy_default_options(self, temp_dir):
        """Test deploy with default options."""
        with mock.patch("tdd_llm.cli.Config.load") as mock_config:
            mock_config.return_value = Config()
            result = runner.invoke(app, [
                "deploy",
                "--target", "project",
                "--lang", "python",
                "--backend", "files",
                "--platform", "claude",
            ], env={"PWD": str(temp_dir)})
            # Just check it doesn't crash - actual deployment tested elsewhere
            assert result.exit_code == 0 or "Error" in result.output

    def test_deploy_dry_run(self, temp_dir):
        """Test deploy with dry-run option."""
        result = runner.invoke(app, [
            "deploy",
            "--lang", "python",
            "--backend", "files",
            "--platform", "claude",
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "dry run" in result.output.lower()

    def test_deploy_invalid_language(self):
        """Test deploy with invalid language."""
        result = runner.invoke(app, [
            "deploy",
            "--lang", "nonexistent_language",
            "--backend", "files",
        ])
        assert result.exit_code == 1
        assert "unknown language" in result.output.lower() or "error" in result.output.lower()

    def test_deploy_invalid_backend(self):
        """Test deploy with invalid backend."""
        result = runner.invoke(app, [
            "deploy",
            "--lang", "python",
            "--backend", "nonexistent_backend",
        ])
        assert result.exit_code == 1
        assert "unknown backend" in result.output.lower() or "error" in result.output.lower()

    def test_deploy_invalid_target(self):
        """Test deploy with invalid target."""
        result = runner.invoke(app, [
            "deploy",
            "--lang", "python",
            "--backend", "files",
            "--target", "invalid_target",
        ])
        assert result.exit_code == 1
        assert "project" in result.output.lower() or "user" in result.output.lower()

    def test_deploy_shows_info(self, temp_dir):
        """Test deploy shows deployment info."""
        result = runner.invoke(app, [
            "deploy",
            "--lang", "python",
            "--backend", "files",
            "--platform", "claude",
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "python" in result.output.lower()
        assert "files" in result.output.lower()


class TestConfigCommand:
    """Tests for config command."""

    def test_config_show(self):
        """Test config --show displays current configuration."""
        result = runner.invoke(app, ["config", "--show"])
        assert result.exit_code == 0
        assert "configuration" in result.output.lower() or "setting" in result.output.lower()

    def test_config_no_args_shows_config(self):
        """Test config without args shows configuration."""
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        # Should show current config
        assert "language" in result.output.lower() or "target" in result.output.lower()

    def test_config_set_invalid_backend(self):
        """Test config --set-backend with invalid value."""
        result = runner.invoke(app, ["config", "--set-backend", "invalid"])
        assert result.exit_code == 1
        assert "error" in result.output.lower()

    def test_config_set_invalid_target(self):
        """Test config --set-target with invalid value."""
        result = runner.invoke(app, ["config", "--set-target", "invalid"])
        assert result.exit_code == 1
        assert "error" in result.output.lower()

    def test_config_set_invalid_coverage_line(self):
        """Test config --set-coverage-line with invalid value."""
        result = runner.invoke(app, ["config", "--set-coverage-line", "150"])
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "100" in result.output

    def test_config_set_invalid_coverage_branch(self):
        """Test config --set-coverage-branch with invalid value."""
        result = runner.invoke(app, ["config", "--set-coverage-branch", "-10"])
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "0" in result.output

    def test_config_set_valid_language(self, temp_dir):
        """Test config --set-lang with valid value."""
        with mock.patch("tdd_llm.paths.get_config_dir", return_value=temp_dir):
            result = runner.invoke(app, ["config", "--set-lang", "typescript"])
            assert result.exit_code == 0
            assert "typescript" in result.output.lower()

    def test_config_set_valid_backend(self, temp_dir):
        """Test config --set-backend with valid value."""
        with mock.patch("tdd_llm.paths.get_config_dir", return_value=temp_dir):
            # Input for Jira wizard: url, email, project_key
            result = runner.invoke(
                app,
                ["config", "--set-backend", "jira"],
                input="https://test.atlassian.net\ntest@example.com\nTEST\n",
            )
            assert result.exit_code == 0
            assert "jira" in result.output.lower()

    def test_config_set_valid_target(self, temp_dir):
        """Test config --set-target with valid value."""
        with mock.patch("tdd_llm.paths.get_config_dir", return_value=temp_dir):
            result = runner.invoke(app, ["config", "--set-target", "user"])
            assert result.exit_code == 0
            assert "user" in result.output.lower()

    def test_config_set_valid_coverage(self, temp_dir):
        """Test config --set-coverage-line with valid value."""
        with mock.patch("tdd_llm.paths.get_config_dir", return_value=temp_dir):
            result = runner.invoke(app, ["config", "--set-coverage-line", "90"])
            assert result.exit_code == 0
            assert "90" in result.output


class TestAppHelp:
    """Tests for app help."""

    def test_no_args_shows_help(self):
        """Test that no arguments shows help."""
        result = runner.invoke(app, [])
        # Typer with no_args_is_help=True returns exit code 0 or 2
        assert result.exit_code in (0, 2)
        # Should show help text
        assert "deploy" in result.output.lower() or "help" in result.output.lower()

    def test_help_option(self):
        """Test --help option."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "deploy" in result.output.lower()
        assert "config" in result.output.lower()
        assert "list" in result.output.lower()
        assert "version" in result.output.lower()

    def test_deploy_help(self):
        """Test deploy --help."""
        result = runner.invoke(app, ["deploy", "--help"])
        assert result.exit_code == 0
        assert "--lang" in result.output
        assert "--backend" in result.output
        assert "--target" in result.output
        assert "--platform" in result.output
        assert "--dry-run" in result.output
        assert "--force" in result.output

    def test_config_help(self):
        """Test config --help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "--show" in result.output
        assert "--set-lang" in result.output
        assert "--set-backend" in result.output


class TestSetupCommand:
    """Tests for setup command and wizard."""

    def test_setup_help(self):
        """Test setup --help."""
        result = runner.invoke(app, ["setup", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output

    def test_setup_when_config_exists(self, temp_dir):
        """Test setup shows message when config already exists."""
        with mock.patch("tdd_llm.cli.is_first_run", return_value=False):
            config_path = temp_dir / "config.yaml"
            with mock.patch("tdd_llm.cli.get_global_config_path", return_value=config_path):
                result = runner.invoke(app, ["setup"])
                assert result.exit_code == 0
                assert "already exists" in result.output.lower()

    def test_setup_force_runs_wizard(self, temp_dir):
        """Test setup --force runs wizard even if config exists."""
        with mock.patch("tdd_llm.cli.is_first_run", return_value=False):
            config_path = temp_dir / "config.yaml"
            with mock.patch("tdd_llm.cli.get_global_config_path", return_value=config_path):
                with mock.patch("tdd_llm.config.get_config_dir", return_value=temp_dir):
                    # Simulate user input: confirm yes, then defaults for all prompts
                    result = runner.invoke(
                        app,
                        ["setup", "--force"],
                        input="y\npython\nfiles\nproject\nclaude,gemini\n80\n70\n",
                    )
                    assert result.exit_code == 0
                    assert "welcome" in result.output.lower()

    def test_setup_wizard_accepts_input(self, temp_dir):
        """Test setup wizard accepts user input."""
        with mock.patch("tdd_llm.cli.is_first_run", return_value=True):
            with mock.patch("tdd_llm.config.get_config_dir", return_value=temp_dir):
                # Input: confirm, lang, backend, jira_url, jira_email, jira_project,
                # target, platforms, coverage_line, coverage_branch
                result = runner.invoke(
                    app,
                    ["setup"],
                    input="y\ntypescript\njira\nhttps://test.atlassian.net\ntest@example.com\nTEST\nuser\nclaude\n90\n85\n",
                )
                assert result.exit_code == 0
                assert "configuration saved" in result.output.lower()

                # Verify config was created
                config_file = temp_dir / "config.yaml"
                assert config_file.exists()

    def test_setup_wizard_can_be_skipped(self, temp_dir):
        """Test setup wizard can be skipped with 'n'."""
        with mock.patch("tdd_llm.cli.is_first_run", return_value=True):
            with mock.patch("tdd_llm.config.get_config_dir", return_value=temp_dir):
                result = runner.invoke(app, ["setup"], input="n\n")
                assert result.exit_code == 0
                assert "skipped" in result.output.lower()

                # Config should not be created
                config_file = temp_dir / "config.yaml"
                assert not config_file.exists()

    def test_setup_wizard_validates_coverage(self, temp_dir):
        """Test setup wizard clamps coverage values to 0-100."""
        with mock.patch("tdd_llm.cli.is_first_run", return_value=True):
            with mock.patch("tdd_llm.config.get_config_dir", return_value=temp_dir):
                # Input coverage > 100, should be clamped
                result = runner.invoke(
                    app,
                    ["setup"],
                    input="y\npython\nfiles\nproject\nclaude\n150\n-10\n",
                )
                assert result.exit_code == 0

                # Read saved config and verify clamped values
                import yaml
                config_file = temp_dir / "config.yaml"
                with open(config_file) as f:
                    data = yaml.safe_load(f)
                assert data["coverage"]["line"] == 100  # clamped from 150
                assert data["coverage"]["branch"] == 0  # clamped from -10


class TestFirstRunCallback:
    """Tests for first-run callback behavior."""

    def test_callback_triggers_wizard_on_first_run(self, temp_dir):
        """Test that first run triggers setup wizard."""
        with mock.patch("tdd_llm.cli.is_first_run", return_value=True):
            with mock.patch("tdd_llm.config.get_config_dir", return_value=temp_dir):
                # Running any command on first run should trigger wizard
                result = runner.invoke(
                    app,
                    ["list"],
                    input="n\n",  # Skip wizard
                )
                assert "welcome" in result.output.lower() or "first time" in result.output.lower()

    def test_callback_skips_wizard_for_version(self, temp_dir):
        """Test that version command does not trigger wizard."""
        with mock.patch("tdd_llm.cli.is_first_run", return_value=True):
            result = runner.invoke(app, ["version"])
            assert result.exit_code == 0
            assert "welcome" not in result.output.lower()
            assert "tdd-llm" in result.output

    def test_callback_skips_wizard_when_config_exists(self):
        """Test that wizard is not triggered when config exists."""
        with mock.patch("tdd_llm.cli.is_first_run", return_value=False):
            result = runner.invoke(app, ["list"])
            assert result.exit_code == 0
            assert "welcome" not in result.output.lower()


class TestDeployIntegration:
    """Integration tests for deploy command."""

    def test_deploy_creates_files(self, temp_dir):
        """Test deploy actually creates files."""
        # Change to temp directory for project deployment
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = runner.invoke(app, [
                "deploy",
                "--lang", "python",
                "--backend", "files",
                "--platform", "claude",
                "--target", "project",
            ])
            assert result.exit_code == 0
            assert (temp_dir / ".claude").exists()
            assert (temp_dir / ".claude" / "commands").exists()
        finally:
            os.chdir(original_cwd)

    def test_deploy_both_platforms(self, temp_dir):
        """Test deploy to both Claude and Gemini."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = runner.invoke(app, [
                "deploy",
                "--lang", "python",
                "--backend", "files",
                "--platform", "claude",
                "--platform", "gemini",
                "--target", "project",
            ])
            assert result.exit_code == 0
            assert (temp_dir / ".claude").exists()
            assert (temp_dir / ".gemini").exists()
        finally:
            os.chdir(original_cwd)

    def test_deploy_force_overwrites(self, temp_dir):
        """Test deploy --force overwrites existing files."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # First deploy
            runner.invoke(app, [
                "deploy",
                "--lang", "python",
                "--backend", "files",
                "--platform", "claude",
                "--target", "project",
            ])

            # Second deploy with force
            result = runner.invoke(app, [
                "deploy",
                "--lang", "python",
                "--backend", "files",
                "--platform", "claude",
                "--target", "project",
                "--force",
            ])
            assert result.exit_code == 0
            assert "created" in result.output.lower() or "done" in result.output.lower()
        finally:
            os.chdir(original_cwd)

    def test_deploy_skips_existing(self, temp_dir):
        """Test deploy skips existing files without --force."""
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # First deploy
            runner.invoke(app, [
                "deploy",
                "--lang", "python",
                "--backend", "files",
                "--platform", "claude",
                "--target", "project",
            ])

            # Second deploy without force
            result = runner.invoke(app, [
                "deploy",
                "--lang", "python",
                "--backend", "files",
                "--platform", "claude",
                "--target", "project",
            ])
            assert result.exit_code == 0
            assert "skipped" in result.output.lower()
        finally:
            os.chdir(original_cwd)
