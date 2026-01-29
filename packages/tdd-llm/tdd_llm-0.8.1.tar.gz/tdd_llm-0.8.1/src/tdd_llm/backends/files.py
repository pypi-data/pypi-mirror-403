"""Files backend for TDD workflow state management.

Uses local files for state storage:
- docs/state.json: Global project state (epics, completion)
- .tdd-state.local.json: Session state (current task, phase)
- docs/epics/*.md: Epic and task definitions
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .base import Backend, Epic, Task, WorkflowState

# File paths relative to project root
STATE_FILE = "docs/state.json"
LOCAL_STATE_FILE = ".tdd-state.local.json"
EPICS_DIR = "docs/epics"


class FilesBackend:
    """Backend using local files for TDD workflow state."""

    def __init__(self, project_root: Path | None = None):
        """Initialize files backend.

        Args:
            project_root: Project root directory. Defaults to cwd.
        """
        self.project_root = project_root or Path.cwd()

    @property
    def state_path(self) -> Path:
        """Path to global state file."""
        return self.project_root / STATE_FILE

    @property
    def local_state_path(self) -> Path:
        """Path to local session state file."""
        return self.project_root / LOCAL_STATE_FILE

    @property
    def epics_dir(self) -> Path:
        """Path to epics directory."""
        return self.project_root / EPICS_DIR

    def _load_state(self) -> dict:
        """Load global state from docs/state.json."""
        if not self.state_path.exists():
            raise FileNotFoundError(
                f"Project not initialized. Run '/tdd:init:1-project' first. "
                f"(Missing: {self.state_path})"
            )
        with open(self.state_path, encoding="utf-8") as f:
            return json.load(f)

    def _save_state(self, state: dict) -> None:
        """Save global state to docs/state.json."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def _load_local_state(self) -> dict:
        """Load local session state from .tdd-state.local.json."""
        if not self.local_state_path.exists():
            # Create default local state
            state = self._load_state()
            current_epic = state.get("current", {}).get("epic", "E0")
            local_state = {
                "current": {
                    "epic": current_epic,
                    "task": None,
                    "phase": None,
                    "skip_phases": [],
                }
            }
            self._save_local_state(local_state)
            return local_state

        with open(self.local_state_path, encoding="utf-8") as f:
            return json.load(f)

    def _save_local_state(self, state: dict) -> None:
        """Save local session state to .tdd-state.local.json."""
        with open(self.local_state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def _find_epic_file(self, epic_id: str) -> Path | None:
        """Find the markdown file for an epic.

        Looks for files matching pattern: e{n}-*.md or E{n}.md
        """
        if not self.epics_dir.exists():
            return None

        # Normalize epic_id (E1 -> e1)
        epic_lower = epic_id.lower()

        for file in self.epics_dir.glob("*.md"):
            # Match e1-name.md or e1.md
            if file.stem.lower().startswith(epic_lower):
                return file

        return None

    def _parse_epic_file(self, epic_id: str) -> tuple[str, str, list[dict]]:
        """Parse an epic markdown file.

        Returns:
            Tuple of (name, description, tasks_list).
        """
        file_path = self._find_epic_file(epic_id)
        if not file_path:
            raise KeyError(f"Epic file not found for {epic_id}")

        content = file_path.read_text(encoding="utf-8")

        # Parse title: # E{N}: {Name} or # E{N} - {Name}
        title_match = re.search(r"^#\s+E\d+[:\-]\s*(.+)$", content, re.MULTILINE)
        name = title_match.group(1).strip() if title_match else epic_id

        # Parse description (text between title and first ## section)
        desc_match = re.search(
            r"^#\s+E\d+[:\-].+?\n\n(.+?)(?=\n##|\Z)", content, re.DOTALL | re.MULTILINE
        )
        description = desc_match.group(1).strip() if desc_match else ""

        # Parse task sections: ## T{N}: {Title} or ### T{N}: {Title}
        tasks = []
        task_pattern = re.compile(
            r"^#{2,3}\s+(T\d+):\s*(.+?)$\n\n(.+?)(?=\n#{2,3}\s+T\d+:|\n#{2,3}\s+Completion|\n#{2,3}\s+Estimation|\Z)",
            re.MULTILINE | re.DOTALL,
        )

        for match in task_pattern.finditer(content):
            task_id = match.group(1)
            task_title = match.group(2).strip()
            task_desc = match.group(3).strip()

            # Try to extract acceptance criteria if in task description
            ac_match = re.search(
                r"\*\*Acceptance criteria:?\*\*\s*\n(.+?)(?=\n\*\*|\Z)",
                task_desc,
                re.DOTALL | re.IGNORECASE,
            )
            acceptance_criteria = ac_match.group(1).strip() if ac_match else None

            tasks.append(
                {
                    "id": task_id,
                    "title": task_title,
                    "description": task_desc,
                    "acceptance_criteria": acceptance_criteria,
                }
            )

        # Also look for task files in E{N}/ subdirectory
        tasks.extend(self._parse_task_files(epic_id))

        return name, description, tasks

    def _parse_task_files(self, epic_id: str) -> list[dict]:
        """Parse task files from E{N}/ subdirectory.

        Args:
            epic_id: Epic ID (e.g., 'E1').

        Returns:
            List of task dicts.
        """
        tasks = []
        task_dir = self.epics_dir / epic_id

        if not task_dir.is_dir():
            return tasks

        # Find task files: T1.md, T2.md, etc. (not T1-context.md)
        for task_file in sorted(task_dir.glob("T*.md")):
            # Skip context files like T1-context.md
            if "-" in task_file.stem:
                continue

            task_id = task_file.stem  # e.g., "T1"
            content = task_file.read_text(encoding="utf-8")

            # Parse title: # [E{N}] T{M} - {Title} or # T{M}: {Title}
            title_match = re.search(
                r"^#\s+(?:\[E\d+\]\s+)?T\d+\s*[:\-]\s*(.+)$", content, re.MULTILINE
            )
            task_title = title_match.group(1).strip() if title_match else task_id

            # Description is everything after the title
            desc_match = re.search(r"^#\s+.+?\n\n(.+)", content, re.DOTALL | re.MULTILINE)
            task_desc = desc_match.group(1).strip() if desc_match else ""

            # Try to extract acceptance criteria
            ac_match = re.search(
                r"\*\*Acceptance criteria:?\*\*\s*\n(.+?)(?=\n\*\*|\Z)",
                task_desc,
                re.DOTALL | re.IGNORECASE,
            )
            acceptance_criteria = ac_match.group(1).strip() if ac_match else None

            tasks.append(
                {
                    "id": task_id,
                    "title": task_title,
                    "description": task_desc,
                    "acceptance_criteria": acceptance_criteria,
                }
            )

        return tasks

    def _get_epic_status(self, epic_id: str, state: dict) -> str:
        """Get epic status from state."""
        epic_state = state.get("epics", {}).get(epic_id, {})
        return epic_state.get("status", "not_started")

    def _get_completed_tasks(self, epic_id: str, state: dict) -> list[str]:
        """Get list of completed task IDs for an epic."""
        epic_state = state.get("epics", {}).get(epic_id, {})
        return epic_state.get("completed", [])

    def get_epic(self, epic_id: str) -> Epic:
        """Get an epic by ID."""
        state = self._load_state()
        local_state = self._load_local_state()

        name, description, task_dicts = self._parse_epic_file(epic_id)
        completed_tasks = self._get_completed_tasks(epic_id, state)

        # Get current task from local state
        current_task_id = None
        current_phase = None
        if local_state.get("current", {}).get("epic") == epic_id:
            current_task_id = local_state["current"].get("task")
            current_phase = local_state["current"].get("phase")

        tasks = []
        for td in task_dicts:
            task_id = td["id"]

            if task_id in completed_tasks:
                status = "completed"
                phase = None
            elif task_id == current_task_id:
                status = "in_progress"
                phase = current_phase
            else:
                status = "not_started"
                phase = None

            tasks.append(
                Task(
                    id=task_id,
                    epic_id=epic_id,
                    title=td["title"],
                    description=td["description"],
                    status=status,
                    acceptance_criteria=td.get("acceptance_criteria"),
                    phase=phase,
                )
            )

        return Epic(
            id=epic_id,
            name=name,
            description=description,
            status=self._get_epic_status(epic_id, state),
            tasks=tasks,
        )

    def list_epics(self, status: str | None = None) -> list[Epic]:
        """List all epics, optionally filtered by status."""
        state = self._load_state()
        epic_ids = list(state.get("epics", {}).keys())

        epics = []
        for epic_id in epic_ids:
            try:
                epic = self.get_epic(epic_id)
                if status is None or epic.status == status:
                    epics.append(epic)
            except KeyError:
                # Epic file not found, skip
                continue

        return epics

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID.

        Note: For files backend, task_id alone is not unique.
        We search through all epics to find the task.
        """
        state = self._load_state()
        local_state = self._load_local_state()

        # First check if it's the current task (we know the epic)
        current_epic_id = local_state.get("current", {}).get("epic")
        current_task_id = local_state.get("current", {}).get("task")

        if task_id == current_task_id and current_epic_id:
            epic = self.get_epic(current_epic_id)
            for task in epic.tasks:
                if task.id == task_id:
                    return task

        # Search all epics
        for epic_id in state.get("epics", {}).keys():
            try:
                epic = self.get_epic(epic_id)
                for task in epic.tasks:
                    if task.id == task_id:
                        return task
            except KeyError:
                continue

        raise KeyError(f"Task not found: {task_id}")

    def get_next_task(self, epic_id: str) -> Task | None:
        """Get the next incomplete task in an epic.

        Returns the first task that is not completed (i.e., not_started or in_progress).
        """
        epic = self.get_epic(epic_id)
        return next((task for task in epic.tasks if task.status != "completed"), None)

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update a task's status."""
        state = self._load_state()
        local_state = self._load_local_state()

        # Find which epic contains this task
        current_epic_id = local_state.get("current", {}).get("epic")

        if status == "completed":
            # Add to completed list
            epic_state = state.get("epics", {}).get(current_epic_id, {})
            completed = epic_state.get("completed", [])
            if task_id not in completed:
                completed.append(task_id)
                state["epics"][current_epic_id]["completed"] = completed

            # Clear current task in local state
            local_state["current"]["task"] = None
            local_state["current"]["phase"] = None

            # Check if epic is now complete
            epic = self.get_epic(current_epic_id)
            if all(t.status == "completed" for t in epic.tasks):
                state["epics"][current_epic_id]["status"] = "completed"

            self._save_state(state)
            self._save_local_state(local_state)

        elif status == "in_progress":
            # Set as current task
            local_state["current"]["task"] = task_id
            state["epics"][current_epic_id]["status"] = "in_progress"
            self._save_state(state)
            self._save_local_state(local_state)

    def get_state(self) -> WorkflowState:
        """Get the current workflow state."""
        self._load_state()  # Validate state file exists
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

        epics = self.list_epics()

        return WorkflowState(
            backend="files",
            current_epic=current_epic,
            current_task=current_task,
            epics=epics,
        )

    def set_phase(self, task_id: str, phase: str) -> None:
        """Set the TDD phase for a task."""
        local_state = self._load_local_state()

        # Verify task is current
        if local_state.get("current", {}).get("task") != task_id:
            raise ValueError(f"Task {task_id} is not the current task")

        local_state["current"]["phase"] = phase
        self._save_local_state(local_state)

    def set_current_task(self, epic_id: str, task_id: str | None) -> None:
        """Set the current active task."""
        state = self._load_state()
        local_state = self._load_local_state()

        local_state["current"]["epic"] = epic_id
        local_state["current"]["task"] = task_id
        local_state["current"]["phase"] = None

        if task_id:
            state["epics"][epic_id]["status"] = "in_progress"
            self._save_state(state)

        self._save_local_state(local_state)

    def add_comment(self, task_id: str, comment: str) -> bool:
        """Add a comment to a task.

        Not supported for files backend.

        Returns:
            False (comments not supported).
        """
        return False

    def _get_next_epic_id(self, state: dict) -> str:
        """Get the next available epic ID."""
        existing_ids = list(state.get("epics", {}).keys())
        if not existing_ids:
            return "E1"

        # Find highest number
        max_num = 0
        for epic_id in existing_ids:
            if epic_id.startswith("E") and epic_id[1:].isdigit():
                max_num = max(max_num, int(epic_id[1:]))
        return f"E{max_num + 1}"

    def _get_next_task_id(self, epic_id: str) -> str:
        """Get the next available task ID for an epic."""
        try:
            _, _, tasks = self._parse_epic_file(epic_id)
            if not tasks:
                return "T1"

            # Find highest number
            max_num = 0
            for task in tasks:
                task_id = task["id"]
                if task_id.startswith("T") and task_id[1:].isdigit():
                    max_num = max(max_num, int(task_id[1:]))
            return f"T{max_num + 1}"
        except KeyError:
            return "T1"

    def _slugify(self, text: str) -> str:
        """Convert text to a URL-friendly slug."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug[:50]  # Limit length

    def create_epic(
        self,
        name: str,
        description: str,
        epic_id: str | None = None,
    ) -> Epic:
        """Create a new epic."""
        state = self._load_state()

        # Generate or validate epic ID
        if epic_id is None:
            epic_id = self._get_next_epic_id(state)
        else:
            # Ensure ID format before checking for existence
            if not epic_id.startswith("E"):
                epic_id = f"E{epic_id}"
            if epic_id in state.get("epics", {}):
                raise ValueError(f"Epic {epic_id} already exists")

        # Create epic file
        self.epics_dir.mkdir(parents=True, exist_ok=True)
        slug = self._slugify(name)
        file_name = f"{epic_id.lower()}-{slug}.md"
        file_path = self.epics_dir / file_name

        # Write epic markdown
        content = f"""# {epic_id}: {name}

{description}

## Completion Criteria

- All tasks completed and verified
- Documentation updated
- Code reviewed and merged
"""
        file_path.write_text(content, encoding="utf-8")

        # Update state.json
        if "epics" not in state:
            state["epics"] = {}
        state["epics"][epic_id] = {
            "status": "not_started",
            "completed": [],
        }
        self._save_state(state)

        return Epic(
            id=epic_id,
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
        """Create a new task/story in an epic."""
        # Normalize epic ID
        if not epic_id.startswith("E"):
            epic_id = f"E{epic_id}"

        # Find epic file
        file_path = self._find_epic_file(epic_id)
        if not file_path:
            raise KeyError(f"Epic file not found for {epic_id}")

        # Generate or validate task ID
        if task_id is None:
            task_id = self._get_next_task_id(epic_id)
        else:
            # Ensure ID format before checking for existence
            if not task_id.startswith("T"):
                task_id = f"T{task_id}"

            # Check if task already exists
            _, _, existing_tasks = self._parse_epic_file(epic_id)
            for t in existing_tasks:
                if t["id"] == task_id:
                    raise ValueError(f"Task {task_id} already exists in {epic_id}")

        # Read existing content
        content = file_path.read_text(encoding="utf-8")

        # Build task section
        task_section = f"\n\n## {task_id}: {title}\n\n{description}"
        if acceptance_criteria:
            task_section += f"\n\n**Acceptance Criteria:**\n{acceptance_criteria}"

        # Insert before "## Completion" if it exists, otherwise append
        completion_match = re.search(r"\n## Completion", content, re.IGNORECASE)
        if completion_match:
            insert_pos = completion_match.start()
            content = content[:insert_pos] + task_section + content[insert_pos:]
        else:
            content = content.rstrip() + task_section + "\n"

        # Write updated content
        file_path.write_text(content, encoding="utf-8")

        return Task(
            id=task_id,
            epic_id=epic_id,
            title=title,
            description=description,
            status="not_started",
            acceptance_criteria=acceptance_criteria,
            phase=None,
        )


# Ensure FilesBackend implements Backend protocol
def _check_protocol() -> None:
    """Type check that FilesBackend implements Backend."""
    _backend: Backend = FilesBackend()  # noqa: F841


_check_protocol()
