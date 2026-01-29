from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, ListView, ListItem, Label, RichLog, Button
from rich.text import Text
from textual.events import Resize, Key
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.binding import Binding
from textual.screen import ModalScreen
from .agent_manager import AgentManager
from .workspace_manager import WorkspaceManager
import os
from datetime import datetime
import json
import subprocess
import shutil

class AddAgentScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Add New AI Agent", id="title")
            yield Label("Agent Name:")
            yield Input(placeholder="e.g. Claude", id="agent-name")
            yield Label("CLI Command:")
            yield Input(placeholder="e.g. claude", id="agent-command")
            with Horizontal(id="actions"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Add Agent", variant="success", id="add")

    def on_mount(self) -> None:
        self.query_one("#agent-name").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            name = self.query_one("#agent-name", Input).value
            command = self.query_one("#agent-command", Input).value
            if name and command:
                self.dismiss((name, command))
        else:
            self.dismiss(None)

class WorkspaceScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Select Project Directory", id="title")
            yield Label("Current: " + os.getcwd())
            yield Label("Enter new path:")
            yield Input(value=os.getcwd(), id="ws-path", placeholder="Enter directory path")
            yield Label("(Press Enter or click Select)", id="hint")
            yield Label("", id="ws-error")
            with Horizontal(id="actions"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Select", variant="success", id="select")

    def on_mount(self) -> None:
        self.query_one("#ws-path").focus()

    def validate_and_select_path(self, path: str) -> None:
        """Validate path and either select it, create it, or show error"""
        input_widget = self.query_one("#ws-path", Input)
        error_label = self.query_one("#ws-error", Label)

        if not path:
            input_widget.styles.border = ("heavy", "red")
            error_label.update("[bold red]Error: Path cannot be empty[/bold red]")
            return

        # Expand user home directory
        path = os.path.expanduser(path)

        # Check if path exists
        if os.path.isdir(path):
            self.dismiss(path)
            return

        # Check if path exists but is a file
        if os.path.exists(path):
            input_widget.styles.border = ("heavy", "red")
            error_label.update("[bold red]Error: Path exists but is a file, not a directory[/bold red]")
            return

        # Check if parent directory exists
        parent_dir = os.path.dirname(path)
        if not parent_dir:
            parent_dir = "."

        if not os.path.exists(parent_dir):
            input_widget.styles.border = ("heavy", "red")
            error_label.update(f"[bold red]Error: Parent directory does not exist: {parent_dir}[/bold red]")
            return

        # Try to create the directory
        try:
            os.makedirs(path, exist_ok=True)
            error_label.update(f"[bold green]✓ Created directory: {path}[/bold green]")
            # Dismiss immediately after creating
            self.dismiss(path)
        except PermissionError:
            input_widget.styles.border = ("heavy", "red")
            error_label.update("[bold red]Error: Permission denied - cannot create directory[/bold red]")
        except Exception as e:
            input_widget.styles.border = ("heavy", "red")
            error_label.update(f"[bold red]Error: {str(e)}[/bold red]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the input field"""
        if event.input.id == "ws-path":
            self.validate_and_select_path(event.input.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select":
            path = self.query_one("#ws-path", Input).value
            self.validate_and_select_path(path)
        else:
            self.dismiss(None)

class SyncChangesScreen(ModalScreen):
    def __init__(self, agent_name, changed_files):
        super().__init__()
        self.agent_name = agent_name
        self.changed_files = changed_files

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Sync Changes from {self.agent_name}", id="title")
            yield Label(f"Found {len(self.changed_files)} changed file(s):")

            # Show list of changed files
            files_list = RichLog(id="files-list", highlight=False, markup=True)
            with Vertical():
                yield files_list

            yield Label("Sync these changes to main workspace?")
            with Horizontal(id="actions"):
                yield Button("Cancel", variant="error", id="cancel")
                yield Button("Sync", variant="success", id="sync")

    def on_mount(self) -> None:
        files_list = self.query_one("#files-list", RichLog)
        for file_path in self.changed_files:
            files_list.write(f"  • {file_path}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sync":
            self.dismiss(True)
        else:
            self.dismiss(False)

class AgentItem(ListItem):
    def __init__(self, agent_name: str):
        super().__init__()
        self.agent_name = agent_name
        self.current_status = "Running"
        self.current_task = "Idle"
        self.label = Label(f"● {agent_name}")
        self.task_label = Label(f"  {self.current_task}", classes="task-label")
    
    def compose(self) -> ComposeResult:
        yield self.label
        yield self.task_label
    
    def update_status(self, task: str = "", attention: bool = False):
        if task:
            self.current_task = task
            self.task_label.update(f"  {task[:25]}")
        
        if attention:
            self.label.styles.color = "red"
            self.label.styles.text_style = "bold italic"
        else:
            self.label.styles.color = "green"
            self.label.styles.text_style = None

class SuperTerminal(App):
    CSS = """
    Screen {
        background: #1a1a1a;
    }

    #sidebar {
        width: 25%;
        border-right: tall $primary;
        background: #242424;
    }

    #main-content {
        width: 75%;
    }

    #terminal-view {
        height: 70%;
        border-bottom: tall $primary;
        background: black;
        color: white;
        padding: 0 1;
    }

    .terminal-area:focus {
        border: tall $accent;
    }

    #monitor-log {
        height: 30%;
        background: #1e1e1e;
        padding: 1;
        color: #cccccc;
    }

    .status-bar {
        background: $accent;
        color: white;
        padding: 0 1;
        text-style: bold;
    }

    #ws-label {
        padding: 1;
        color: $secondary;
        text-style: italic;
    }

    AddAgentScreen, WorkspaceScreen, SyncChangesScreen {
        align: center middle;
    }

    #files-list {
        height: 10;
        border: solid $primary;
        background: $surface;
        margin: 1 0;
    }

    #dialog {
        padding: 1 2;
        width: 70;
        height: auto;
        border: thick $primary 80%;
        background: $surface;
    }

    #dialog Input {
        margin: 1 0;
        width: 100%;
    }

    #dialog Label {
        margin-top: 1;
    }

    #hint {
        text-style: italic;
        opacity: 0.7;
        margin-top: 0;
    }

    #ws-error {
        min-height: 2;
        margin: 1 0;
    }

    #title {
        height: 3;
        width: 100%;
        content-align: center middle;
        text-style: bold;
        background: $primary;
        color: white;
        margin: 0;
    }

    #actions {
        height: 3;
        margin-top: 1;
        content-align: center middle;
    }

    #actions Button {
        margin: 0 1;
    }

    #terminal-input {
        margin: 1 0;
    }

    .task-label {
        opacity: 0.5;
        text-style: italic;
    }
    """

    BINDINGS = [
        Binding("f1", "add_agent", "Add Agent"),
        Binding("f2", "change_workspace", "Workspace"),
        Binding("f3", "close_agent", "Close Agent"),
        Binding("f4", "quit", "Quit"),
        Binding("f5", "prev_agent", "← Prev"),
        Binding("f6", "next_agent", "Next →"),
        Binding("f7", "sync_agent_changes", "Sync Changes"),
        Binding("pageup", "scroll_up", "Scroll Up", show=False),
        Binding("pagedown", "scroll_down", "Scroll Down", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.agent_manager = AgentManager()
        self.workspace_manager = None
        self.current_workspace = os.getcwd()
        self.active_agent_name = None
        self.attention_agents = set()
        self.agent_history_buffers = {}  # Store screen text for each agent
        self.agent_log_files = {}  # Store log file handles for each agent
        self.agent_workspaces = {}  # Store isolated workspace directory for each agent
        self.logs_dir = None
        self.setup_logging()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label(" AGENTS ", classes="status-bar")
                yield ListView(id="agent-list")
                yield Label(" WORKSPACE ", classes="status-bar")
                self.workspace_label = Label(os.path.basename(self.current_workspace), id="ws-label")
                yield self.workspace_label
            
            with Vertical(id="main-content"):
                yield Label(" TERMINAL (Interactive Mode) ", classes="status-bar", id="terminal-header")
                yield RichLog(id="terminal-view", classes="terminal-area", highlight=False, markup=False, auto_scroll=True, wrap=False)
                yield Label(" FILE MONITOR ", classes="status-bar")
                yield RichLog(id="monitor-log", highlight=True, markup=False, auto_scroll=True)
        yield Footer()

    def create_agent_workspace(self, agent_name):
        """Create an isolated workspace copy for the agent"""
        try:
            # Create agents directory in workspace
            agents_dir = os.path.join(self.current_workspace, ".super-terminal-agents")
            os.makedirs(agents_dir, exist_ok=True)

            # Create agent-specific workspace
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            agent_workspace_name = f"{agent_name.lower().replace(' ', '-')}_{timestamp}"
            agent_workspace_path = os.path.join(agents_dir, agent_workspace_name)

            # Copy the workspace (excluding .super-terminal-agents and logs)
            def ignore_patterns(dir, files):
                ignore = []
                if '.super-terminal-agents' in files:
                    ignore.append('.super-terminal-agents')
                if 'super-terminal-logs' in files:
                    ignore.append('super-terminal-logs')
                if '.git' in files:
                    ignore.append('.git')
                if '__pycache__' in files:
                    ignore.append('__pycache__')
                if 'node_modules' in files:
                    ignore.append('node_modules')
                if 'venv' in files:
                    ignore.append('venv')
                if '.venv' in files:
                    ignore.append('.venv')
                return ignore

            shutil.copytree(
                self.current_workspace,
                agent_workspace_path,
                ignore=ignore_patterns,
                symlinks=False
            )

            return agent_workspace_path
        except Exception as e:
            try:
                self.query_one("#monitor-log", RichLog).write(
                    f"[bold red]Failed to create workspace: {str(e)}[/bold red]"
                )
            except:
                pass
            return None

    def cleanup_agent_workspace(self, agent_name):
        """Remove agent's isolated workspace"""
        if agent_name not in self.agent_workspaces:
            return

        try:
            workspace_path = self.agent_workspaces[agent_name]
            if os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
            del self.agent_workspaces[agent_name]
        except Exception as e:
            pass

    def find_changed_files(self, agent_name):
        """Find files that changed in agent's workspace"""
        if agent_name not in self.agent_workspaces:
            return []

        agent_workspace = self.agent_workspaces[agent_name]
        changed_files = []

        try:
            # Walk through agent workspace
            for root, dirs, files in os.walk(agent_workspace):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', '.venv']]

                for file in files:
                    agent_file = os.path.join(root, file)
                    relative_path = os.path.relpath(agent_file, agent_workspace)
                    main_file = os.path.join(self.current_workspace, relative_path)

                    # Check if file is new or modified
                    if not os.path.exists(main_file):
                        changed_files.append(relative_path)
                    else:
                        # Compare modification times and sizes
                        agent_stat = os.stat(agent_file)
                        main_stat = os.stat(main_file)

                        if agent_stat.st_mtime > main_stat.st_mtime or agent_stat.st_size != main_stat.st_size:
                            changed_files.append(relative_path)

            return changed_files
        except Exception as e:
            return []

    def sync_agent_changes(self, agent_name):
        """Sync changed files from agent workspace to main workspace"""
        if agent_name not in self.agent_workspaces:
            return False

        agent_workspace = self.agent_workspaces[agent_name]
        changed_files = self.find_changed_files(agent_name)

        try:
            for relative_path in changed_files:
                agent_file = os.path.join(agent_workspace, relative_path)
                main_file = os.path.join(self.current_workspace, relative_path)

                # Create parent directory if needed
                os.makedirs(os.path.dirname(main_file), exist_ok=True)

                # Copy file
                shutil.copy2(agent_file, main_file)

                # Log the sync
                try:
                    self.query_one("#monitor-log", RichLog).write(
                        f"[bold green]✓ Synced: {relative_path}[/bold green]"
                    )
                except:
                    pass

            return True
        except Exception as e:
            try:
                self.query_one("#monitor-log", RichLog).write(
                    f"[bold red]✗ Sync failed: {str(e)}[/bold red]"
                )
            except:
                pass
            return False

    def setup_logging(self):
        """Setup logging directory in the workspace"""
        self.logs_dir = os.path.join(self.current_workspace, "super-terminal-logs")
        try:
            os.makedirs(self.logs_dir, exist_ok=True)
            # Create a session log
            session_file = os.path.join(self.logs_dir, "session.json")
            session_data = {
                "session_start": datetime.now().isoformat(),
                "workspace": self.current_workspace,
                "agents": []
            }
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            # If we can't create logs, continue without logging
            self.logs_dir = None

    def create_agent_log(self, agent_name):
        """Create a log file for a new agent"""
        if not self.logs_dir:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{agent_name}_{timestamp}.log"
        log_path = os.path.join(self.logs_dir, log_filename)

        try:
            log_file = open(log_path, "w", encoding="utf-8")
            log_file.write(f"=== Agent: {agent_name} ===\n")
            log_file.write(f"=== Started: {datetime.now().isoformat()} ===\n")
            log_file.write(f"=== Workspace: {self.current_workspace} ===\n\n")
            log_file.flush()
            return log_file
        except Exception:
            return None

    def log_agent_output(self, agent_name, data):
        """Log agent output to file"""
        if agent_name in self.agent_log_files and self.agent_log_files[agent_name]:
            try:
                self.agent_log_files[agent_name].write(data)
                self.agent_log_files[agent_name].flush()
            except Exception:
                pass

    def log_agent_input(self, agent_name, input_text):
        """Log user input to agent"""
        if agent_name in self.agent_log_files and self.agent_log_files[agent_name]:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.agent_log_files[agent_name].write(f"\n[USER INPUT {timestamp}]: {repr(input_text)}\n")
                self.agent_log_files[agent_name].flush()
            except Exception:
                pass

    def close_agent_log(self, agent_name):
        """Close the log file for an agent"""
        if agent_name in self.agent_log_files and self.agent_log_files[agent_name]:
            try:
                self.agent_log_files[agent_name].write(f"\n\n=== Ended: {datetime.now().isoformat()} ===\n")
                self.agent_log_files[agent_name].close()
            except Exception:
                pass
            del self.agent_log_files[agent_name]

    def on_mount(self):
        self.setup_workspace(self.current_workspace)
        self.set_timer(0.05, self.check_agent_outputs)
        self.query_one("#terminal-view").focus()

    def add_agent_callback(self, result):
        if result:
            name, command = result
            view = self.query_one("#terminal-view", RichLog)
            cols = (view.size.width or 82) - 2 # Adjust for padding
            rows = view.size.height or 24

            # Create isolated workspace for this agent
            agent_workspace = self.create_agent_workspace(name)
            if agent_workspace:
                self.agent_workspaces[name] = agent_workspace
                try:
                    self.query_one("#monitor-log", RichLog).write(
                        f"[bold green]✓ Created isolated workspace: {os.path.basename(agent_workspace)}[/bold green]"
                    )
                except:
                    pass
            else:
                # Fall back to main workspace if copy fails
                agent_workspace = self.current_workspace

            # Add agent with its isolated workspace
            self.agent_manager.add_agent(name, command, agent_workspace)
            agent = self.agent_manager.get_agent(name)
            if agent:
                agent.start(cols=cols, rows=rows)

            self.agent_history_buffers[name] = ""

            # Create log file for this agent
            log_file = self.create_agent_log(name)
            if log_file:
                self.agent_log_files[name] = log_file
                log_file.write(f"Command: {command}\n")
                if name in self.agent_workspaces:
                    log_file.write(f"Isolated Workspace: {self.agent_workspaces[name]}\n")
                log_file.write("\n")
                log_file.flush()

            item = AgentItem(name)
            self.query_one("#agent-list", ListView).append(item)
            if not self.active_agent_name:
                self.set_active_agent(name)

    def set_active_agent(self, name):
        if self.active_agent_name == name:
            return

        self.active_agent_name = name

        # Update header to show workspace info
        workspace_info = ""
        if name in self.agent_workspaces:
            workspace_info = f" (isolated)"
        self.query_one("#terminal-header", Label).update(f" TERMINAL - {name}{workspace_info} ")

        # Get current screen state from the agent
        terminal_view = self.query_one("#terminal-view", RichLog)
        terminal_view.clear()

        agent = self.agent_manager.get_agent(name)
        if agent:
            # Get the current terminal screen from the agent
            screen_text = agent.get_screen_text()
            if screen_text:
                terminal_view.write(screen_text)
                # Update the buffer with current state
                self.agent_history_buffers[name] = screen_text

        # Reset attention
        if name in self.attention_agents:
            self.attention_agents.remove(name)
            for item in self.query("#agent-list ListItem"):
                if isinstance(item, AgentItem) and item.agent_name == name:
                    item.update_status(attention=False)

        self.call_after_refresh(lambda: self.query_one("#terminal-view").focus())

    def check_agent_outputs(self):
        for name, agent in self.agent_manager.agents.items():
            has_output = False
            last_line = ""

            while not agent.output_queue.empty():
                data = agent.output_queue.get()
                has_output = True

                # Log the output
                self.log_agent_output(name, data)

                if "\n" in data:
                    parts = data.split("\n")
                    if len(parts) > 1:
                        last_line = parts[-2]

                if any(kw in data.lower() for kw in ["confirm", "error", "failed", "y/n", "?", "trust"]):
                    if name != self.active_agent_name:
                        self.attention_agents.add(name)
                        for item in self.query("#agent-list ListItem"):
                            if isinstance(item, AgentItem) and item.agent_name == name:
                                item.update_status(attention=True)

            if has_output:
                # Get the rendered screen from pyte
                screen_text = agent.get_screen_text()

                # Store in history buffer
                self.agent_history_buffers[name] = screen_text

                # Update UI if active
                if name == self.active_agent_name:
                    terminal_view = self.query_one("#terminal-view", RichLog)
                    terminal_view.clear()
                    terminal_view.write(screen_text)

            if last_line:
                for item in self.query("#agent-list ListItem"):
                    if isinstance(item, AgentItem) and item.agent_name == name:
                        item.update_status(task=last_line.strip())

        self.set_timer(0.05, self.check_agent_outputs)

    def on_resize(self, event: Resize):
        try:
            view = self.query_one("#terminal-view", RichLog)
            cols = view.size.width - 2
            rows = view.size.height
            if cols > 0 and rows > 0:
                for agent in self.agent_manager.agents.values():
                    agent.resize(cols, rows)
        except:
            pass

    def action_close_agent(self):
        if self.active_agent_name:
            name_to_close = self.active_agent_name

            # Cleanup isolated workspace
            self.cleanup_agent_workspace(name_to_close)

            # Close the log file for this agent
            self.close_agent_log(name_to_close)

            self.agent_manager.remove_agent(name_to_close)
            if name_to_close in self.agent_history_buffers:
                del self.agent_history_buffers[name_to_close]

            list_view = self.query_one("#agent-list", ListView)
            items = list_view.query(AgentItem)
            for item in items:
                if item.agent_name == name_to_close:
                    item.remove()
                    break

            self.active_agent_name = None
            self.query_one("#terminal-view", RichLog).clear()
            self.query_one("#terminal-header", Label).update(" TERMINAL ")

            remaining = list_view.query(AgentItem)
            if remaining:
                self.set_active_agent(remaining[0].agent_name)

        self.query_one("#terminal-view").focus()

    def action_add_agent(self):
        self.push_screen(AddAgentScreen(), self.add_agent_callback)

    def action_sync_agent_changes(self):
        """Sync changes from active agent to main workspace"""
        if not self.active_agent_name:
            return

        if self.active_agent_name not in self.agent_workspaces:
            try:
                self.query_one("#monitor-log", RichLog).write(
                    "[yellow]No isolated workspace for this agent[/yellow]"
                )
            except:
                pass
            return

        # Find changed files
        changed_files = self.find_changed_files(self.active_agent_name)

        if not changed_files:
            try:
                self.query_one("#monitor-log", RichLog).write(
                    "[yellow]No changes found to sync[/yellow]"
                )
            except:
                pass
            return

        # Show sync dialog
        self.push_screen(
            SyncChangesScreen(self.active_agent_name, changed_files),
            self.sync_callback
        )

    def sync_callback(self, should_sync):
        """Handle sync confirmation"""
        if should_sync and self.active_agent_name:
            success = self.sync_agent_changes(self.active_agent_name)
            if success:
                try:
                    changed_count = len(self.find_changed_files(self.active_agent_name))
                    # Recalculate to get count before sync
                    self.query_one("#monitor-log", RichLog).write(
                        f"[bold green]✓ Synced all changes from {self.active_agent_name}[/bold green]"
                    )
                except:
                    pass

    def action_change_workspace(self):
        self.push_screen(WorkspaceScreen(), self.setup_workspace)

    def action_next_agent(self):
        """Switch to next agent in the list"""
        agents = list(self.agent_manager.agents.keys())
        if not agents or not self.active_agent_name:
            return
        try:
            current_idx = agents.index(self.active_agent_name)
            next_idx = (current_idx + 1) % len(agents)
            self.set_active_agent(agents[next_idx])
            self.query_one("#agent-list", ListView).index = next_idx
        except: pass

    def action_prev_agent(self):
        """Switch to previous agent in the list"""
        agents = list(self.agent_manager.agents.keys())
        if not agents or not self.active_agent_name:
            return
        try:
            current_idx = agents.index(self.active_agent_name)
            prev_idx = (current_idx - 1) % len(agents)
            self.set_active_agent(agents[prev_idx])
            self.query_one("#agent-list", ListView).index = prev_idx
        except: pass

    def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, AgentItem):
            self.set_active_agent(item.agent_name)

    def action_scroll_up(self):
        """Scroll terminal view up"""
        try:
            self.query_one("#terminal-view", RichLog).scroll_page_up()
        except:
            pass

    def action_scroll_down(self):
        """Scroll terminal view down"""
        try:
            self.query_one("#terminal-view", RichLog).scroll_page_down()
        except:
            pass

    def on_key(self, event: Key) -> None:
        # Don't intercept function keys (f1-f12) or special keys used for app bindings
        function_keys = ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"]
        if event.key in function_keys or event.key in ["pageup", "pagedown"]:
            return

        # Don't intercept keys if we have a modal screen open (dialog)
        # Check screen_stack length > 1 means modal is open
        if len(self._screen_stack) > 1:
            return

        # Only intercept if we have an active agent
        if not self.active_agent_name:
            return

        agent = self.agent_manager.get_agent(self.active_agent_name)
        if not agent:
            return

        # Map keys to terminal sequences
        key_map = {
            "enter": "\r",
            "backspace": "\x7f",
            "tab": "\t",
            "escape": "\x1b",
            "up": "\x1b[A",
            "down": "\x1b[B",
            "right": "\x1b[C",
            "left": "\x1b[D",
        }

        char = key_map.get(event.key, event.character)
        if char:
            agent.send_input(char)
            # Log user input
            self.log_agent_input(self.active_agent_name, char)
            event.prevent_default()
            event.stop()

    def setup_workspace(self, path):
        if not path or not os.path.isdir(path):
            return
        if self.workspace_manager:
            self.workspace_manager.stop()
        self.current_workspace = os.path.abspath(path)

        # Reinitialize logging for new workspace
        self.setup_logging()

        self.workspace_label.update(os.path.basename(path))
        self.workspace_manager = WorkspaceManager(
            path,
            lambda *a, **kw: self.call_from_thread(self.log_file_change, *a, **kw),
            lambda *a, **kw: self.call_from_thread(self.log_file_conflict, *a, **kw)
        )
        self.workspace_manager.start()
        try:
            self.query_one("#monitor-log", RichLog).write(f"--- Monitoring: {path} ---")
        except: pass

    def log_file_change(self, message, event_type="", filepath=""):
        try:
            self.query_one("#monitor-log", RichLog).write(f"[File] {message}")
            if self.active_agent_name and filepath and self.workspace_manager:
                self.workspace_manager.track_file_access(filepath, self.active_agent_name, event_type)
        except: pass

    def log_file_conflict(self, filepath, current_agent, conflicting_agents):
        conflict_msg = (
            f"[bold red]⚠ CONFLICT DETECTED[/bold red]\n"
            f"File: {filepath}\n"
            f"Current agent: {current_agent}\n"
            f"Conflicting with: {', '.join(conflicting_agents)}\n"
        )
        try:
            self.query_one("#monitor-log", RichLog).write(conflict_msg)
            for name in conflicting_agents + [current_agent]:
                if name != self.active_agent_name and name in self.agent_manager.agents:
                    self.attention_agents.add(name)
                    for item in self.query("#agent-list ListItem"):
                        if isinstance(item, AgentItem) and item.agent_name == name:
                            item.update_status(attention=True)
        except: pass

    async def action_quit(self):
        # Close all agent log files
        for agent_name in list(self.agent_log_files.keys()):
            self.close_agent_log(agent_name)

        self.agent_manager.stop_all()
        if self.workspace_manager:
            self.workspace_manager.stop()
        await super().action_quit()

if __name__ == "__main__":
    app = SuperTerminal()
    app.run()
