"""Tests for deployer module."""


from tdd_llm.config import Config, CoverageThresholds
from tdd_llm.deployer import DeploymentResult, deploy, get_target_dirs


class TestGetTargetDirs:
    """Tests for get_target_dirs function."""

    def test_project_level_both_platforms(self, temp_dir):
        """Test project-level directories for both platforms."""
        dirs = get_target_dirs("project", ["claude", "gemini"], temp_dir)

        assert "claude" in dirs
        assert "gemini" in dirs
        assert dirs["claude"] == temp_dir / ".claude"
        assert dirs["gemini"] == temp_dir / ".gemini"

    def test_project_level_claude_only(self, temp_dir):
        """Test project-level directory for Claude only."""
        dirs = get_target_dirs("project", ["claude"], temp_dir)

        assert "claude" in dirs
        assert "gemini" not in dirs

    def test_user_level_directories(self):
        """Test user-level directories."""
        dirs = get_target_dirs("user", ["claude", "gemini"])

        assert "claude" in dirs
        assert "gemini" in dirs
        # User dirs should be in home directory
        assert ".claude" in str(dirs["claude"])
        assert ".gemini" in str(dirs["gemini"])


class TestDeploy:
    """Tests for deploy function."""

    def test_deploy_creates_claude_files(self, temp_dir):
        """Test deployment creates Claude files."""
        result = deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["claude"],
            project_path=temp_dir,
        )

        assert result.success
        assert len(result.files_created) > 0

        # Check Claude directory was created
        claude_dir = temp_dir / ".claude"
        assert claude_dir.exists()

        # Check command files exist
        analyze_file = claude_dir / "commands" / "tdd" / "flow" / "1-analyze.md"
        assert analyze_file.exists()

    def test_deploy_creates_gemini_toml_files(self, temp_dir):
        """Test deployment creates Gemini TOML files."""
        result = deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["gemini"],
            project_path=temp_dir,
        )

        assert result.success
        assert len(result.files_converted) > 0

        # Check Gemini directory was created
        gemini_dir = temp_dir / ".gemini"
        assert gemini_dir.exists()

        # Check TOML file exists
        analyze_file = gemini_dir / "commands" / "tdd" / "flow" / "1-analyze.toml"
        assert analyze_file.exists()

        # Check it's valid TOML structure
        content = analyze_file.read_text()
        assert 'description = "' in content
        assert 'prompt = """' in content

    def test_deploy_replaces_placeholders(self, temp_dir):
        """Test deployment replaces placeholders."""
        result = deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["claude"],
            project_path=temp_dir,
        )

        assert result.success
        assert len(result.placeholders_replaced) > 0

        # Check placeholder was replaced in file
        test_file = temp_dir / ".claude" / "commands" / "tdd" / "flow" / "2-test.md"
        content = test_file.read_text()

        assert "{{BUILD_TEST_CMD}}" not in content
        assert "pytest" in content

    def test_deploy_uses_config_coverage_thresholds(self, temp_dir):
        """Test deployment uses coverage thresholds from config."""
        config = Config(coverage=CoverageThresholds(line=95, branch=90))

        result = deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["claude"],
            project_path=temp_dir,
            config=config,
        )

        assert result.success

        # COVERAGE_THRESHOLDS is used in 5-review.md
        review_file = temp_dir / ".claude" / "commands" / "tdd" / "flow" / "5-review.md"
        content = review_file.read_text()

        assert "95%" in content
        assert "90%" in content

    def test_deploy_dry_run_no_files_created(self, temp_dir):
        """Test dry run doesn't create files."""
        result = deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["claude"],
            project_path=temp_dir,
            dry_run=True,
        )

        assert result.success
        assert len(result.files_created) > 0

        # But no actual files should exist
        claude_dir = temp_dir / ".claude"
        assert not claude_dir.exists()

    def test_deploy_skips_existing_without_force(self, temp_dir):
        """Test deployment skips existing files without force."""
        # First deployment
        deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["claude"],
            project_path=temp_dir,
        )

        # Second deployment without force
        result = deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["claude"],
            project_path=temp_dir,
            force=False,
        )

        assert result.success
        assert len(result.skipped) > 0
        assert len(result.files_created) == 0

    def test_deploy_overwrites_with_force(self, temp_dir):
        """Test deployment overwrites existing files with force."""
        # First deployment
        deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["claude"],
            project_path=temp_dir,
        )

        # Second deployment with force
        result = deploy(
            target="project",
            lang="python",
            backend="files",
            platforms=["claude"],
            project_path=temp_dir,
            force=True,
        )

        assert result.success
        assert len(result.files_created) > 0
        assert len(result.skipped) == 0

    def test_deploy_different_languages(self, temp_dir):
        """Test deployment with different languages."""
        for lang, expected_cmd in [
            ("python", "pytest"),
            ("csharp", "dotnet test"),
            ("typescript", "jest"),
        ]:
            # Clean up between tests
            import shutil
            if (temp_dir / ".claude").exists():
                shutil.rmtree(temp_dir / ".claude")

            result = deploy(
                target="project",
                lang=lang,
                backend="files",
                platforms=["claude"],
                project_path=temp_dir,
            )

            assert result.success

            test_file = temp_dir / ".claude" / "commands" / "tdd" / "flow" / "2-test.md"
            content = test_file.read_text()
            assert expected_cmd in content, f"Expected '{expected_cmd}' for {lang}"

    def test_deploy_jira_backend(self, temp_dir):
        """Test deployment with Jira backend."""
        result = deploy(
            target="project",
            lang="python",
            backend="jira",
            platforms=["claude"],
            project_path=temp_dir,
        )

        assert result.success

        # Check Jira-specific content
        status_file = temp_dir / ".claude" / "commands" / "tdd" / "flow" / "status.md"
        content = status_file.read_text()
        assert "Jira" in content or "MCP" in content


class TestDeploymentResult:
    """Tests for DeploymentResult dataclass."""

    def test_default_values(self):
        """Test default DeploymentResult values."""
        result = DeploymentResult()

        assert result.success is True
        assert result.files_created == []
        assert result.files_converted == []
        assert result.placeholders_replaced == []
        assert result.errors == []
        assert result.skipped == []

    def test_result_with_data(self):
        """Test DeploymentResult with data."""
        result = DeploymentResult(
            success=True,
            files_created=["file1.md", "file2.md"],
            files_converted=["file1.toml"],
            placeholders_replaced=["FOO", "BAR"],
        )

        assert len(result.files_created) == 2
        assert len(result.files_converted) == 1
        assert len(result.placeholders_replaced) == 2
