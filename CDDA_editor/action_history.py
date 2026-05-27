from __future__ import annotations

from dataclasses import dataclass

try:
    from .project import ModProject, ProjectEditState
except ImportError:
    from project import ModProject, ProjectEditState


@dataclass(frozen=True)
class ProjectAction:
    label: str
    before: ProjectEditState
    after: ProjectEditState


class ProjectActionHistory:
    def __init__(self, project: ModProject) -> None:
        self.project = project
        self._undo_stack: list[ProjectAction] = []
        self._redo_stack: list[ProjectAction] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    def capture(self) -> ProjectEditState:
        return self.project.capture_edit_state()

    def record(self, label: str, before: ProjectEditState) -> bool:
        after = self.capture()
        if before == after:
            return False
        self._undo_stack.append(ProjectAction(label=label, before=before, after=after))
        self._redo_stack.clear()
        return True

    def undo(self) -> ProjectAction:
        if not self._undo_stack:
            raise RuntimeError("No project action to undo")
        action = self._undo_stack.pop()
        self.project.restore_edit_state(action.before)
        self._redo_stack.append(action)
        return action

    def redo(self) -> ProjectAction:
        if not self._redo_stack:
            raise RuntimeError("No project action to redo")
        action = self._redo_stack.pop()
        self.project.restore_edit_state(action.after)
        self._undo_stack.append(action)
        return action
