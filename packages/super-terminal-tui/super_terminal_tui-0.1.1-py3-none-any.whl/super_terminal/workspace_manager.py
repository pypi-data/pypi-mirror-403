import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WorkspaceHandler(FileSystemEventHandler):
    def __init__(self, workspace_path, callback, conflict_callback):
        self.workspace_path = workspace_path
        self.callback = callback
        self.conflict_callback = conflict_callback
        self.file_modifications = {}  # Track recent modifications: {filepath: (timestamp, agent_name)}

    def on_modified(self, event):
        if not event.is_directory:
            rel_path = os.path.relpath(event.src_path, self.workspace_path)
            self.callback(f"Modified: {rel_path}", event_type="modified", filepath=rel_path)

    def on_created(self, event):
        if not event.is_directory:
            rel_path = os.path.relpath(event.src_path, self.workspace_path)
            self.callback(f"Created: {rel_path}", event_type="created", filepath=rel_path)

    def on_deleted(self, event):
        if not event.is_directory:
            rel_path = os.path.relpath(event.src_path, self.workspace_path)
            self.callback(f"Deleted: {rel_path}", event_type="deleted", filepath=rel_path)

class WorkspaceManager:
    def __init__(self, path, callback, conflict_callback=None):
        self.path = os.path.abspath(path)
        self.callback = callback
        self.conflict_callback = conflict_callback
        self.observer = Observer()
        self.handler = WorkspaceHandler(self.path, callback, conflict_callback)
        self.file_access_tracker = {}  # Track: {filepath: [(timestamp, agent_name, event_type)]}

    def track_file_access(self, filepath, agent_name, event_type):
        """Track file modifications by agents and detect conflicts"""
        current_time = time.time()

        if filepath not in self.file_access_tracker:
            self.file_access_tracker[filepath] = []

        # Clean up old entries (older than 5 seconds)
        self.file_access_tracker[filepath] = [
            entry for entry in self.file_access_tracker[filepath]
            if current_time - entry[0] < 5
        ]

        # Check for conflicts: same file modified by different agents within 5 seconds
        recent_agents = {entry[1] for entry in self.file_access_tracker[filepath]}
        if recent_agents and agent_name not in recent_agents:
            # Conflict detected!
            if self.conflict_callback:
                conflicting_agents = list(recent_agents)
                self.conflict_callback(filepath, agent_name, conflicting_agents)

        # Add current access
        self.file_access_tracker[filepath].append((current_time, agent_name, event_type))

    def start(self):
        self.observer.schedule(self.handler, self.path, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
