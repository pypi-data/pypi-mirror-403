"""
Base Plugin Class for PyIDE

This module provides the base class that all PyIDE plugins must inherit from.
"""

from abc import ABC
from typing import Optional, Dict, Any, List, Callable
import logging


class PluginMeta(type):
    """Metaclass for automatic plugin registration and hook collection."""

    _plugins: Dict[str, type] = {}

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)

        if name != "Plugin" and any(isinstance(b, PluginMeta) for b in bases):
            plugin_name = namespace.get("name", name)
            mcs._plugins[plugin_name] = cls

            # Collect hooks from methods
            hooks = {}
            commands = {}
            menu_items = []
            keybindings = {}

            for attr_name, attr_value in namespace.items():
                if callable(attr_value):
                    if hasattr(attr_value, "_hook_type"):
                        hook_type = attr_value._hook_type
                        if hook_type not in hooks:
                            hooks[hook_type] = []
                        hooks[hook_type].append(attr_name)

                    if hasattr(attr_value, "_command_name"):
                        commands[attr_value._command_name] = attr_name

                    if hasattr(attr_value, "_menu_item"):
                        menu_items.append(attr_value._menu_item)

                    if hasattr(attr_value, "_keybinding"):
                        keybindings[attr_value._keybinding] = attr_name

            cls._hooks = hooks
            cls._commands = commands
            cls._menu_items = menu_items
            cls._keybindings = keybindings

        return cls

    @classmethod
    def get_plugins(mcs) -> Dict[str, type]:
        """Get all registered plugins."""
        return mcs._plugins.copy()


class Plugin(metaclass=PluginMeta):
    """
    Base class for PyIDE plugins.

    All plugins must inherit from this class and define at minimum
    a `name` and `version` attribute.

    Attributes:
        name (str): The display name of the plugin
        version (str): Semantic version string (e.g., "1.0.0")
        description (str): Brief description of the plugin
        author (str): Plugin author name
        homepage (str): URL to plugin homepage or repository
        requires (List[str]): List of required PyIDE versions or other plugins

    Example:
        class MyPlugin(Plugin):
            name = "My Awesome Plugin"
            version = "1.0.0"
            description = "Does awesome things"
            author = "Your Name"

            def on_activate(self):
                self.log.info("Plugin activated!")

            @hook("on_file_save")
            def handle_save(self, filepath):
                self.api.show_notification(f"Saved: {filepath}")
    """

    # Required attributes (override in subclass)
    name: str = "Unnamed Plugin"
    version: str = "0.0.0"

    # Optional attributes
    description: str = ""
    author: str = ""
    homepage: str = ""
    requires: List[str] = []
    icon: Optional[str] = None

    # Internal attributes
    _hooks: Dict[str, List[str]] = {}
    _commands: Dict[str, str] = {}
    _menu_items: List[Dict] = []
    _keybindings: Dict[str, str] = {}

    def __init__(self, api: "PyIDEAPI" = None):
        """
        Initialize the plugin.

        Args:
            api: The PyIDE API instance for interacting with the IDE
        """
        self.api = api
        self.enabled = False
        self.config: Dict[str, Any] = {}
        self.log = logging.getLogger(f"pyide.plugin.{self.name}")

        # Plugin-specific data storage
        self._data: Dict[str, Any] = {}

    def on_activate(self) -> None:
        """
        Called when the plugin is activated.
        Override this method to perform initialization tasks.
        """
        pass

    def on_deactivate(self) -> None:
        """
        Called when the plugin is deactivated.
        Override this method to perform cleanup tasks.
        """
        pass

    def on_config_change(self, key: str, value: Any) -> None:
        """
        Called when a plugin configuration value changes.

        Args:
            key: The configuration key that changed
            value: The new value
        """
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key
            default: Default value if key doesn't exist

        Returns:
            The configuration value or default
        """
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: The configuration key
            value: The value to set
        """
        old_value = self.config.get(key)
        self.config[key] = value
        if old_value != value:
            self.on_config_change(key, value)

    def store_data(self, key: str, value: Any) -> None:
        """Store plugin-specific data."""
        self._data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Retrieve plugin-specific data."""
        return self._data.get(key, default)

    def register_command(self, name: str, callback: Callable, description: str = "") -> None:
        """
        Register a new command dynamically.

        Args:
            name: Command name (e.g., "my_plugin.do_something")
            callback: Function to call when command is executed
            description: Human-readable description
        """
        if self.api:
            self.api.register_command(name, callback, description)

    def register_keybinding(self, keys: str, command: str) -> None:
        """
        Register a keyboard shortcut.

        Args:
            keys: Key combination (e.g., "Ctrl+Shift+P")
            command: Command name to execute
        """
        if self.api:
            self.api.register_keybinding(keys, command)

    def __repr__(self) -> str:
        return f"<Plugin: {self.name} v{self.version}>"
