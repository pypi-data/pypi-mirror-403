"""Base types and protocol for TDD workflow backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class Task:
    """A task/story in the TDD workflow."""

    id: str
    """Task identifier (e.g., 'T1' for files, 'PROJ-1234' for Jira)."""

    epic_id: str
    """Parent epic identifier."""

    title: str
    """Task title/summary."""

    description: str
    """Full task description."""

    status: str
    """Task status: 'not_started', 'in_progress', or 'completed'."""

    acceptance_criteria: str | None = None
    """Acceptance criteria or definition of done."""

    phase: str | None = None
    """Current TDD phase: 'analyze', 'test', 'dev', 'docs', 'review', or None."""


@dataclass
class Epic:
    """An epic containing multiple tasks."""

    id: str
    """Epic identifier (e.g., 'E1' for files, 'PROJ-100' for Jira)."""

    name: str
    """Epic name/title."""

    description: str
    """Epic description and objectives."""

    status: str
    """Epic status: 'not_started', 'in_progress', or 'completed'."""

    tasks: list[Task] = field(default_factory=list)
    """List of tasks in this epic."""

    @property
    def completed_count(self) -> int:
        """Number of completed tasks."""
        return sum(1 for t in self.tasks if t.status == "completed")

    @property
    def progress(self) -> str:
        """Progress as 'completed/total' string."""
        return f"{self.completed_count}/{len(self.tasks)}"


@dataclass
class WorkflowState:
    """Current TDD workflow state."""

    backend: str
    """Backend type: 'files' or 'jira'."""

    current_epic: Epic | None = None
    """Currently active epic, if any."""

    current_task: Task | None = None
    """Currently active task, if any."""

    epics: list[Epic] = field(default_factory=list)
    """All epics in the project."""


@runtime_checkable
class Backend(Protocol):
    """Protocol defining the interface for TDD workflow backends.

    Backends are responsible for:
    - Reading and writing epic/task state
    - Tracking TDD phases
    - Managing workflow progression
    """

    def get_epic(self, epic_id: str) -> Epic:
        """Get an epic by ID.

        Args:
            epic_id: Epic identifier.

        Returns:
            Epic with its tasks.

        Raises:
            KeyError: If epic not found.
        """
        ...

    def list_epics(self, status: str | None = None) -> list[Epic]:
        """List all epics, optionally filtered by status.

        Args:
            status: Filter by status ('not_started', 'in_progress', 'completed').
                   If None, returns all epics.

        Returns:
            List of epics.
        """
        ...

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID.

        Args:
            task_id: Task identifier.

        Returns:
            Task details.

        Raises:
            KeyError: If task not found.
        """
        ...

    def get_next_task(self, epic_id: str) -> Task | None:
        """Get the next incomplete task in an epic.

        Args:
            epic_id: Epic to search in.

        Returns:
            Next task to work on, or None if all completed.
        """
        ...

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update a task's status.

        Args:
            task_id: Task to update.
            status: New status ('not_started', 'in_progress', 'completed').
        """
        ...

    def get_state(self) -> WorkflowState:
        """Get the current workflow state.

        Returns:
            Current state including active epic/task and all epics.
        """
        ...

    def set_phase(self, task_id: str, phase: str) -> None:
        """Set the TDD phase for a task.

        Args:
            task_id: Task to update.
            phase: TDD phase ('analyze', 'test', 'dev', 'docs', 'review').
        """
        ...

    def set_current_task(self, epic_id: str, task_id: str | None) -> None:
        """Set the current active task.

        Args:
            epic_id: Epic containing the task.
            task_id: Task to set as current, or None to clear.
        """
        ...

    def add_comment(self, task_id: str, comment: str) -> bool:
        """Add a comment to a task.

        Args:
            task_id: Task to comment on.
            comment: Comment text.

        Returns:
            True if comment was added, False if not supported.
        """
        ...

    def create_epic(
        self,
        name: str,
        description: str,
        epic_id: str | None = None,
    ) -> Epic:
        """Create a new epic.

        Args:
            name: Epic name/title.
            description: Epic description with objectives and context.
            epic_id: Optional epic ID (auto-generated if not provided).
                For files backend: E1, E2, etc.
                For Jira: ignored (key assigned by Jira).

        Returns:
            Created Epic instance.

        Raises:
            ValueError: If epic already exists or invalid data.
        """
        ...

    def create_task(
        self,
        epic_id: str,
        title: str,
        description: str,
        acceptance_criteria: str | None = None,
        task_id: str | None = None,
    ) -> Task:
        """Create a new task/story in an epic.

        Args:
            epic_id: Parent epic ID.
            title: Task title/summary.
            description: Full task description.
            acceptance_criteria: Optional acceptance criteria.
            task_id: Optional task ID (auto-generated if not provided).
                For files backend: T1, T2, etc.
                For Jira: ignored (key assigned by Jira).

        Returns:
            Created Task instance.

        Raises:
            KeyError: If epic not found.
            ValueError: If task already exists or invalid data.
        """
        ...
