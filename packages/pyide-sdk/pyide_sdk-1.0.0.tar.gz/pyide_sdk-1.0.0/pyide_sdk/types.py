"""
Type Definitions for PyIDE SDK

This module contains dataclasses and type definitions used throughout the SDK.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum


@dataclass
class FileEvent:
    """Event data for file-related hooks."""

    filepath: str
    filename: str
    extension: str
    content: Optional[str] = None
    old_path: Optional[str] = None  # For rename events
    is_new: bool = False
    is_modified: bool = False

    @property
    def is_python(self) -> bool:
        """Check if this is a Python file."""
        return self.extension.lower() in (".py", ".pyw", ".pyi")


@dataclass
class EditorEvent:
    """Event data for editor-related hooks."""

    filepath: Optional[str]
    content: str
    cursor_line: int
    cursor_column: int
    selection_start: Optional[Dict[str, int]] = None
    selection_end: Optional[Dict[str, int]] = None
    language: str = "python"

    @property
    def has_selection(self) -> bool:
        """Check if there's an active selection."""
        return self.selection_start is not None and self.selection_end is not None

    @property
    def selected_text(self) -> Optional[str]:
        """Get the selected text if any."""
        if not self.has_selection:
            return None
        lines = self.content.split("\n")
        # Simplified - actual implementation would handle multi-line
        return None


@dataclass
class MenuAction:
    """Definition of a menu action."""

    id: str
    label: str
    menu_path: str  # e.g., "Tools/My Plugin"
    shortcut: Optional[str] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    callback: Optional[str] = None  # Method name to call


@dataclass
class PluginConfig:
    """Plugin configuration schema."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: str = ""
    repository: str = ""
    license: str = "MIT"
    keywords: List[str] = field(default_factory=list)

    # Requirements
    min_pyide_version: str = "1.0.0"
    python_requires: str = ">=3.8"
    dependencies: List[str] = field(default_factory=list)

    # Plugin entry
    main: str = ""  # Main module path
    activationEvents: List[str] = field(default_factory=list)

    # Contributions
    commands: List[Dict[str, str]] = field(default_factory=list)
    menus: List[MenuAction] = field(default_factory=list)
    keybindings: List[Dict[str, str]] = field(default_factory=list)
    settings: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DiagnosticItem:
    """A diagnostic (error/warning) item."""

    filepath: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    message: str = ""
    severity: str = "error"  # "error", "warning", "info", "hint"
    source: str = ""
    code: Optional[str] = None
    related_info: List[Dict[str, Any]] = field(default_factory=list)


class Severity(Enum):
    """Diagnostic severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class CompletionItem:
    """A code completion item."""

    label: str
    kind: str = "text"  # "text", "method", "function", "class", "variable", etc.
    detail: str = ""
    documentation: str = ""
    insert_text: Optional[str] = None
    sort_text: Optional[str] = None
    filter_text: Optional[str] = None


class CompletionItemKind(Enum):
    """Types of completion items."""

    TEXT = "text"
    METHOD = "method"
    FUNCTION = "function"
    CONSTRUCTOR = "constructor"
    FIELD = "field"
    VARIABLE = "variable"
    CLASS = "class"
    INTERFACE = "interface"
    MODULE = "module"
    PROPERTY = "property"
    UNIT = "unit"
    VALUE = "value"
    ENUM = "enum"
    KEYWORD = "keyword"
    SNIPPET = "snippet"
    COLOR = "color"
    FILE = "file"
    REFERENCE = "reference"
    FOLDER = "folder"
    CONSTANT = "constant"


@dataclass
class Position:
    """A position in a text document."""

    line: int  # 1-indexed
    column: int  # 1-indexed

    def to_dict(self) -> Dict[str, int]:
        return {"line": self.line, "column": self.column}


@dataclass
class Range:
    """A range in a text document."""

    start: Position
    end: Position

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict()
        }


@dataclass
class TextEdit:
    """A text edit operation."""

    range: Range
    new_text: str


@dataclass
class WorkspaceEdit:
    """A workspace edit containing multiple file edits."""

    changes: Dict[str, List[TextEdit]] = field(default_factory=dict)

    def add_edit(self, filepath: str, edit: TextEdit) -> None:
        """Add an edit to a file."""
        if filepath not in self.changes:
            self.changes[filepath] = []
        self.changes[filepath].append(edit)


@dataclass
class GitStatus:
    """Git repository status."""

    is_repo: bool
    branch: str = ""
    remote: str = ""
    ahead: int = 0
    behind: int = 0
    staged: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    untracked: List[str] = field(default_factory=list)
    conflicted: List[str] = field(default_factory=list)


@dataclass
class CodeAction:
    """A code action (quick fix, refactoring, etc.)."""

    title: str
    kind: str = "quickfix"  # "quickfix", "refactor", "source"
    diagnostics: List[DiagnosticItem] = field(default_factory=list)
    edit: Optional[WorkspaceEdit] = None
    command: Optional[str] = None
    is_preferred: bool = False


@dataclass
class HoverInfo:
    """Information to display on hover."""

    contents: Union[str, List[str]]
    range: Optional[Range] = None


@dataclass
class SymbolInfo:
    """Information about a symbol (function, class, variable)."""

    name: str
    kind: str
    location: Range
    container_name: Optional[str] = None
    detail: str = ""


class SymbolKind(Enum):
    """Types of symbols."""

    FILE = "file"
    MODULE = "module"
    NAMESPACE = "namespace"
    PACKAGE = "package"
    CLASS = "class"
    METHOD = "method"
    PROPERTY = "property"
    FIELD = "field"
    CONSTRUCTOR = "constructor"
    ENUM = "enum"
    INTERFACE = "interface"
    FUNCTION = "function"
    VARIABLE = "variable"
    CONSTANT = "constant"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    KEY = "key"
    NULL = "null"
