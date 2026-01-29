"""
PyIDE API for Plugin Developers

This module provides the API interface for plugins to interact with PyIDE.
"""

from typing import Optional, List, Dict, Any, Callable, Union
from abc import ABC, abstractmethod


class PyIDEAPI(ABC):
    """
    Abstract base class defining the PyIDE API interface.

    Plugins receive an instance of this class to interact with the IDE.
    All methods are designed to be called from plugin code.
    """

    # ==================== Editor Operations ====================

    @abstractmethod
    def get_current_editor(self) -> Optional["EditorAPI"]:
        """Get the currently active editor instance."""
        pass

    @abstractmethod
    def get_editor_content(self) -> str:
        """Get the content of the current editor."""
        pass

    @abstractmethod
    def set_editor_content(self, content: str) -> None:
        """Set the content of the current editor."""
        pass

    @abstractmethod
    def get_selection(self) -> Optional[Dict[str, Any]]:
        """
        Get the current selection.

        Returns:
            Dict with keys: text, start_line, start_col, end_line, end_col
            or None if no selection
        """
        pass

    @abstractmethod
    def insert_text(self, text: str, position: Optional[Dict[str, int]] = None) -> None:
        """
        Insert text at position or cursor.

        Args:
            text: Text to insert
            position: Optional dict with 'line' and 'column' keys
        """
        pass

    @abstractmethod
    def replace_selection(self, text: str) -> None:
        """Replace the current selection with text."""
        pass

    @abstractmethod
    def get_cursor_position(self) -> Dict[str, int]:
        """
        Get current cursor position.

        Returns:
            Dict with 'line' and 'column' keys
        """
        pass

    @abstractmethod
    def set_cursor_position(self, line: int, column: int) -> None:
        """Set the cursor position."""
        pass

    @abstractmethod
    def get_line(self, line_number: int) -> str:
        """Get the content of a specific line."""
        pass

    @abstractmethod
    def get_line_count(self) -> int:
        """Get the total number of lines."""
        pass

    # ==================== File Operations ====================

    @abstractmethod
    def get_current_file_path(self) -> Optional[str]:
        """Get the path of the currently open file."""
        pass

    @abstractmethod
    def open_file(self, filepath: str) -> bool:
        """
        Open a file in the editor.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def save_file(self, filepath: Optional[str] = None) -> bool:
        """
        Save the current file.

        Args:
            filepath: Optional path for "Save As" behavior

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def create_file(self, filepath: str, content: str = "") -> bool:
        """Create a new file with optional content."""
        pass

    @abstractmethod
    def read_file(self, filepath: str) -> Optional[str]:
        """Read file content."""
        pass

    @abstractmethod
    def file_exists(self, filepath: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    def get_workspace_path(self) -> Optional[str]:
        """Get the current workspace/folder path."""
        pass

    # ==================== UI Operations ====================

    @abstractmethod
    def show_notification(
        self,
        message: str,
        type: str = "info",
        duration: int = 3000
    ) -> None:
        """
        Show a notification toast.

        Args:
            message: Notification message
            type: "info", "success", "warning", or "error"
            duration: Display duration in milliseconds
        """
        pass

    @abstractmethod
    def show_message_box(
        self,
        title: str,
        message: str,
        buttons: List[str] = None,
        type: str = "info"
    ) -> str:
        """
        Show a message box dialog.

        Args:
            title: Dialog title
            message: Message content
            buttons: List of button labels (default: ["OK"])
            type: "info", "warning", "error", "question"

        Returns:
            The label of the clicked button
        """
        pass

    @abstractmethod
    def show_input_dialog(
        self,
        title: str,
        prompt: str,
        default_value: str = "",
        placeholder: str = ""
    ) -> Optional[str]:
        """
        Show an input dialog.

        Returns:
            User input or None if cancelled
        """
        pass

    @abstractmethod
    def show_quick_pick(
        self,
        items: List[Union[str, Dict[str, str]]],
        placeholder: str = "",
        can_pick_many: bool = False
    ) -> Optional[Union[str, List[str]]]:
        """
        Show a quick pick selection dialog.

        Args:
            items: List of items (strings or dicts with 'label', 'description')
            placeholder: Placeholder text
            can_pick_many: Allow multiple selections

        Returns:
            Selected item(s) or None if cancelled
        """
        pass

    @abstractmethod
    def show_file_dialog(
        self,
        type: str = "open",
        filters: List[Dict[str, List[str]]] = None,
        default_path: str = ""
    ) -> Optional[str]:
        """
        Show a file open/save dialog.

        Args:
            type: "open" or "save"
            filters: File type filters [{"name": "Python", "extensions": ["py"]}]
            default_path: Default file path

        Returns:
            Selected file path or None if cancelled
        """
        pass

    # ==================== Output & Terminal ====================

    @abstractmethod
    def write_output(self, text: str, channel: str = "output") -> None:
        """
        Write to an output channel.

        Args:
            text: Text to write
            channel: "output", "terminal", or custom channel name
        """
        pass

    @abstractmethod
    def clear_output(self, channel: str = "output") -> None:
        """Clear an output channel."""
        pass

    @abstractmethod
    def run_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a shell command.

        Returns:
            Dict with 'stdout', 'stderr', 'exit_code'
        """
        pass

    # ==================== Code Execution ====================

    @abstractmethod
    def run_python(self, code: str) -> Dict[str, Any]:
        """
        Run Python code.

        Returns:
            Dict with 'output', 'error', 'exit_code'
        """
        pass

    @abstractmethod
    def stop_execution(self) -> None:
        """Stop any running code execution."""
        pass

    # ==================== Command Registration ====================

    @abstractmethod
    def register_command(
        self,
        name: str,
        callback: Callable,
        description: str = ""
    ) -> None:
        """Register a command."""
        pass

    @abstractmethod
    def execute_command(self, name: str, *args, **kwargs) -> Any:
        """Execute a registered command."""
        pass

    @abstractmethod
    def register_keybinding(self, keys: str, command: str) -> None:
        """Register a keyboard shortcut."""
        pass

    # ==================== Settings ====================

    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a PyIDE setting value."""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """Set a PyIDE setting value."""
        pass

    # ==================== Git Operations ====================

    @abstractmethod
    def git_status(self) -> Dict[str, Any]:
        """Get git status of current workspace."""
        pass

    @abstractmethod
    def git_commit(self, message: str) -> bool:
        """Create a git commit."""
        pass

    @abstractmethod
    def git_push(self) -> bool:
        """Push to remote."""
        pass

    @abstractmethod
    def git_pull(self) -> bool:
        """Pull from remote."""
        pass

    # ==================== Diagnostics ====================

    @abstractmethod
    def add_diagnostic(
        self,
        filepath: str,
        line: int,
        column: int,
        message: str,
        severity: str = "error",
        source: str = ""
    ) -> None:
        """
        Add a diagnostic (error/warning marker).

        Args:
            filepath: File path
            line: Line number (1-indexed)
            column: Column number (1-indexed)
            message: Diagnostic message
            severity: "error", "warning", "info", "hint"
            source: Source identifier (e.g., plugin name)
        """
        pass

    @abstractmethod
    def clear_diagnostics(self, filepath: Optional[str] = None, source: Optional[str] = None) -> None:
        """Clear diagnostics, optionally filtered by file or source."""
        pass


class EditorAPI(ABC):
    """API for a specific editor instance."""

    @abstractmethod
    def get_content(self) -> str:
        """Get editor content."""
        pass

    @abstractmethod
    def set_content(self, content: str) -> None:
        """Set editor content."""
        pass

    @abstractmethod
    def get_language(self) -> str:
        """Get the editor's language mode."""
        pass

    @abstractmethod
    def set_language(self, language: str) -> None:
        """Set the editor's language mode."""
        pass

    @abstractmethod
    def format_document(self) -> None:
        """Format the document."""
        pass

    @abstractmethod
    def fold_all(self) -> None:
        """Fold all foldable regions."""
        pass

    @abstractmethod
    def unfold_all(self) -> None:
        """Unfold all regions."""
        pass

    @abstractmethod
    def go_to_line(self, line: int) -> None:
        """Navigate to a line."""
        pass

    @abstractmethod
    def reveal_range(self, start_line: int, end_line: int) -> None:
        """Scroll to reveal a range."""
        pass


class MockPyIDEAPI(PyIDEAPI):
    """
    Mock implementation of PyIDEAPI for testing plugins.

    Use this class when developing and testing plugins outside of PyIDE.
    """

    def __init__(self):
        self._content = ""
        self._cursor = {"line": 1, "column": 1}
        self._selection = None
        self._filepath = None
        self._workspace = None
        self._settings = {}
        self._commands = {}
        self._output = []

    def get_current_editor(self):
        return None

    def get_editor_content(self) -> str:
        return self._content

    def set_editor_content(self, content: str) -> None:
        self._content = content

    def get_selection(self):
        return self._selection

    def insert_text(self, text: str, position=None) -> None:
        self._content += text

    def replace_selection(self, text: str) -> None:
        self._content = text

    def get_cursor_position(self):
        return self._cursor

    def set_cursor_position(self, line: int, column: int) -> None:
        self._cursor = {"line": line, "column": column}

    def get_line(self, line_number: int) -> str:
        lines = self._content.split("\n")
        if 0 < line_number <= len(lines):
            return lines[line_number - 1]
        return ""

    def get_line_count(self) -> int:
        return len(self._content.split("\n"))

    def get_current_file_path(self):
        return self._filepath

    def open_file(self, filepath: str) -> bool:
        self._filepath = filepath
        return True

    def save_file(self, filepath=None) -> bool:
        return True

    def create_file(self, filepath: str, content: str = "") -> bool:
        return True

    def read_file(self, filepath: str):
        return None

    def file_exists(self, filepath: str) -> bool:
        return False

    def get_workspace_path(self):
        return self._workspace

    def show_notification(self, message: str, type: str = "info", duration: int = 3000) -> None:
        print(f"[{type.upper()}] {message}")

    def show_message_box(self, title: str, message: str, buttons=None, type: str = "info") -> str:
        return buttons[0] if buttons else "OK"

    def show_input_dialog(self, title: str, prompt: str, default_value: str = "", placeholder: str = ""):
        return default_value

    def show_quick_pick(self, items, placeholder: str = "", can_pick_many: bool = False):
        return items[0] if items else None

    def show_file_dialog(self, type: str = "open", filters=None, default_path: str = ""):
        return None

    def write_output(self, text: str, channel: str = "output") -> None:
        self._output.append(text)
        print(text)

    def clear_output(self, channel: str = "output") -> None:
        self._output.clear()

    def run_command(self, command: str, cwd=None):
        return {"stdout": "", "stderr": "", "exit_code": 0}

    def run_python(self, code: str):
        return {"output": "", "error": "", "exit_code": 0}

    def stop_execution(self) -> None:
        pass

    def register_command(self, name: str, callback: Callable, description: str = "") -> None:
        self._commands[name] = callback

    def execute_command(self, name: str, *args, **kwargs):
        if name in self._commands:
            return self._commands[name](*args, **kwargs)

    def register_keybinding(self, keys: str, command: str) -> None:
        pass

    def get_setting(self, key: str, default=None):
        return self._settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        self._settings[key] = value

    def git_status(self):
        return {"branch": "main", "files": [], "is_repo": False}

    def git_commit(self, message: str) -> bool:
        return True

    def git_push(self) -> bool:
        return True

    def git_pull(self) -> bool:
        return True

    def add_diagnostic(self, filepath, line, column, message, severity="error", source="") -> None:
        pass

    def clear_diagnostics(self, filepath=None, source=None) -> None:
        pass
