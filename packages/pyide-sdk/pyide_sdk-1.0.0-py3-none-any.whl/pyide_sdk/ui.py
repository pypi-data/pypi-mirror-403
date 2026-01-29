"""
UI Extension Components for PyIDE Plugins

This module provides classes for creating custom UI elements in PyIDE.
"""

from typing import Optional, List, Dict, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class UIExtension:
    """Base class for UI extensions."""

    id: str
    title: str
    icon: Optional[str] = None
    enabled: bool = True


@dataclass
class Panel(UIExtension):
    """
    A sidebar or bottom panel extension.

    Example:
        panel = Panel(
            id="my_plugin.panel",
            title="My Panel",
            location="sidebar",
            icon="puzzle"
        )
    """

    location: str = "sidebar"  # "sidebar", "bottom", "floating"
    width: Optional[int] = None
    height: Optional[int] = None
    html_content: str = ""
    on_render: Optional[Callable] = None
    on_message: Optional[Callable[[Dict], None]] = None

    def set_content(self, html: str) -> None:
        """Set the panel's HTML content."""
        self.html_content = html

    def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to the panel's webview."""
        pass  # Implemented by PyIDE

    def show(self) -> None:
        """Show the panel."""
        pass  # Implemented by PyIDE

    def hide(self) -> None:
        """Hide the panel."""
        pass  # Implemented by PyIDE

    def toggle(self) -> None:
        """Toggle panel visibility."""
        pass  # Implemented by PyIDE


@dataclass
class Dialog:
    """
    A custom dialog/modal window.

    Example:
        dialog = Dialog(
            id="my_plugin.settings",
            title="Plugin Settings",
            width=500,
            height=400
        )
    """

    id: str
    title: str
    width: int = 400
    height: int = 300
    modal: bool = True
    resizable: bool = True
    html_content: str = ""
    buttons: List[Dict[str, Any]] = field(default_factory=list)
    on_open: Optional[Callable] = None
    on_close: Optional[Callable] = None
    on_button_click: Optional[Callable[[str], None]] = None

    def set_content(self, html: str) -> None:
        """Set the dialog's HTML content."""
        self.html_content = html

    def add_button(
        self,
        label: str,
        action: str = "close",
        style: str = "default"
    ) -> "Dialog":
        """
        Add a button to the dialog.

        Args:
            label: Button text
            action: "close", "submit", or custom action name
            style: "default", "primary", "danger"
        """
        self.buttons.append({
            "label": label,
            "action": action,
            "style": style
        })
        return self

    def show(self) -> None:
        """Show the dialog."""
        pass  # Implemented by PyIDE

    def close(self) -> None:
        """Close the dialog."""
        pass  # Implemented by PyIDE


@dataclass
class StatusBarItem(UIExtension):
    """
    A status bar item.

    Example:
        status = StatusBarItem(
            id="my_plugin.status",
            title="My Status",
            text="Ready",
            position="right",
            priority=100
        )
    """

    text: str = ""
    tooltip: str = ""
    position: str = "right"  # "left", "center", "right"
    priority: int = 100  # Lower = more prominent
    command: Optional[str] = None  # Command to run on click
    color: Optional[str] = None
    background_color: Optional[str] = None

    def set_text(self, text: str) -> None:
        """Update the status bar text."""
        self.text = text

    def set_tooltip(self, tooltip: str) -> None:
        """Update the tooltip."""
        self.tooltip = tooltip

    def show(self) -> None:
        """Show the status bar item."""
        pass  # Implemented by PyIDE

    def hide(self) -> None:
        """Hide the status bar item."""
        pass  # Implemented by PyIDE


@dataclass
class TreeView:
    """
    A tree view component for sidebar panels.

    Example:
        tree = TreeView(
            id="my_plugin.tree",
            title="My Tree"
        )
        tree.set_items([
            TreeItem("root", "Root Item", children=[
                TreeItem("child1", "Child 1"),
                TreeItem("child2", "Child 2"),
            ])
        ])
    """

    id: str
    title: str
    items: List["TreeItem"] = field(default_factory=list)
    on_select: Optional[Callable[["TreeItem"], None]] = None
    on_expand: Optional[Callable[["TreeItem"], None]] = None
    on_collapse: Optional[Callable[["TreeItem"], None]] = None

    def set_items(self, items: List["TreeItem"]) -> None:
        """Set the tree items."""
        self.items = items

    def refresh(self) -> None:
        """Refresh the tree view."""
        pass  # Implemented by PyIDE

    def reveal(self, item_id: str) -> None:
        """Reveal and select an item."""
        pass  # Implemented by PyIDE


@dataclass
class TreeItem:
    """A tree view item."""

    id: str
    label: str
    description: str = ""
    icon: Optional[str] = None
    children: List["TreeItem"] = field(default_factory=list)
    collapsible: bool = True
    expanded: bool = False
    context_value: str = ""  # For context menu filtering
    data: Any = None  # Custom data


@dataclass
class Webview(UIExtension):
    """
    A webview panel for rich HTML content.

    Example:
        webview = Webview(
            id="my_plugin.webview",
            title="My Webview"
        )
        webview.set_html("<h1>Hello World</h1>")
    """

    html: str = ""
    scripts: List[str] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)
    enable_scripts: bool = True
    retain_context: bool = True
    on_message: Optional[Callable[[Dict], None]] = None

    def set_html(self, html: str) -> None:
        """Set the webview HTML content."""
        self.html = html

    def post_message(self, message: Dict[str, Any]) -> None:
        """Send a message to the webview."""
        pass  # Implemented by PyIDE

    def add_script(self, script_path: str) -> None:
        """Add a script to the webview."""
        self.scripts.append(script_path)

    def add_style(self, style_path: str) -> None:
        """Add a stylesheet to the webview."""
        self.styles.append(style_path)


@dataclass
class InputBox:
    """
    A quick input box.

    Example:
        result = InputBox(
            prompt="Enter your name:",
            placeholder="John Doe"
        ).show()
    """

    prompt: str
    placeholder: str = ""
    value: str = ""
    password: bool = False
    validate: Optional[Callable[[str], Optional[str]]] = None

    def show(self) -> Optional[str]:
        """Show the input box and return the result."""
        pass  # Implemented by PyIDE


@dataclass
class QuickPick:
    """
    A quick pick selection list.

    Example:
        result = QuickPick(
            items=[
                QuickPickItem("opt1", "Option 1", "Description"),
                QuickPickItem("opt2", "Option 2", "Description"),
            ],
            placeholder="Select an option"
        ).show()
    """

    items: List["QuickPickItem"]
    placeholder: str = ""
    can_pick_many: bool = False
    match_on_description: bool = True
    match_on_detail: bool = True

    def show(self) -> Optional[Any]:
        """Show the quick pick and return the selected item(s)."""
        pass  # Implemented by PyIDE


@dataclass
class QuickPickItem:
    """An item in a quick pick list."""

    id: str
    label: str
    description: str = ""
    detail: str = ""
    icon: Optional[str] = None
    picked: bool = False
    data: Any = None


class UIBuilder:
    """
    Fluent builder for creating UI elements.

    Example:
        dialog = (UIBuilder()
            .dialog("settings", "Settings")
            .size(500, 400)
            .content("<form>...</form>")
            .button("Save", "submit", "primary")
            .button("Cancel", "close")
            .build())
    """

    def __init__(self):
        self._element = None
        self._type = None

    def dialog(self, id: str, title: str) -> "UIBuilder":
        """Start building a dialog."""
        self._element = Dialog(id=id, title=title)
        self._type = "dialog"
        return self

    def panel(self, id: str, title: str, location: str = "sidebar") -> "UIBuilder":
        """Start building a panel."""
        self._element = Panel(id=id, title=title, location=location)
        self._type = "panel"
        return self

    def size(self, width: int, height: int) -> "UIBuilder":
        """Set the size."""
        if hasattr(self._element, "width"):
            self._element.width = width
        if hasattr(self._element, "height"):
            self._element.height = height
        return self

    def content(self, html: str) -> "UIBuilder":
        """Set HTML content."""
        if hasattr(self._element, "html_content"):
            self._element.html_content = html
        elif hasattr(self._element, "html"):
            self._element.html = html
        return self

    def button(self, label: str, action: str = "close", style: str = "default") -> "UIBuilder":
        """Add a button (for dialogs)."""
        if isinstance(self._element, Dialog):
            self._element.add_button(label, action, style)
        return self

    def icon(self, icon: str) -> "UIBuilder":
        """Set the icon."""
        if hasattr(self._element, "icon"):
            self._element.icon = icon
        return self

    def on(self, event: str, callback: Callable) -> "UIBuilder":
        """Set an event handler."""
        attr_name = f"on_{event}"
        if hasattr(self._element, attr_name):
            setattr(self._element, attr_name, callback)
        return self

    def build(self) -> Any:
        """Build and return the UI element."""
        return self._element
