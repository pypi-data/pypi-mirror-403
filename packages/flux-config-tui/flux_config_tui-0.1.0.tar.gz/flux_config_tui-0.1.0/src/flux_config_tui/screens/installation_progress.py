"""Installation progress screen for FluxNode setup."""

from __future__ import annotations

import logging

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Label, ProgressBar, Static

logger = logging.getLogger(__name__)


class TaskItem(Static):
    """Individual task item in the installation progress list."""

    DEFAULT_CSS = """
    TaskItem {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }

    TaskItem.pending {
        color: $text-muted;
    }

    TaskItem.in_progress {
        color: $accent;
        text-style: bold;
    }

    TaskItem.completed {
        color: $success;
    }

    TaskItem.failed {
        color: $error;
    }
    """

    def __init__(self, task_name: str, description: str, status: str = "pending") -> None:
        """Initialize task item.

        Args:
            task_name: Task identifier
            description: Human-readable description
            status: Task status (pending, in_progress, completed, failed)
        """
        super().__init__()
        self.task_name = task_name
        self.description = description
        self.status = status

    def render(self) -> str:
        """Render the task item."""
        if self.status == "pending":
            icon = "⏸"
        elif self.status == "in_progress":
            icon = "⏳"
        elif self.status == "completed":
            icon = "✓"
        elif self.status == "failed":
            icon = "✗"
        else:
            icon = "?"

        return f"{icon} {self.description}"

    def update_status(self, status: str) -> None:
        """Update task status.

        Args:
            status: New status
        """
        # Remove old status class
        if self.has_class(self.status):
            self.remove_class(self.status)

        self.status = status
        self.add_class(status)
        self.refresh()


class InstallationProgressScreen(Screen):
    """Screen showing installation progress with task list and progress bar."""

    DEFAULT_CSS = """
    InstallationProgressScreen {
        align: center middle;
    }

    InstallationProgressScreen Container {
        width: 80;
        height: auto;
        background: $panel;
        border: solid $primary;
        padding: 2;
    }

    #progress-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #current-task {
        text-align: center;
        color: $text;
        margin-bottom: 1;
        height: auto;
    }

    #progress-bar {
        margin-bottom: 2;
    }

    #download-info {
        text-align: center;
        color: $text-muted;
        height: auto;
        margin-bottom: 1;
    }

    #task-list-container {
        height: auto;
        max-height: 20;
        border: solid $primary-darken-2;
        padding: 1;
    }

    #task-list {
        height: auto;
    }
    """

    # Reactive vars
    current_task = var("")
    progress_percent = var(0)
    download_info = var("")

    def __init__(self) -> None:
        """Initialize installation progress screen."""
        super().__init__()
        self.tasks: dict[str, TaskItem] = {}

    def compose(self) -> ComposeResult:
        """Compose the installation progress screen."""
        with Container():
            yield Label("Installing FluxNode...", id="progress-title")
            yield Label("", id="current-task")
            yield ProgressBar(total=100, id="progress-bar", show_eta=False)
            yield Label("", id="download-info")
            with VerticalScroll(id="task-list-container"):
                yield Container(id="task-list")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Initialize progress bar
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(total=100, progress=0)

    def watch_current_task(self, value: str) -> None:
        """Watch current_task reactive var.

        Args:
            value: New current task value
        """
        try:
            label = self.query_one("#current-task", Label)
            label.update(value)
        except NoMatches as e:
            logger.warning("Failed to update current task: %s", e)

    def watch_progress_percent(self, value: int) -> None:
        """Watch progress_percent reactive var.

        Args:
            value: New progress percentage
        """
        try:
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.update(progress=value)
        except NoMatches as e:
            logger.warning("Failed to update progress bar: %s", e)

    def watch_download_info(self, value: str) -> None:
        """Watch download_info reactive var.

        Args:
            value: New download info
        """
        try:
            label = self.query_one("#download-info", Label)
            label.update(value)
        except NoMatches as e:
            logger.warning("Failed to update download info: %s", e)

    def add_task(self, task_name: str, description: str, status: str = "pending") -> None:
        """Add a task to the list.

        Args:
            task_name: Task identifier
            description: Human-readable description
            status: Initial status
        """
        if task_name in self.tasks:
            # Task already exists, update it
            self.update_task_status(task_name, status)
            return

        task_item = TaskItem(task_name, description, status)
        task_item.add_class(status)
        self.tasks[task_name] = task_item

        # Add to container
        container = self.query_one("#task-list", Container)
        container.mount(task_item)

    def update_task_status(self, task_name: str, status: str) -> None:
        """Update status of a specific task.

        Args:
            task_name: Task identifier
            status: New status (pending, in_progress, completed, failed)
        """
        if task_name in self.tasks:
            self.tasks[task_name].update_status(status)

    def set_current_task(self, task: str, description: str) -> None:
        """Set the current task being executed.

        Args:
            task: Task identifier
            description: Task description
        """
        self.current_task = f"⏳ {description}"

        # Add task to list if not already present
        if task not in self.tasks:
            self.add_task(task, description, "in_progress")
        else:
            self.update_task_status(task, "in_progress")

    def set_progress(self, percent: int) -> None:
        """Set installation progress percentage.

        Args:
            percent: Progress percentage (0-100)
        """
        self.progress_percent = min(100, max(0, percent))

    def mark_task_complete(self, task: str, success: bool) -> None:
        """Mark a task as completed or failed.

        Args:
            task: Task identifier
            success: Whether task completed successfully
        """
        status = "completed" if success else "failed"
        if task in self.tasks:
            self.update_task_status(task, status)

    def set_download_info(self, filename: str, percent: float, speed_mbps: float) -> None:
        """Set download progress information.

        Args:
            filename: Name of file being downloaded
            percent: Download percentage
            speed_mbps: Download speed in Mbit/s
        """
        self.download_info = f"Downloading {filename}: {percent:.1f}% @ {speed_mbps:.1f} Mbit/s"

    def mark_download_complete(self, filename: str, success: bool) -> None:
        """Mark a download as completed.

        Args:
            filename: Name of downloaded file
            success: Whether download succeeded
        """
        if success:
            self.download_info = f"✓ Downloaded {filename}"
        else:
            self.download_info = f"✗ Failed to download {filename}"
