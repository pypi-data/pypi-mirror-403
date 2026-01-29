"""Tests for backend base types."""


from tdd_llm.backends.base import Epic, Task, WorkflowState


class TestTask:
    """Tests for Task dataclass."""

    def test_create_task(self):
        """Test creating a task with all fields."""
        task = Task(
            id="T1",
            epic_id="E1",
            title="Test task",
            description="Test description",
            status="not_started",
            acceptance_criteria="Should pass tests",
            phase="test",
        )
        assert task.id == "T1"
        assert task.epic_id == "E1"
        assert task.title == "Test task"
        assert task.description == "Test description"
        assert task.status == "not_started"
        assert task.acceptance_criteria == "Should pass tests"
        assert task.phase == "test"

    def test_create_task_minimal(self):
        """Test creating a task with minimal fields."""
        task = Task(
            id="T1",
            epic_id="E1",
            title="Test task",
            description="Test description",
            status="not_started",
        )
        assert task.acceptance_criteria is None
        assert task.phase is None


class TestEpic:
    """Tests for Epic dataclass."""

    def test_create_epic(self):
        """Test creating an epic with tasks."""
        tasks = [
            Task(id="T1", epic_id="E1", title="Task 1", description="", status="completed"),
            Task(id="T2", epic_id="E1", title="Task 2", description="", status="in_progress"),
            Task(id="T3", epic_id="E1", title="Task 3", description="", status="not_started"),
        ]
        epic = Epic(
            id="E1",
            name="Test Epic",
            description="Epic description",
            status="in_progress",
            tasks=tasks,
        )
        assert epic.id == "E1"
        assert epic.name == "Test Epic"
        assert len(epic.tasks) == 3

    def test_completed_count(self):
        """Test completed task count calculation."""
        tasks = [
            Task(id="T1", epic_id="E1", title="Task 1", description="", status="completed"),
            Task(id="T2", epic_id="E1", title="Task 2", description="", status="completed"),
            Task(id="T3", epic_id="E1", title="Task 3", description="", status="not_started"),
        ]
        epic = Epic(
            id="E1",
            name="Test Epic",
            description="",
            status="in_progress",
            tasks=tasks,
        )
        assert epic.completed_count == 2

    def test_progress(self):
        """Test progress string calculation."""
        tasks = [
            Task(id="T1", epic_id="E1", title="Task 1", description="", status="completed"),
            Task(id="T2", epic_id="E1", title="Task 2", description="", status="not_started"),
        ]
        epic = Epic(
            id="E1",
            name="Test Epic",
            description="",
            status="in_progress",
            tasks=tasks,
        )
        assert epic.progress == "1/2"

    def test_empty_epic(self):
        """Test epic with no tasks."""
        epic = Epic(
            id="E1",
            name="Empty Epic",
            description="",
            status="not_started",
        )
        assert epic.tasks == []
        assert epic.completed_count == 0
        assert epic.progress == "0/0"


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""

    def test_create_state(self):
        """Test creating a workflow state."""
        epic = Epic(id="E1", name="Epic", description="", status="in_progress")
        task = Task(id="T1", epic_id="E1", title="Task", description="", status="in_progress")

        state = WorkflowState(
            backend="files",
            current_epic=epic,
            current_task=task,
            epics=[epic],
        )

        assert state.backend == "files"
        assert state.current_epic is not None
        assert state.current_epic.id == "E1"
        assert state.current_task is not None
        assert state.current_task.id == "T1"

    def test_empty_state(self):
        """Test workflow state with no current task."""
        state = WorkflowState(
            backend="jira",
            current_epic=None,
            current_task=None,
            epics=[],
        )

        assert state.backend == "jira"
        assert state.current_epic is None
        assert state.current_task is None
        assert state.epics == []
