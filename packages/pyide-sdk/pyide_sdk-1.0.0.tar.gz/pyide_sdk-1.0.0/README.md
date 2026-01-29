# PyIDE SDK

The official Plugin SDK for PyIDE. Create powerful extensions and plugins to enhance your PyIDE experience.

## Installation

```bash
pip install pyide-sdk
```

For development:

```bash
pip install pyide-sdk[dev]
```

## Quick Start

Create your first plugin in just a few lines:

```python
from pyide_sdk import Plugin, command, hook

class HelloPlugin(Plugin):
    """A simple hello world plugin."""

    name = "hello-world"
    version = "1.0.0"
    description = "My first PyIDE plugin"

    def on_activate(self):
        self.api.show_notification("Hello Plugin activated!")

    @command("hello.say_hello", description="Say Hello")
    def say_hello(self):
        self.api.show_notification("Hello from my plugin!")

    @hook("on_file_save")
    def on_save(self, filepath):
        self.api.write_output(f"File saved: {filepath}")
```

## Features

- **Decorators** - Register commands, menu items, keybindings, and toolbar buttons
- **Event Hooks** - Respond to file, editor, code execution, and application events
- **UI Components** - Create panels, dialogs, status bar items, and more
- **Full API Access** - Interact with the editor, file system, terminal, and git

## Plugin Structure

A typical plugin structure:

```
my-plugin/
├── plugin.json          # Plugin manifest
├── __init__.py          # Plugin entry point
├── main.py              # Main plugin class
└── resources/           # Icons, templates, etc.
```

### plugin.json

```json
{
    "name": "my-plugin",
    "version": "1.0.0",
    "description": "My awesome plugin",
    "main": "main.py",
    "author": "Your Name",
    "license": "MIT",
    "activationEvents": ["on_app_ready"],
    "dependencies": []
}
```

## Decorators

### @command

Register a method as a command accessible from the command palette:

```python
@command("my_plugin.run_action", description="Run My Action", category="My Plugin")
def run_action(self):
    # Your code here
    pass
```

### @menu_item

Add items to the menu bar:

```python
@menu_item("Tools", "My Tool", shortcut="Ctrl+Shift+M")
def open_tool(self):
    pass

@menu_item("Tools/My Plugin", "Sub Action", icon="star")
def sub_action(self):
    pass
```

### @keybinding

Register keyboard shortcuts:

```python
@keybinding("Ctrl+Alt+H", when="editorFocus")
def show_help(self):
    self.show_plugin_help()
```

### @toolbar_button

Add buttons to the toolbar:

```python
@toolbar_button(icon="play", tooltip="Run Plugin")
def run_plugin(self):
    self.execute()
```

### @context_menu

Add items to context menus:

```python
@context_menu("editor", "Format Selection")
def format_selection(self):
    pass
```

## Event Hooks

Respond to IDE events using the `@hook` decorator:

```python
from pyide_sdk import hook, HookType

class MyPlugin(Plugin):

    @hook("on_file_save")
    def handle_save(self, filepath):
        print(f"File saved: {filepath}")

    @hook(HookType.ON_EDITOR_CHANGE)
    def handle_change(self, content):
        # React to editor changes
        pass

    @hook("on_code_run_start")
    def before_run(self, code):
        self.api.write_output("Starting execution...")
```

### Available Hooks

| Hook Type | Description |
|-----------|-------------|
| `on_file_new` | New file created |
| `on_file_open` | File opened |
| `on_file_save` | File saved |
| `on_file_close` | File closed |
| `on_editor_change` | Editor content changed |
| `on_editor_cursor_move` | Cursor position changed |
| `on_code_run_start` | Code execution started |
| `on_code_run_end` | Code execution finished |
| `on_code_run_error` | Code execution error |
| `on_git_commit` | Git commit made |
| `on_app_ready` | Application fully loaded |
| `on_settings_change` | Settings modified |

See `HookType` enum for the complete list.

## API Reference

The `self.api` object provides access to PyIDE functionality:

### Editor Operations

```python
# Get/set content
content = self.api.get_editor_content()
self.api.set_editor_content("new content")

# Cursor and selection
pos = self.api.get_cursor_position()  # {"line": 1, "column": 5}
self.api.set_cursor_position(10, 1)
selection = self.api.get_selection()

# Insert and replace
self.api.insert_text("hello", {"line": 5, "column": 10})
self.api.replace_selection("replacement text")
```

### File Operations

```python
# File info
filepath = self.api.get_current_file_path()
workspace = self.api.get_workspace_path()

# File actions
self.api.open_file("/path/to/file.py")
self.api.save_file()
self.api.create_file("/path/to/new.py", "# New file")
content = self.api.read_file("/path/to/file.py")
```

### UI Operations

```python
# Notifications
self.api.show_notification("Hello!", type="success", duration=3000)

# Dialogs
result = self.api.show_message_box(
    "Confirm",
    "Are you sure?",
    buttons=["Yes", "No"],
    type="question"
)

# Input
name = self.api.show_input_dialog("Enter Name", "What's your name?")

# Quick pick
choice = self.api.show_quick_pick(
    ["Option 1", "Option 2", "Option 3"],
    placeholder="Select an option"
)

# File dialogs
filepath = self.api.show_file_dialog(
    type="open",
    filters=[{"name": "Python", "extensions": ["py"]}]
)
```

### Output & Terminal

```python
self.api.write_output("Hello from plugin")
self.api.clear_output()

result = self.api.run_command("python --version")
# {"stdout": "Python 3.11.0", "stderr": "", "exit_code": 0}
```

### Code Execution

```python
result = self.api.run_python("print('Hello')")
# {"output": "Hello\n", "error": "", "exit_code": 0}

self.api.stop_execution()
```

### Git Operations

```python
status = self.api.git_status()
# {"branch": "main", "files": [...], "is_repo": True}

self.api.git_commit("Fix bug")
self.api.git_push()
self.api.git_pull()
```

### Diagnostics

```python
self.api.add_diagnostic(
    filepath="/path/to/file.py",
    line=10,
    column=5,
    message="Undefined variable 'x'",
    severity="error",
    source="my-linter"
)

self.api.clear_diagnostics(filepath="/path/to/file.py")
```

## UI Components

### Panel

Create sidebar or bottom panels:

```python
from pyide_sdk.ui import Panel

panel = Panel(
    id="my_plugin.panel",
    title="My Panel",
    location="sidebar",  # "sidebar", "bottom", "floating"
    icon="puzzle"
)
panel.set_content("<h1>Hello Panel</h1>")
panel.show()
```

### Dialog

Create modal dialogs:

```python
from pyide_sdk.ui import Dialog

dialog = Dialog(
    id="my_plugin.settings",
    title="Settings",
    width=500,
    height=400
)
dialog.set_content("<form>...</form>")
dialog.add_button("Save", "submit", "primary")
dialog.add_button("Cancel", "close")
dialog.show()
```

### Status Bar

Add status bar items:

```python
from pyide_sdk.ui import StatusBarItem

status = StatusBarItem(
    id="my_plugin.status",
    title="Status",
    text="Ready",
    position="right",
    tooltip="Click for details"
)
status.show()

# Update later
status.set_text("Processing...")
```

### Tree View

Create tree views for sidebar:

```python
from pyide_sdk.ui import TreeView, TreeItem

tree = TreeView(id="my_plugin.tree", title="My Tree")
tree.set_items([
    TreeItem("root", "Root", children=[
        TreeItem("child1", "Child 1"),
        TreeItem("child2", "Child 2"),
    ])
])
```

### UIBuilder

Fluent API for building UI:

```python
from pyide_sdk.ui import UIBuilder

dialog = (UIBuilder()
    .dialog("settings", "Settings")
    .size(500, 400)
    .content("<form>...</form>")
    .button("Save", "submit", "primary")
    .button("Cancel", "close")
    .build())
```

## Configuration

Plugins can define and access configuration:

```python
class MyPlugin(Plugin):
    name = "my-plugin"

    default_config = {
        "enabled": True,
        "auto_format": False,
        "max_items": 100
    }

    def on_activate(self):
        # Get config value
        enabled = self.get_config("enabled", True)

        # Set config value
        self.set_config("max_items", 200)
```

## Testing Plugins

Use `MockPyIDEAPI` for testing:

```python
from pyide_sdk.api import MockPyIDEAPI

def test_my_plugin():
    api = MockPyIDEAPI()
    api.set_editor_content("test content")

    plugin = MyPlugin(api)
    plugin.on_activate()

    assert api.get_editor_content() == "test content"
```

## Type Definitions

The SDK provides type definitions for IDE events:

```python
from pyide_sdk.types import (
    FileEvent,
    EditorEvent,
    DiagnosticItem,
    CompletionItem,
    Position,
    Range,
    TextEdit
)
```

## Examples

See the `examples/` directory for complete plugin examples:

- `hello_world/` - Basic plugin structure
- `file_watcher/` - File system monitoring
- `code_formatter/` - Code formatting plugin
- `git_helper/` - Git integration utilities

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## Support

- GitHub Issues: https://github.com/AeonLtd/pyide-sdk/issues
- Documentation: https://github.com/AeonLtd/pyide-sdk
