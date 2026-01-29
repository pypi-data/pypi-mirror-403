"""Jira backend implementation for TDD workflow."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ..base import Backend, Epic, Task, WorkflowState
from .client import JiraClient, JiraIssue, JiraNotFoundError, markdown_to_adf

if TYPE_CHECKING:
    from ...config import JiraConfig

logger = logging.getLogger(__name__)

# Local state file for session continuity
LOCAL_STATE_FILE = ".tdd-state.local.json"

# TDD phase label prefix
PHASE_LABEL_PREFIX = "tdd:"


class JiraBackend:
    """Backend using Jira for TDD workflow state management."""

    def __init__(self, config: JiraConfig, project_root: Path | None = None):
        """Initialize Jira backend.

        Args:
            config: Jira configuration.
            project_root: Project root for local state file. Defaults to cwd.
        """
        self.config = config
        self.project_root = project_root or Path.cwd()
        self._client: JiraClient | None = None

    @property
    def client(self) -> JiraClient:
        """Get or create the Jira client."""
        if self._client is None:
            self._client = JiraClient(self.config)
        return self._client

    @property
    def local_state_path(self) -> Path:
        """Path to local session state file."""
        return self.project_root / LOCAL_STATE_FILE

    def _load_local_state(self) -> dict:
        """Load local session state."""
        if not self.local_state_path.exists():
            return {"current": {"epic": None, "task": None, "phase": None}}

        with open(self.local_state_path, encoding="utf-8") as f:
            return json.load(f)

    def _save_local_state(self, state: dict) -> None:
        """Save local session state."""
        with open(self.local_state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def _issue_to_task(self, issue: JiraIssue, epic_id: str | None = None) -> Task:
        """Convert Jira issue to Task.

        Args:
            issue: Jira issue.
            epic_id: Parent epic ID (if known).

        Returns:
            Task instance.
        """
        # Determine epic_id
        if epic_id is None:
            epic_id = issue.parent_key or ""

        # Get TDD status from Jira status
        status = self.config.get_tdd_status(issue.status)

        # Get acceptance criteria from custom field or description
        acceptance_criteria = None
        if self.config.fields.acceptance_criteria:
            ac_field = issue.custom_fields.get(self.config.fields.acceptance_criteria)
            if ac_field:
                if isinstance(ac_field, str):
                    acceptance_criteria = ac_field
                elif isinstance(ac_field, dict):
                    # ADF format
                    acceptance_criteria = JiraIssue._extract_text_from_adf(ac_field)

        # Get phase from labels
        phase = None
        for label in issue.labels:
            if label.startswith(PHASE_LABEL_PREFIX):
                phase = label[len(PHASE_LABEL_PREFIX) :]
                break

        return Task(
            id=issue.key,
            epic_id=epic_id,
            title=issue.summary,
            description=issue.description or "",
            status=status,
            acceptance_criteria=acceptance_criteria,
            phase=phase,
        )

    def _issue_to_epic(self, issue: JiraIssue, tasks: list[Task] | None = None) -> Epic:
        """Convert Jira epic issue to Epic.

        Args:
            issue: Jira epic issue.
            tasks: Pre-loaded tasks (optional).

        Returns:
            Epic instance.
        """
        status = self.config.get_tdd_status(issue.status)

        return Epic(
            id=issue.key,
            name=issue.summary,
            description=issue.description or "",
            status=status,
            tasks=tasks or [],
        )

    def _get_tasks_for_epic(self, epic_key: str) -> list[Task]:
        """Get all tasks belonging to an epic.

        Args:
            epic_key: Epic issue key.

        Returns:
            List of tasks in the epic.
        """
        project = self.config.effective_project_key

        # Build JQL for tasks in this epic
        # Jira Cloud uses parent = EPIC_KEY
        # Also filter by task issue types
        task_types = ", ".join(f'"{t}"' for t in self.config.task_issue_types)
        jql = (
            f'project = "{project}" AND parent = "{epic_key}" '
            f"AND issuetype in ({task_types}) ORDER BY rank"
        )

        issues, _ = self.client.search(jql)
        return [self._issue_to_task(issue, epic_id=epic_key) for issue in issues]

    def get_epic(self, epic_id: str) -> Epic:
        """Get an epic by ID (Jira key)."""
        try:
            issue = self.client.get_issue(epic_id)
        except JiraNotFoundError as e:
            raise KeyError(f"Epic not found: {epic_id}") from e

        if issue.issue_type != self.config.epic_issue_type:
            raise KeyError(f"Issue {epic_id} is not an Epic (type: {issue.issue_type})")

        tasks = self._get_tasks_for_epic(epic_id)
        return self._issue_to_epic(issue, tasks)

    def list_epics(self, status: str | None = None) -> list[Epic]:
        """List all epics, optionally filtered by status."""
        project = self.config.effective_project_key
        epic_type = self.config.epic_issue_type

        jql = f'project = "{project}" AND issuetype = "{epic_type}"'

        # Filter by status if specified using config-based mapping
        if status:
            jira_statuses = self.config.get_jira_statuses_for_tdd(status)
            if jira_statuses:
                quoted_statuses = ", ".join(f'"{s}"' for s in jira_statuses)
                jql += f" AND status IN ({quoted_statuses})"

        jql += " ORDER BY rank"

        issues, _ = self.client.search(jql)
        epics = []

        for issue in issues:
            tasks = self._get_tasks_for_epic(issue.key)
            epic = self._issue_to_epic(issue, tasks)

            # Double-check status filter (in case Jira status names differ)
            if status is None or epic.status == status:
                epics.append(epic)

        return epics

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID (Jira key)."""
        try:
            issue = self.client.get_issue(task_id)
        except JiraNotFoundError as e:
            raise KeyError(f"Task not found: {task_id}") from e

        if issue.issue_type not in self.config.task_issue_types:
            raise KeyError(
                f"Issue {task_id} is not a task (type: {issue.issue_type}, "
                f"expected: {self.config.task_issue_types})"
            )

        return self._issue_to_task(issue)

    def get_next_task(self, epic_id: str) -> Task | None:
        """Get the next incomplete task in an epic.

        Returns the first task that is not completed (i.e., not_started or in_progress).
        """
        epic = self.get_epic(epic_id)
        return next((task for task in epic.tasks if task.status != "completed"), None)

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update a task's status in Jira."""
        # Map TDD status to Jira status name using config
        jira_status = self.config.get_jira_status(status)

        # Try to transition the issue
        success, available = self.client.transition_to_status(task_id, jira_status)
        if not success:
            logger.warning(
                "Failed to transition issue %s to status '%s'. "
                "Available transitions: %s. "
                "Configure status_map in tdd-llm.toml to map your Jira statuses.",
                task_id,
                jira_status,
                available,
            )

        # Update local state if completing
        if status == "completed":
            local_state = self._load_local_state()
            if local_state.get("current", {}).get("task") == task_id:
                local_state["current"]["task"] = None
                local_state["current"]["phase"] = None
                self._save_local_state(local_state)

    def get_state(self) -> WorkflowState:
        """Get the current workflow state."""
        local_state = self._load_local_state()

        current_epic_id = local_state.get("current", {}).get("epic")
        current_task_id = local_state.get("current", {}).get("task")

        current_epic = None
        current_task = None

        if current_epic_id:
            try:
                current_epic = self.get_epic(current_epic_id)
                if current_task_id:
                    for task in current_epic.tasks:
                        if task.id == current_task_id:
                            current_task = task
                            break
            except KeyError:
                pass

        # Get all epics
        epics = self.list_epics()

        # If no current epic set, use the first in-progress or not-started epic
        if current_epic is None and epics:
            for epic in epics:
                if epic.status in ("in_progress", "not_started"):
                    current_epic = epic
                    break

        return WorkflowState(
            backend="jira",
            current_epic=current_epic,
            current_task=current_task,
            epics=epics,
        )

    def set_phase(self, task_id: str, phase: str) -> None:
        """Set the TDD phase for a task using Jira labels."""
        # Remove existing phase labels and add new one
        remove_labels = [
            label
            for label in self.client.get_issue(task_id).labels
            if label.startswith(PHASE_LABEL_PREFIX)
        ]

        new_label = f"{PHASE_LABEL_PREFIX}{phase}"

        self.client.update_labels(
            task_id,
            add=[new_label],
            remove=remove_labels if remove_labels else None,
        )

        # Update local state
        local_state = self._load_local_state()
        local_state["current"]["phase"] = phase
        self._save_local_state(local_state)

    def set_current_task(self, epic_id: str, task_id: str | None) -> None:
        """Set the current active task."""
        local_state = self._load_local_state()
        local_state["current"]["epic"] = epic_id
        local_state["current"]["task"] = task_id
        local_state["current"]["phase"] = None
        self._save_local_state(local_state)

    def add_comment(self, task_id: str, comment: str) -> bool:
        """Add a comment to a task.

        Args:
            task_id: Task issue key.
            comment: Comment text.

        Returns:
            True (comments are supported).
        """
        self.client.add_comment(task_id, comment)
        return True

    def create_epic(
        self,
        name: str,
        description: str,
        epic_id: str | None = None,
    ) -> Epic:
        """Create a new epic in Jira.

        Args:
            name: Epic name/title.
            description: Epic description.
            epic_id: Ignored for Jira (key assigned by Jira).

        Returns:
            Created Epic instance.
        """
        project = self.config.effective_project_key
        epic_type = self.config.epic_issue_type

        payload = {
            "fields": {
                "project": {"key": project},
                "summary": name,
                "description": markdown_to_adf(description),
                "issuetype": {"name": epic_type},
            }
        }

        result = self.client.create_issue(payload)
        key = result["key"]

        logger.info("Created epic %s: %s", key, name)

        return Epic(
            id=key,
            name=name,
            description=description,
            status="not_started",
            tasks=[],
        )

    def create_task(
        self,
        epic_id: str,
        title: str,
        description: str,
        acceptance_criteria: str | None = None,
        task_id: str | None = None,
    ) -> Task:
        """Create a new task/story in Jira under an epic.

        Args:
            epic_id: Parent epic key (e.g., 'PROJ-100').
            title: Task title/summary.
            description: Full task description.
            acceptance_criteria: Optional acceptance criteria.
            task_id: Ignored for Jira (key assigned by Jira).

        Returns:
            Created Task instance.

        Raises:
            KeyError: If epic not found.
        """
        # Verify epic exists
        try:
            self.client.get_issue(epic_id)
        except JiraNotFoundError as e:
            raise KeyError(f"Epic not found: {epic_id}") from e

        project = self.config.effective_project_key
        # Use first task issue type (usually "Story")
        task_type = self.config.task_issue_types[0] if self.config.task_issue_types else "Story"

        # Build description with acceptance criteria if provided
        full_description = description
        if acceptance_criteria:
            full_description += f"\n\n**Acceptance Criteria:**\n{acceptance_criteria}"

        payload: dict = {
            "fields": {
                "project": {"key": project},
                "summary": title,
                "description": markdown_to_adf(full_description),
                "issuetype": {"name": task_type},
                "parent": {"key": epic_id},
            }
        }

        # Add acceptance criteria to custom field if configured
        if acceptance_criteria and self.config.fields.acceptance_criteria:
            payload["fields"][self.config.fields.acceptance_criteria] = markdown_to_adf(
                acceptance_criteria
            )

        result = self.client.create_issue(payload)
        key = result["key"]

        logger.info("Created task %s under %s: %s", key, epic_id, title)

        return Task(
            id=key,
            epic_id=epic_id,
            title=title,
            description=description,
            status="not_started",
            acceptance_criteria=acceptance_criteria,
            phase=None,
        )


# Ensure JiraBackend implements Backend protocol
def _check_protocol() -> None:
    """Type check that JiraBackend implements Backend."""
    from ...config import JiraConfig as _JiraConfig

    _backend: Backend = JiraBackend(_JiraConfig())  # noqa: F841
