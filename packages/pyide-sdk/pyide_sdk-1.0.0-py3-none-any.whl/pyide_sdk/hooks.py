"""
Event Hooks System for PyIDE Plugins

This module provides the hook decorator and hook management system
that allows plugins to respond to IDE events.
"""

from enum import Enum
from typing import Callable, Dict, List, Any, Optional
from functools import wraps
import asyncio


class HookType(Enum):
    """Available hook types in PyIDE."""

    # File Events
    ON_FILE_NEW = "on_file_new"
    ON_FILE_OPEN = "on_file_open"
    ON_FILE_SAVE = "on_file_save"
    ON_FILE_SAVE_AS = "on_file_save_as"
    ON_FILE_CLOSE = "on_file_close"
    ON_FILE_RENAME = "on_file_rename"
    ON_FILE_DELETE = "on_file_delete"

    # Editor Events
    ON_EDITOR_CHANGE = "on_editor_change"
    ON_EDITOR_CURSOR_MOVE = "on_editor_cursor_move"
    ON_EDITOR_SELECTION_CHANGE = "on_editor_selection_change"
    ON_EDITOR_SCROLL = "on_editor_scroll"
    ON_EDITOR_FOCUS = "on_editor_focus"
    ON_EDITOR_BLUR = "on_editor_blur"

    # Tab Events
    ON_TAB_OPEN = "on_tab_open"
    ON_TAB_CLOSE = "on_tab_close"
    ON_TAB_SWITCH = "on_tab_switch"

    # Code Events
    ON_CODE_RUN_START = "on_code_run_start"
    ON_CODE_RUN_END = "on_code_run_end"
    ON_CODE_RUN_ERROR = "on_code_run_error"
    ON_CODE_OUTPUT = "on_code_output"

    # Debug Events
    ON_DEBUG_START = "on_debug_start"
    ON_DEBUG_STOP = "on_debug_stop"
    ON_DEBUG_BREAKPOINT_HIT = "on_debug_breakpoint_hit"
    ON_DEBUG_STEP = "on_debug_step"

    # Git Events
    ON_GIT_COMMIT = "on_git_commit"
    ON_GIT_PUSH = "on_git_push"
    ON_GIT_PULL = "on_git_pull"
    ON_GIT_BRANCH_CHANGE = "on_git_branch_change"

    # Project Events
    ON_PROJECT_OPEN = "on_project_open"
    ON_PROJECT_CLOSE = "on_project_close"
    ON_FOLDER_OPEN = "on_folder_open"

    # Application Events
    ON_APP_START = "on_app_start"
    ON_APP_READY = "on_app_ready"
    ON_APP_CLOSE = "on_app_close"
    ON_SETTINGS_CHANGE = "on_settings_change"
    ON_THEME_CHANGE = "on_theme_change"

    # Completion Events
    ON_COMPLETION_REQUEST = "on_completion_request"
    ON_COMPLETION_ACCEPT = "on_completion_accept"

    # Linting Events
    ON_LINT_START = "on_lint_start"
    ON_LINT_COMPLETE = "on_lint_complete"


def hook(hook_type: str) -> Callable:
    """
    Decorator to register a method as a hook handler.

    Args:
        hook_type: The type of hook to listen for (use HookType enum values)

    Returns:
        Decorated function

    Example:
        @hook("on_file_save")
        def handle_save(self, filepath):
            print(f"File saved: {filepath}")

        @hook(HookType.ON_CODE_RUN_START)
        def handle_run(self, code):
            print("Code execution started")
    """
    if isinstance(hook_type, HookType):
        hook_name = hook_type.value
    else:
        hook_name = hook_type

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._hook_type = hook_name
        return wrapper

    return decorator


class HookManager:
    """
    Manages hook registration and execution.

    This class is used internally by PyIDE to manage plugin hooks.
    Plugin developers typically don't need to use this directly.
    """

    def __init__(self):
        self._hooks: Dict[str, List[Dict[str, Any]]] = {}
        self._async_hooks: Dict[str, List[Dict[str, Any]]] = {}

    def register(
        self,
        hook_type: str,
        callback: Callable,
        plugin_name: str,
        priority: int = 100
    ) -> None:
        """
        Register a hook callback.

        Args:
            hook_type: The hook type name
            callback: The callback function
            plugin_name: Name of the plugin registering the hook
            priority: Execution priority (lower = earlier, default 100)
        """
        if hook_type not in self._hooks:
            self._hooks[hook_type] = []

        self._hooks[hook_type].append({
            "callback": callback,
            "plugin": plugin_name,
            "priority": priority
        })

        # Sort by priority
        self._hooks[hook_type].sort(key=lambda x: x["priority"])

    def unregister(self, hook_type: str, plugin_name: str) -> None:
        """
        Unregister all hooks for a plugin.

        Args:
            hook_type: The hook type name
            plugin_name: Name of the plugin to unregister
        """
        if hook_type in self._hooks:
            self._hooks[hook_type] = [
                h for h in self._hooks[hook_type]
                if h["plugin"] != plugin_name
            ]

    def unregister_all(self, plugin_name: str) -> None:
        """
        Unregister all hooks for a plugin across all hook types.

        Args:
            plugin_name: Name of the plugin to unregister
        """
        for hook_type in self._hooks:
            self.unregister(hook_type, plugin_name)

    def emit(self, hook_type: str, *args, **kwargs) -> List[Any]:
        """
        Emit a hook event to all registered callbacks.

        Args:
            hook_type: The hook type name
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            List of return values from all callbacks
        """
        results = []

        if hook_type in self._hooks:
            for hook_info in self._hooks[hook_type]:
                try:
                    result = hook_info["callback"](*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    # Log error but continue with other hooks
                    print(f"Hook error in {hook_info['plugin']}: {e}")

        return results

    async def emit_async(self, hook_type: str, *args, **kwargs) -> List[Any]:
        """
        Emit a hook event asynchronously.

        Args:
            hook_type: The hook type name
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            List of return values from all callbacks
        """
        results = []

        if hook_type in self._hooks:
            tasks = []
            for hook_info in self._hooks[hook_type]:
                callback = hook_info["callback"]
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(*args, **kwargs))
                else:
                    # Wrap sync function
                    tasks.append(asyncio.to_thread(callback, *args, **kwargs))

            results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    def get_hooks(self, hook_type: str) -> List[Dict[str, Any]]:
        """Get all registered hooks for a type."""
        return self._hooks.get(hook_type, []).copy()

    def get_all_hooks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all registered hooks."""
        return self._hooks.copy()


# Global hook manager instance
_hook_manager = HookManager()


def get_hook_manager() -> HookManager:
    """Get the global hook manager instance."""
    return _hook_manager
