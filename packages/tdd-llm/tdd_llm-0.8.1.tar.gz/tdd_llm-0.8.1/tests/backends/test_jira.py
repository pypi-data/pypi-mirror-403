"""Tests for Jira backend."""

import json
from unittest import mock

import pytest

from tdd_llm.backends.jira.backend import JiraBackend
from tdd_llm.backends.jira.client import (
    JiraClient,
    JiraIssue,
    JiraNotFoundError,
)
from tdd_llm.config import JiraConfig

# Sample Jira API responses
SAMPLE_EPIC_RESPONSE = {
    "key": "PROJ-100",
    "fields": {
        "summary": "Test Epic",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Epic description"}],
                }
            ],
        },
        "status": {"name": "In Progress"},
        "issuetype": {"name": "Epic"},
        "labels": [],
        "parent": None,
    },
}

SAMPLE_STORY_RESPONSE = {
    "key": "PROJ-1234",
    "fields": {
        "summary": "Test Story",
        "description": "Story description",
        "status": {"name": "To Do"},
        "issuetype": {"name": "Story"},
        "labels": ["tdd:test"],
        "parent": {"key": "PROJ-100"},
    },
}

SAMPLE_SEARCH_RESPONSE = {
    "issues": [
        {
            "key": "PROJ-1234",
            "fields": {
                "summary": "Story 1",
                "description": "Desc 1",
                "status": {"name": "To Do"},
                "issuetype": {"name": "Story"},
                "labels": [],
                "parent": {"key": "PROJ-100"},
            },
        },
        {
            "key": "PROJ-1235",
            "fields": {
                "summary": "Story 2",
                "description": "Desc 2",
                "status": {"name": "Done"},
                "issuetype": {"name": "Story"},
                "labels": [],
                "parent": {"key": "PROJ-100"},
            },
        },
    ]
}


@pytest.fixture
def jira_config():
    """Create a Jira config for testing."""
    return JiraConfig(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        project_key="PROJ",
    )


@pytest.fixture
def mock_api_token(monkeypatch):
    """Set the JIRA_API_TOKEN environment variable."""
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token")


class TestJiraIssue:
    """Tests for JiraIssue parsing."""

    def test_from_api_response_epic(self):
        """Test parsing an epic from API response."""
        issue = JiraIssue.from_api_response(SAMPLE_EPIC_RESPONSE)

        assert issue.key == "PROJ-100"
        assert issue.summary == "Test Epic"
        assert issue.description == "Epic description"
        assert issue.status == "In Progress"
        assert issue.issue_type == "Epic"
        assert issue.parent_key is None

    def test_from_api_response_story(self):
        """Test parsing a story from API response."""
        issue = JiraIssue.from_api_response(SAMPLE_STORY_RESPONSE)

        assert issue.key == "PROJ-1234"
        assert issue.summary == "Test Story"
        assert issue.description == "Story description"
        assert issue.status == "To Do"
        assert issue.issue_type == "Story"
        assert issue.parent_key == "PROJ-100"
        assert "tdd:test" in issue.labels

    def test_parse_adf_description(self):
        """Test parsing Atlassian Document Format description."""
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "First line"},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Second line"},
                    ],
                },
            ],
        }

        text = JiraIssue._extract_text_from_adf(adf)

        assert "First line" in text
        assert "Second line" in text


class TestJiraConfig:
    """Tests for JiraConfig."""

    def test_is_configured(self, jira_config, mock_api_token):
        """Test is_configured returns True when all required fields are set."""
        assert jira_config.is_configured() is True

    def test_is_configured_missing_token(self, jira_config):
        """Test is_configured returns False when token is missing."""
        assert jira_config.is_configured() is False

    def test_get_tdd_status_default_mapping(self, jira_config):
        """Test default Jira status to TDD status mapping."""
        assert jira_config.get_tdd_status("To Do") == "not_started"
        assert jira_config.get_tdd_status("In Progress") == "in_progress"
        assert jira_config.get_tdd_status("In Review") == "in_progress"
        assert jira_config.get_tdd_status("Done") == "completed"
        assert jira_config.get_tdd_status("Closed") == "completed"

    def test_get_tdd_status_custom_mapping(self, jira_config):
        """Test custom status mapping."""
        jira_config.status_map = {
            "Open": "not_started",
            "Working": "in_progress",
            "Finished": "completed",
        }

        assert jira_config.get_tdd_status("Open") == "not_started"
        assert jira_config.get_tdd_status("Working") == "in_progress"
        assert jira_config.get_tdd_status("Finished") == "completed"
        assert jira_config.get_tdd_status("Unknown") == "not_started"  # Default


class TestJiraClient:
    """Tests for JiraClient."""

    def test_client_requires_config_on_use(self):
        """Test client raises error if not configured when used."""
        config = JiraConfig()  # Empty config
        client = JiraClient(config)

        # Mock token storage to ensure no tokens are found
        with mock.patch(
            "tdd_llm.backends.jira.auth.TokenStorage.load_tokens", return_value=None
        ):
            # Client is lazy-loaded, so error occurs on first use
            with pytest.raises(ValueError) as exc_info:
                client._ensure_client()

            assert "not configured" in str(exc_info.value).lower()

    def test_client_init(self, jira_config, mock_api_token):
        """Test client initialization (lazy-loaded)."""
        client = JiraClient(jira_config)

        assert client.config == jira_config
        # Client is lazy-loaded, so _client is None until first use
        assert client._client is None

        client.close()

    def test_client_context_manager(self, jira_config, mock_api_token):
        """Test client as context manager."""
        with JiraClient(jira_config) as client:
            assert client is not None


class TestJiraBackend:
    """Tests for JiraBackend."""

    @pytest.fixture
    def mock_client(self, jira_config, mock_api_token):
        """Create a JiraBackend with mocked client."""
        backend = JiraBackend(jira_config)

        # Mock the client property
        mock_jira_client = mock.MagicMock()
        backend._client = mock_jira_client

        return backend, mock_jira_client

    def test_get_epic(self, mock_client):
        """Test getting an epic."""
        backend, client = mock_client

        # Mock responses
        client.get_issue.return_value = JiraIssue.from_api_response(SAMPLE_EPIC_RESPONSE)
        client.search.return_value = (
            [
                JiraIssue.from_api_response(issue)
                for issue in SAMPLE_SEARCH_RESPONSE["issues"]
            ],
            None,  # next_page_token
        )

        epic = backend.get_epic("PROJ-100")

        assert epic.id == "PROJ-100"
        assert epic.name == "Test Epic"
        assert len(epic.tasks) == 2

    def test_get_task(self, mock_client):
        """Test getting a task."""
        backend, client = mock_client

        client.get_issue.return_value = JiraIssue.from_api_response(SAMPLE_STORY_RESPONSE)

        task = backend.get_task("PROJ-1234")

        assert task.id == "PROJ-1234"
        assert task.title == "Test Story"
        assert task.epic_id == "PROJ-100"
        assert task.phase == "test"  # From label tdd:test

    def test_get_task_not_found(self, mock_client):
        """Test getting a non-existent task."""
        backend, client = mock_client

        client.get_issue.side_effect = JiraNotFoundError("Not found")

        with pytest.raises(KeyError):
            backend.get_task("PROJ-9999")

    def test_list_epics(self, mock_client):
        """Test listing epics."""
        backend, client = mock_client

        # Mock epic search
        client.search.side_effect = [
            # First call: list epics
            ([JiraIssue.from_api_response(SAMPLE_EPIC_RESPONSE)], None),
            # Second call: tasks for epic
            (
                [
                    JiraIssue.from_api_response(issue)
                    for issue in SAMPLE_SEARCH_RESPONSE["issues"]
                ],
                None,
            ),
        ]

        epics = backend.list_epics()

        assert len(epics) == 1
        assert epics[0].id == "PROJ-100"

    def test_get_next_task(self, mock_client):
        """Test getting the next incomplete task."""
        backend, client = mock_client

        # Mock responses
        client.get_issue.return_value = JiraIssue.from_api_response(SAMPLE_EPIC_RESPONSE)
        client.search.return_value = (
            [
                JiraIssue.from_api_response(issue)
                for issue in SAMPLE_SEARCH_RESPONSE["issues"]
            ],
            None,
        )

        next_task = backend.get_next_task("PROJ-100")

        assert next_task is not None
        assert next_task.id == "PROJ-1234"  # First "To Do" task

    def test_set_phase(self, mock_client, temp_dir):
        """Test setting TDD phase."""
        backend, client = mock_client
        backend.project_root = temp_dir

        # Mock get_issue to return current labels
        client.get_issue.return_value = JiraIssue.from_api_response(SAMPLE_STORY_RESPONSE)

        backend.set_phase("PROJ-1234", "dev")

        # Verify labels were updated
        client.update_labels.assert_called_once()
        call_args = client.update_labels.call_args
        assert "tdd:dev" in call_args[1]["add"]

    def test_update_task_status(self, mock_client, temp_dir):
        """Test updating task status."""
        backend, client = mock_client
        backend.project_root = temp_dir

        client.transition_to_status.return_value = (True, [])

        backend.update_task_status("PROJ-1234", "completed")

        client.transition_to_status.assert_called_once_with("PROJ-1234", "Done")

    def test_set_current_task(self, mock_client, temp_dir):
        """Test setting current task updates local state."""
        backend, client = mock_client
        backend.project_root = temp_dir

        backend.set_current_task("PROJ-100", "PROJ-1234")

        # Verify local state was updated
        local_state_file = temp_dir / ".tdd-state.local.json"
        assert local_state_file.exists()

        with open(local_state_file) as f:
            state = json.load(f)

        assert state["current"]["epic"] == "PROJ-100"
        assert state["current"]["task"] == "PROJ-1234"

    def test_add_comment(self, mock_client):
        """Test adding a comment to a task."""
        backend, client = mock_client

        backend.add_comment("PROJ-1234", "Test comment")

        client.add_comment.assert_called_once_with("PROJ-1234", "Test comment")

    def test_create_epic(self, mock_client):
        """Test creating an epic."""
        backend, client = mock_client

        # Mock create_issue response
        client.create_issue.return_value = {"key": "PROJ-200", "id": "12345"}

        epic = backend.create_epic(
            name="New Epic",
            description="Epic description here.",
        )

        # Verify the epic was created correctly
        assert epic.id == "PROJ-200"
        assert epic.name == "New Epic"
        assert epic.description == "Epic description here."
        assert epic.status == "not_started"
        assert len(epic.tasks) == 0

        # Verify create_issue was called with correct payload
        client.create_issue.assert_called_once()
        call_args = client.create_issue.call_args[0][0]
        assert call_args["fields"]["summary"] == "New Epic"
        assert call_args["fields"]["issuetype"]["name"] == "Epic"

    def test_create_task(self, mock_client):
        """Test creating a task under an epic."""
        backend, client = mock_client

        # Mock get_issue for epic verification
        client.get_issue.return_value = JiraIssue.from_api_response(SAMPLE_EPIC_RESPONSE)
        # Mock create_issue response
        client.create_issue.return_value = {"key": "PROJ-1500", "id": "67890"}

        task = backend.create_task(
            epic_id="PROJ-100",
            title="New Story",
            description="Story description here.",
            acceptance_criteria="- [ ] Test passes",
        )

        # Verify the task was created correctly
        assert task.id == "PROJ-1500"
        assert task.epic_id == "PROJ-100"
        assert task.title == "New Story"
        assert task.description == "Story description here."
        assert task.acceptance_criteria == "- [ ] Test passes"
        assert task.status == "not_started"

        # Verify create_issue was called with correct payload
        client.create_issue.assert_called_once()
        call_args = client.create_issue.call_args[0][0]
        assert call_args["fields"]["summary"] == "New Story"
        assert call_args["fields"]["parent"]["key"] == "PROJ-100"
        assert call_args["fields"]["issuetype"]["name"] == "Story"

    def test_create_task_epic_not_found(self, mock_client):
        """Test creating a task when epic doesn't exist."""
        backend, client = mock_client

        client.get_issue.side_effect = JiraNotFoundError("Not found")

        with pytest.raises(KeyError) as exc_info:
            backend.create_task(
                epic_id="PROJ-9999",
                title="Should Fail",
                description="This should fail.",
            )
        assert "Epic not found" in str(exc_info.value)


class TestMarkdownToAdf:
    """Tests for markdown_to_adf function."""

    def test_simple_paragraph(self):
        """Test simple text becomes a paragraph."""
        from tdd_llm.backends.jira.client import markdown_to_adf

        adf = markdown_to_adf("Hello world")
        assert adf["type"] == "doc"
        assert adf["version"] == 1
        assert len(adf["content"]) == 1
        assert adf["content"][0]["type"] == "paragraph"
        assert adf["content"][0]["content"][0]["text"] == "Hello world"

    def test_headings(self):
        """Test heading conversion."""
        from tdd_llm.backends.jira.client import markdown_to_adf

        adf = markdown_to_adf("## Heading 2\n### Heading 3")
        assert len(adf["content"]) == 2
        assert adf["content"][0]["type"] == "heading"
        assert adf["content"][0]["attrs"]["level"] == 2
        assert adf["content"][0]["content"][0]["text"] == "Heading 2"
        assert adf["content"][1]["attrs"]["level"] == 3

    def test_bold(self):
        """Test bold text conversion."""
        from tdd_llm.backends.jira.client import markdown_to_adf

        adf = markdown_to_adf("This is **bold** text")
        para = adf["content"][0]
        assert para["content"][0]["text"] == "This is "
        assert para["content"][1]["text"] == "bold"
        assert para["content"][1]["marks"] == [{"type": "strong"}]
        assert para["content"][2]["text"] == " text"

    def test_bullet_list(self):
        """Test bullet list conversion."""
        from tdd_llm.backends.jira.client import markdown_to_adf

        adf = markdown_to_adf("- Item 1\n- Item 2\n- Item 3")
        assert len(adf["content"]) == 1
        bullet_list = adf["content"][0]
        assert bullet_list["type"] == "bulletList"
        assert len(bullet_list["content"]) == 3
        assert bullet_list["content"][0]["type"] == "listItem"

    def test_mixed_content(self):
        """Test mixed markdown content."""
        from tdd_llm.backends.jira.client import markdown_to_adf

        md = """## Task Completed

### Objective
Build a feature

### Changes
**Created:** file.py
**Modified:** other.py

- Coverage: 85%
- Tests: 10 passed"""

        adf = markdown_to_adf(md)
        types = [node["type"] for node in adf["content"]]
        assert "heading" in types
        assert "paragraph" in types
        assert "bulletList" in types
