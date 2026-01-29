"""Backend abstraction for TDD workflow state management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from .base import Backend, Epic, Task, WorkflowState

if TYPE_CHECKING:
    from ..config import Config

__all__ = ["Backend", "Epic", "Task", "WorkflowState", "get_backend"]


def get_backend(config: Config) -> Backend:
    """Factory function to get backend instance based on configuration.

    Args:
        config: TDD-LLM configuration with backend settings.

    Returns:
        Backend instance (FilesBackend or JiraBackend).

    Raises:
        ValueError: If backend type is not supported.
    """
    backend_type: Literal["files", "jira"] = config.default_backend

    if backend_type == "files":
        from .files import FilesBackend

        return FilesBackend()

    if backend_type == "jira":
        from .jira import JiraBackend

        return JiraBackend(config.jira)

    raise ValueError(f"Unknown backend type: {backend_type}")
