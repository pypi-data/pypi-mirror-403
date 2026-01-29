"""Tests for files backend."""

import json

import pytest

from tdd_llm.backends.files import FilesBackend


@pytest.fixture
def project_dir(temp_dir):
    """Create a project directory with state files."""
    # Create docs/state.json
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()

    state = {
        "current": {"epic": "E1", "task": None, "phase": None},
        "epics": {
            "E1": {"status": "in_progress", "completed": ["T1"]},
            "E2": {"status": "not_started", "completed": []},
        },
    }
    with open(docs_dir / "state.json", "w") as f:
        json.dump(state, f)

    # Create docs/epics directory
    epics_dir = docs_dir / "epics"
    epics_dir.mkdir()

    # Create E1 epic file
    e1_content = """# E1: Foundation

Set up the project foundation.

## Objective

- Initialize project structure
- Set up basic configuration

## Tasks

| # | Task | Description |
|---|------|-------------|
| T1 | Setup | Initial setup |
| T2 | Config | Configuration |

## T1: Setup

Set up the initial project structure.

**To create:**
- Project skeleton

## T2: Config

Configure the project settings.

**Acceptance criteria:**
- Config file exists
- Tests pass

## Completion criteria

- [ ] Build OK
- [ ] Tests OK
"""
    with open(epics_dir / "e1-foundation.md", "w") as f:
        f.write(e1_content)

    # Create E2 epic file
    e2_content = """# E2: Features

Add main features.

## Tasks

| # | Task | Description |
|---|------|-------------|
| T1 | Feature A | First feature |

## T1: Feature A

Implement the first feature.
"""
    with open(epics_dir / "e2-features.md", "w") as f:
        f.write(e2_content)

    return temp_dir


@pytest.fixture
def backend(project_dir):
    """Create a FilesBackend instance."""
    return FilesBackend(project_root=project_dir)


class TestFilesBackend:
    """Tests for FilesBackend."""

    def test_get_epic(self, backend):
        """Test getting an epic by ID."""
        epic = backend.get_epic("E1")

        assert epic.id == "E1"
        assert epic.name == "Foundation"
        assert "foundation" in epic.description.lower()
        assert epic.status == "in_progress"
        assert len(epic.tasks) == 2

    def test_get_epic_tasks(self, backend):
        """Test that epic tasks are properly loaded."""
        epic = backend.get_epic("E1")

        task1 = next(t for t in epic.tasks if t.id == "T1")
        task2 = next(t for t in epic.tasks if t.id == "T2")

        assert task1.title == "Setup"
        assert task1.status == "completed"  # In completed list

        assert task2.title == "Config"
        assert task2.status == "not_started"

    def test_get_epic_not_found(self, backend):
        """Test getting a non-existent epic."""
        with pytest.raises(KeyError):
            backend.get_epic("E99")

    def test_list_epics(self, backend):
        """Test listing all epics."""
        epics = backend.list_epics()

        assert len(epics) == 2
        epic_ids = [e.id for e in epics]
        assert "E1" in epic_ids
        assert "E2" in epic_ids

    def test_list_epics_filter_status(self, backend):
        """Test listing epics filtered by status."""
        in_progress = backend.list_epics(status="in_progress")
        not_started = backend.list_epics(status="not_started")

        assert len(in_progress) == 1
        assert in_progress[0].id == "E1"

        assert len(not_started) == 1
        assert not_started[0].id == "E2"

    def test_get_task(self, backend):
        """Test getting a task by ID."""
        task = backend.get_task("T2")

        assert task.id == "T2"
        assert task.title == "Config"

    def test_get_task_not_found(self, backend):
        """Test getting a non-existent task."""
        with pytest.raises(KeyError):
            backend.get_task("T99")

    def test_get_next_task(self, backend):
        """Test getting the next incomplete task."""
        next_task = backend.get_next_task("E1")

        assert next_task is not None
        assert next_task.id == "T2"  # T1 is completed

    def test_get_next_task_all_completed(self, backend, project_dir):
        """Test getting next task when all are completed."""
        # Update state to have all tasks completed
        state_file = project_dir / "docs" / "state.json"
        with open(state_file) as f:
            state = json.load(f)
        state["epics"]["E1"]["completed"] = ["T1", "T2"]
        with open(state_file, "w") as f:
            json.dump(state, f)

        next_task = backend.get_next_task("E1")
        assert next_task is None

    def test_get_state(self, backend):
        """Test getting workflow state."""
        state = backend.get_state()

        assert state.backend == "files"
        assert state.current_epic is not None
        assert state.current_epic.id == "E1"
        assert len(state.epics) == 2

    def test_set_phase(self, backend, project_dir):
        """Test setting the TDD phase."""
        # First set a current task
        backend.set_current_task("E1", "T2")

        # Then set the phase
        backend.set_phase("T2", "test")

        # Verify local state was updated
        local_state_file = project_dir / ".tdd-state.local.json"
        with open(local_state_file) as f:
            local_state = json.load(f)

        assert local_state["current"]["phase"] == "test"

    def test_set_current_task(self, backend, project_dir):
        """Test setting the current task."""
        backend.set_current_task("E1", "T2")

        local_state_file = project_dir / ".tdd-state.local.json"
        with open(local_state_file) as f:
            local_state = json.load(f)

        assert local_state["current"]["epic"] == "E1"
        assert local_state["current"]["task"] == "T2"

    def test_update_task_status_completed(self, backend, project_dir):
        """Test marking a task as completed."""
        # Set current task first
        backend.set_current_task("E1", "T2")

        # Complete the task
        backend.update_task_status("T2", "completed")

        # Verify state.json was updated
        state_file = project_dir / "docs" / "state.json"
        with open(state_file) as f:
            state = json.load(f)

        assert "T2" in state["epics"]["E1"]["completed"]


class TestFilesBackendCreateEpic:
    """Tests for FilesBackend.create_epic."""

    def test_create_epic_auto_id(self, backend, project_dir):
        """Test creating an epic with auto-generated ID."""
        epic = backend.create_epic(
            name="New Epic",
            description="This is a new epic for testing.",
        )

        assert epic.id == "E3"  # E1 and E2 already exist
        assert epic.name == "New Epic"
        assert epic.description == "This is a new epic for testing."
        assert epic.status == "not_started"
        assert len(epic.tasks) == 0

        # Verify file was created
        epic_file = project_dir / "docs" / "epics" / "e3-new-epic.md"
        assert epic_file.exists()
        content = epic_file.read_text()
        assert "# E3: New Epic" in content
        assert "This is a new epic for testing." in content

        # Verify state was updated
        state_file = project_dir / "docs" / "state.json"
        with open(state_file) as f:
            state = json.load(f)
        assert "E3" in state["epics"]
        assert state["epics"]["E3"]["status"] == "not_started"

    def test_create_epic_with_id(self, backend, project_dir):
        """Test creating an epic with a specific ID."""
        epic = backend.create_epic(
            name="Custom ID Epic",
            description="Epic with custom ID.",
            epic_id="E10",
        )

        assert epic.id == "E10"
        epic_file = project_dir / "docs" / "epics" / "e10-custom-id-epic.md"
        assert epic_file.exists()

    def test_create_epic_duplicate_id_fails(self, backend):
        """Test that creating an epic with existing ID fails."""
        with pytest.raises(ValueError) as exc_info:
            backend.create_epic(
                name="Duplicate",
                description="Should fail.",
                epic_id="E1",
            )
        assert "already exists" in str(exc_info.value)


class TestFilesBackendCreateTask:
    """Tests for FilesBackend.create_task."""

    def test_create_task_auto_id(self, backend, project_dir):
        """Test creating a task with auto-generated ID."""
        task = backend.create_task(
            epic_id="E1",
            title="New Task",
            description="This is a new task.",
        )

        assert task.id == "T3"  # T1 and T2 already exist in E1
        assert task.epic_id == "E1"
        assert task.title == "New Task"
        assert task.description == "This is a new task."
        assert task.status == "not_started"

        # Verify file was updated
        epic_file = project_dir / "docs" / "epics" / "e1-foundation.md"
        content = epic_file.read_text()
        assert "## T3: New Task" in content
        assert "This is a new task." in content

    def test_create_task_with_acceptance_criteria(self, backend, project_dir):
        """Test creating a task with acceptance criteria."""
        task = backend.create_task(
            epic_id="E1",
            title="Task with AC",
            description="Task description.",
            acceptance_criteria="- [ ] Test passes\n- [ ] Docs updated",
        )

        assert task.acceptance_criteria == "- [ ] Test passes\n- [ ] Docs updated"

        # Verify AC in file
        epic_file = project_dir / "docs" / "epics" / "e1-foundation.md"
        content = epic_file.read_text()
        assert "**Acceptance Criteria:**" in content
        assert "Test passes" in content

    def test_create_task_with_specific_id(self, backend, project_dir):
        """Test creating a task with a specific ID."""
        task = backend.create_task(
            epic_id="E1",
            title="Custom ID Task",
            description="Task with custom ID.",
            task_id="T10",
        )

        assert task.id == "T10"

    def test_create_task_epic_not_found(self, backend):
        """Test creating a task in non-existent epic fails."""
        with pytest.raises(KeyError):
            backend.create_task(
                epic_id="E99",
                title="Should Fail",
                description="This should fail.",
            )

    def test_create_task_normalizes_epic_id(self, backend):
        """Test that epic ID is normalized (E prefix added)."""
        task = backend.create_task(
            epic_id="1",  # Without E prefix
            title="Normalized Epic",
            description="Should work with normalized ID.",
        )

        assert task.epic_id == "E1"


class TestFilesBackendNoState:
    """Tests for FilesBackend when state files don't exist."""

    def test_missing_state_file(self, temp_dir):
        """Test error when state.json is missing."""
        backend = FilesBackend(project_root=temp_dir)

        with pytest.raises(FileNotFoundError) as exc_info:
            backend.get_state()

        assert "init" in str(exc_info.value).lower()

    def test_creates_local_state_on_first_access(self, project_dir):
        """Test that local state is created when first accessed."""
        local_state_file = project_dir / ".tdd-state.local.json"

        # Ensure it doesn't exist
        if local_state_file.exists():
            local_state_file.unlink()

        backend = FilesBackend(project_root=project_dir)

        # Access state - should create local state
        backend.get_state()

        assert local_state_file.exists()
        with open(local_state_file) as f:
            local_state = json.load(f)
        assert "current" in local_state
