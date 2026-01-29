"""Tests for updater module."""

import hashlib
import json
from unittest import mock

from tdd_llm.updater import (
    Manifest,
    UpdateResult,
    _verify_checksum,
    get_local_manifest,
    update_templates,
)


class TestManifest:
    """Tests for Manifest dataclass."""

    def test_from_json(self):
        """Test creating manifest from JSON data."""
        data = {"version": "1.0.0", "templates": {"foo.md": "abc123"}}
        manifest = Manifest.from_json(data)
        assert manifest.version == "1.0.0"
        assert manifest.templates == {"foo.md": "abc123"}

    def test_from_json_defaults(self):
        """Test defaults when JSON is missing fields."""
        data = {}
        manifest = Manifest.from_json(data)
        assert manifest.version == "0.0.0"
        assert manifest.templates == {}

    def test_to_json(self):
        """Test converting manifest to JSON."""
        manifest = Manifest(version="1.0.0", templates={"foo.md": "abc123"})
        result = manifest.to_json()
        assert result == {"version": "1.0.0", "templates": {"foo.md": "abc123"}}


class TestVerifyChecksum:
    """Tests for checksum verification."""

    def test_verify_checksum_correct(self, temp_dir):
        """Test verification with correct checksum."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("hello")
        # sha256 of "hello"
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        assert _verify_checksum(file_path, expected)

    def test_verify_checksum_incorrect(self, temp_dir):
        """Test verification with incorrect checksum."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("hello")
        assert not _verify_checksum(file_path, "wrongchecksum")

    def test_verify_checksum_missing_file(self, temp_dir):
        """Test verification with missing file."""
        file_path = temp_dir / "missing.txt"
        assert not _verify_checksum(file_path, "anychecksum")


class TestGetLocalManifest:
    """Tests for get_local_manifest function."""

    def test_no_manifest(self, temp_dir):
        """Test when no manifest exists."""
        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            result = get_local_manifest()
            assert result is None

    def test_valid_manifest(self, temp_dir):
        """Test loading valid manifest."""
        manifest_data = {"version": "1.0.0", "templates": {"test.md": "abc"}}
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))

        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            result = get_local_manifest()
            assert result is not None
            assert result.version == "1.0.0"

    def test_invalid_json(self, temp_dir):
        """Test handling of invalid JSON."""
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text("not valid json")

        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            result = get_local_manifest()
            assert result is None


class TestUpdateResult:
    """Tests for UpdateResult dataclass."""

    def test_defaults(self):
        """Test default values."""
        result = UpdateResult(status="error")
        assert result.status == "error"
        assert result.version is None
        assert result.previous_version is None
        assert result.files_updated == []
        assert result.files_unchanged == []
        assert result.errors == []


class TestUpdateTemplates:
    """Tests for update_templates function."""

    def test_network_error(self, temp_dir):
        """Test handling of network errors."""
        import httpx

        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            with mock.patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = (
                    httpx.ConnectError("Network error")
                )

                result = update_templates()

                assert result.status == "error"
                assert len(result.errors) > 0
                assert "Network error" in result.errors[0]

    def test_up_to_date(self, temp_dir):
        """Test when already up to date."""
        # Setup existing cache with same version
        manifest_data = {"version": "1.0.0", "templates": {}}
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))

        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            with mock.patch("httpx.Client") as mock_client:
                mock_response = mock.Mock()
                mock_response.json.return_value = {"version": "1.0.0", "templates": {}}
                mock_response.raise_for_status = mock.Mock()
                mock_client.return_value.__enter__.return_value.get.return_value = mock_response

                result = update_templates()

                assert result.status == "up_to_date"
                assert result.version == "1.0.0"

    def test_force_update(self, temp_dir):
        """Test force flag bypasses version check."""
        # Setup existing cache with same version
        manifest_data = {"version": "1.0.0", "templates": {}}
        manifest_path = temp_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))

        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            with mock.patch("httpx.Client") as mock_client:
                mock_response = mock.Mock()
                mock_response.json.return_value = {"version": "1.0.0", "templates": {}}
                mock_response.raise_for_status = mock.Mock()
                mock_client.return_value.__enter__.return_value.get.return_value = mock_response

                result = update_templates(force=True)

                # With force=True, should proceed to update even if same version
                assert result.status == "updated"

    def test_successful_update(self, temp_dir):
        """Test successful update with new version."""
        test_content = b"# Test Template"
        test_checksum = hashlib.sha256(test_content).hexdigest()

        manifest_data = {"version": "1.1.0", "templates": {"commands/test.md": test_checksum}}

        def mock_get(url, **kwargs):
            mock_resp = mock.Mock()
            mock_resp.raise_for_status = mock.Mock()
            if "manifest.json" in url:
                mock_resp.json.return_value = manifest_data
            else:
                mock_resp.content = test_content
            return mock_resp

        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            with mock.patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = mock_get

                result = update_templates()

                assert result.status == "updated"
                assert result.version == "1.1.0"
                assert "commands/test.md" in result.files_updated

    def test_checksum_mismatch(self, temp_dir):
        """Test handling of checksum mismatch."""
        manifest_data = {"version": "1.0.0", "templates": {"commands/test.md": "expected_checksum"}}

        def mock_get(url, **kwargs):
            mock_resp = mock.Mock()
            mock_resp.raise_for_status = mock.Mock()
            if "manifest.json" in url:
                mock_resp.json.return_value = manifest_data
            else:
                mock_resp.content = b"different content"
            return mock_resp

        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            with mock.patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = mock_get

                result = update_templates()

                assert result.status == "error"
                assert any("Checksum mismatch" in e for e in result.errors)

    def test_progress_callback(self, temp_dir):
        """Test progress callback is called."""
        test_content = b"# Test"
        test_checksum = hashlib.sha256(test_content).hexdigest()

        manifest_data = {"version": "1.0.0", "templates": {"commands/test.md": test_checksum}}

        def mock_get(url, **kwargs):
            mock_resp = mock.Mock()
            mock_resp.raise_for_status = mock.Mock()
            if "manifest.json" in url:
                mock_resp.json.return_value = manifest_data
            else:
                mock_resp.content = test_content
            return mock_resp

        callback_calls = []

        def progress_callback(current, total, filename):
            callback_calls.append((current, total, filename))

        with mock.patch("tdd_llm.updater.get_templates_cache_dir", return_value=temp_dir):
            with mock.patch("httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = mock_get

                update_templates(progress_callback=progress_callback)

                assert len(callback_calls) == 1
                assert callback_calls[0] == (1, 1, "commands/test.md")
