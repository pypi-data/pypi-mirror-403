"""
PyIDE SDK - Plugin Development Kit for PyIDE

A comprehensive SDK for building plugins and extensions for PyIDE,
the lightweight Python IDE.

Usage:
    from pyide_sdk import Plugin, hook, command, menu_item

    class MyPlugin(Plugin):
        name = "My Plugin"
        version = "1.0.0"

        @hook("on_file_open")
        def handle_file_open(self, filepath):
            print(f"File opened: {filepath}")

        @command("hello")
        def say_hello(self):
            self.api.show_notification("Hello from my plugin!")
"""

__version__ = "1.0.0"
__author__ = "PyIDE Team"
__license__ = "MIT"

from .plugin import Plugin, PluginMeta
from .hooks import hook, HookManager, HookType
from .decorators import command, menu_item, keybinding, toolbar_button
from .api import PyIDEAPI
from .ui import UIExtension, Panel, Dialog, StatusBarItem
from .types import FileEvent, EditorEvent, MenuAction, PluginConfig

__all__ = [
    # Core
    "Plugin",
    "PluginMeta",
    "PyIDEAPI",

    # Hooks
    "hook",
    "HookManager",
    "HookType",

    # Decorators
    "command",
    "menu_item",
    "keybinding",
    "toolbar_button",

    # UI
    "UIExtension",
    "Panel",
    "Dialog",
    "StatusBarItem",

    # Types
    "FileEvent",
    "EditorEvent",
    "MenuAction",
    "PluginConfig",
]
