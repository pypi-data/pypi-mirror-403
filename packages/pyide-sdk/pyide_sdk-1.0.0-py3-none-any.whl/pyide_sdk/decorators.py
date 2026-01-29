"""
Plugin Decorators for PyIDE

Decorators for registering commands, menu items, keybindings, and toolbar buttons.
"""

from typing import Callable, Optional, List
from functools import wraps


def command(
    name: str,
    description: str = "",
    category: str = "Plugin"
) -> Callable:
    """
    Register a method as a command.

    Commands can be executed via the command palette or programmatically.

    Args:
        name: Unique command identifier (e.g., "my_plugin.do_action")
        description: Human-readable description for command palette
        category: Category for grouping in command palette

    Example:
        @command("hello_world", description="Say hello")
        def say_hello(self):
            self.api.show_notification("Hello, World!")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._command_name = name
        wrapper._command_description = description
        wrapper._command_category = category
        return wrapper

    return decorator


def menu_item(
    menu: str,
    label: str,
    shortcut: Optional[str] = None,
    icon: Optional[str] = None,
    position: int = -1,
    separator_before: bool = False,
    separator_after: bool = False
) -> Callable:
    """
    Register a method as a menu item.

    Args:
        menu: Target menu path (e.g., "Tools", "Tools/My Plugin")
        label: Display label for the menu item
        shortcut: Optional keyboard shortcut (e.g., "Ctrl+Shift+M")
        icon: Optional icon name or path
        position: Position in menu (-1 for end)
        separator_before: Add separator before this item
        separator_after: Add separator after this item

    Example:
        @menu_item("Tools", "Run My Tool", shortcut="Ctrl+Alt+T")
        def run_tool(self):
            self.do_something()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._menu_item = {
            "menu": menu,
            "label": label,
            "shortcut": shortcut,
            "icon": icon,
            "position": position,
            "separator_before": separator_before,
            "separator_after": separator_after,
            "callback": func.__name__
        }
        return wrapper

    return decorator


def keybinding(
    keys: str,
    when: Optional[str] = None
) -> Callable:
    """
    Register a keyboard shortcut for a method.

    Args:
        keys: Key combination (e.g., "Ctrl+Shift+P", "Alt+F1")
        when: Optional context when binding is active (e.g., "editorFocus")

    Supported modifiers: Ctrl, Alt, Shift, Meta (Cmd on Mac)
    Supported keys: A-Z, 0-9, F1-F12, Enter, Escape, Tab, Space, etc.

    Example:
        @keybinding("Ctrl+Shift+H")
        def show_help(self):
            self.show_plugin_help()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._keybinding = keys
        wrapper._keybinding_when = when
        return wrapper

    return decorator


def toolbar_button(
    icon: str,
    tooltip: str,
    group: str = "plugins",
    position: int = -1
) -> Callable:
    """
    Register a method as a toolbar button.

    Args:
        icon: Icon name or SVG path
        tooltip: Hover tooltip text
        group: Toolbar group (default: "plugins")
        position: Position in group (-1 for end)

    Example:
        @toolbar_button(icon="play", tooltip="Run Plugin Action")
        def run_action(self):
            self.execute()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._toolbar_button = {
            "icon": icon,
            "tooltip": tooltip,
            "group": group,
            "position": position,
            "callback": func.__name__
        }
        return wrapper

    return decorator


def context_menu(
    target: str,
    label: str,
    icon: Optional[str] = None
) -> Callable:
    """
    Register a method as a context menu item.

    Args:
        target: Context target ("editor", "file_tree", "tab", "output")
        label: Display label
        icon: Optional icon

    Example:
        @context_menu("editor", "Format with My Formatter")
        def format_selection(self):
            self.format_code()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._context_menu = {
            "target": target,
            "label": label,
            "icon": icon,
            "callback": func.__name__
        }
        return wrapper

    return decorator


def status_bar(
    position: str = "right",
    priority: int = 100
) -> Callable:
    """
    Register a method to provide status bar content.

    The decorated method should return a string or dict with status info.

    Args:
        position: "left", "center", or "right"
        priority: Display priority (lower = more prominent)

    Example:
        @status_bar(position="right")
        def get_status(self):
            return f"Lines: {self.line_count}"
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._status_bar = {
            "position": position,
            "priority": priority,
            "callback": func.__name__
        }
        return wrapper

    return decorator


def on_interval(seconds: float) -> Callable:
    """
    Register a method to be called periodically.

    Args:
        seconds: Interval in seconds

    Example:
        @on_interval(30)
        def auto_save_check(self):
            self.check_unsaved_files()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._interval = seconds
        return wrapper

    return decorator


def debounce(wait: float) -> Callable:
    """
    Debounce a method to prevent rapid repeated calls.

    Args:
        wait: Minimum time between calls in seconds

    Example:
        @debounce(0.5)
        def on_text_change(self, text):
            self.analyze_text(text)
    """
    import time

    def decorator(func: Callable) -> Callable:
        last_called = [0.0]

        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_called[0] >= wait:
                last_called[0] = now
                return func(*args, **kwargs)

        return wrapper

    return decorator


def async_command(name: str, description: str = "") -> Callable:
    """
    Register an async method as a command.

    Like @command but for async functions.

    Example:
        @async_command("fetch_data", "Fetch remote data")
        async def fetch_data(self):
            data = await self.api.fetch("https://api.example.com/data")
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper._command_name = name
        wrapper._command_description = description
        wrapper._is_async = True
        return wrapper

    return decorator
