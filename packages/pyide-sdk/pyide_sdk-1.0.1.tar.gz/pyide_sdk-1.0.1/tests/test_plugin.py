"""Tests for the Plugin base class."""

import pytest
from pyide_sdk import Plugin, command, hook
from pyide_sdk.api import MockPyIDEAPI


class TestPlugin(Plugin):
    """A test plugin for unit testing."""

    name = "test-plugin"
    version = "1.0.0"
    description = "Test plugin"

    def on_activate(self):
        self.activated = True

    def on_deactivate(self):
        self.activated = False

    @command("test.action", description="Test action")
    def test_action(self):
        return "action executed"

    @hook("on_file_save")
    def on_save(self, filepath):
        return f"saved: {filepath}"


class TestPluginBase:
    """Test cases for Plugin base class."""

    def test_plugin_creation(self):
        """Test that a plugin can be instantiated."""
        api = MockPyIDEAPI()
        plugin = TestPlugin(api)
        assert plugin.name == "test-plugin"
        assert plugin.version == "1.0.0"

    def test_plugin_activation(self):
        """Test plugin activation lifecycle."""
        api = MockPyIDEAPI()
        plugin = TestPlugin(api)
        plugin.on_activate()
        assert plugin.activated is True

    def test_plugin_deactivation(self):
        """Test plugin deactivation lifecycle."""
        api = MockPyIDEAPI()
        plugin = TestPlugin(api)
        plugin.on_activate()
        plugin.on_deactivate()
        assert plugin.activated is False

    def test_command_decorator(self):
        """Test that command decorator marks methods correctly."""
        api = MockPyIDEAPI()
        plugin = TestPlugin(api)
        assert hasattr(plugin.test_action, "_command_name")
        assert plugin.test_action._command_name == "test.action"

    def test_hook_decorator(self):
        """Test that hook decorator marks methods correctly."""
        api = MockPyIDEAPI()
        plugin = TestPlugin(api)
        assert hasattr(plugin.on_save, "_hook_type")
        assert plugin.on_save._hook_type == "on_file_save"

    def test_config_operations(self):
        """Test plugin configuration get/set."""
        api = MockPyIDEAPI()
        plugin = TestPlugin(api)

        # Test default value
        value = plugin.get_config("missing_key", "default")
        assert value == "default"

        # Test set and get
        plugin.set_config("test_key", "test_value")
        assert plugin.get_config("test_key") == "test_value"


class TestMockAPI:
    """Test cases for MockPyIDEAPI."""

    def test_editor_content(self):
        """Test editor content operations."""
        api = MockPyIDEAPI()
        api.set_editor_content("hello world")
        assert api.get_editor_content() == "hello world"

    def test_cursor_position(self):
        """Test cursor position operations."""
        api = MockPyIDEAPI()
        api.set_cursor_position(10, 5)
        pos = api.get_cursor_position()
        assert pos["line"] == 10
        assert pos["column"] == 5

    def test_line_operations(self):
        """Test line-based operations."""
        api = MockPyIDEAPI()
        api.set_editor_content("line1\nline2\nline3")
        assert api.get_line(1) == "line1"
        assert api.get_line(2) == "line2"
        assert api.get_line_count() == 3

    def test_settings(self):
        """Test settings operations."""
        api = MockPyIDEAPI()
        api.set_setting("test.setting", True)
        assert api.get_setting("test.setting") is True
        assert api.get_setting("missing", "default") == "default"

    def test_command_registration(self):
        """Test command registration and execution."""
        api = MockPyIDEAPI()

        def my_command():
            return "executed"

        api.register_command("test.cmd", my_command)
        result = api.execute_command("test.cmd")
        assert result == "executed"
