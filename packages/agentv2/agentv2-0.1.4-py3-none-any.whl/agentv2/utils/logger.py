import inspect
import json
import logging
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

# =============================================================================
# GLOBALS
# =============================================================================

console = Console()
_lock = Lock()


LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "success": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


LOG_STYLES = {
    "debug": ("dim", "🔍"),
    "info": ("cyan", "ℹ️"),
    "success": ("green", "✅"),
    "warning": ("yellow", "⚠️"),
    "error": ("red bold", "❌"),
}


LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(filename)s:%(lineno)d → %(message)s"


# =============================================================================
# FILE TRACKING MANAGER
# =============================================================================


class FileTrackingManager:
    """Manages per-module file loggers and transitions."""

    def __init__(
        self,
        app_name: str = "AgentV2",
        log_level: int = logging.DEBUG,
    ):
        self.app_name = app_name
        self.log_level = log_level
        self.loggers: Dict[str, logging.Logger] = {}
        self.previous_module: Optional[str] = None

        backend_dir = Path(__file__).resolve().parents[1]
        self.logs_dir = backend_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def _resolve_module(self) -> str:
        frame = inspect.currentframe()
        try:
            while frame:
                frame = frame.f_back
                if not frame:
                    break

                file = frame.f_globals.get("__file__")
                if not file or "logger" in file:
                    continue

                return Path(file).stem
            return "unknown"
        finally:
            del frame

    def _create_file_handler(self, module: str) -> logging.Handler:
        handler = RotatingFileHandler(
            self.logs_dir / f"{module.lower()}_log.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        return handler

    def get_logger(self) -> logging.Logger:
        module = self._resolve_module()

        with _lock:
            if module not in self.loggers:
                logger = logging.getLogger(f"{self.app_name}.{module}")
                logger.setLevel(self.log_level)
                logger.propagate = False

                file_handler = self._create_file_handler(module)
                logger.addHandler(file_handler)

                self.loggers[module] = logger

                if self.previous_module and self.previous_module != module:
                    self.loggers[self.previous_module].info(
                        f"→ Execution has been moved to {module}"
                    )
                    logger.info(f"← Execution started from {self.previous_module}")

            self.previous_module = module
            return self.loggers[module]

    def log_transition(self, from_module: str, to_module: str):
        with _lock:
            if from_module in self.loggers and to_module in self.loggers:
                self.loggers[from_module].info(
                    f"→ Execution has been moved to {to_module}"
                )
                self.loggers[to_module].info(f"← Execution started from {from_module}")


# =============================================================================
# RICH LOGGER (FRONTEND)
# =============================================================================


class RichLogger:
    """Rich console logger backed by file-tracking logging.Logger."""

    def __init__(
        self,
        manager: FileTrackingManager,
        context: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
    ):
        self.manager = manager
        self.context = context or {}
        self.verbose = verbose

    # ------------------------------------------------------------------
    # CONTEXT
    # ------------------------------------------------------------------

    def bind(self, **kwargs) -> "RichLogger":
        return RichLogger(self.manager, {**self.context, **kwargs}, verbose=self.verbose)

    # ------------------------------------------------------------------
    # CORE LOGGING
    # ------------------------------------------------------------------

    def _format_value(self, value: Any, for_text: bool = False) -> str | Text:
        """Format a value for display. If for_text=True, returns Text object."""
        if value is None:
            if for_text:
                return Text("None", style="dim italic")
            return "None"
        if isinstance(value, bool):
            if for_text:
                return Text(str(value), style="green" if value else "red")
            return str(value)
        if isinstance(value, (int, float)):
            if for_text:
                return Text(str(value), style="cyan bold")
            return str(value)
        if isinstance(value, (dict, list)):
            formatted = (
                json.dumps(value, indent=2)
                if len(json.dumps(value)) > 50
                else json.dumps(value)
            )
            if for_text:
                return Text(formatted, style="yellow")
            return formatted
        if for_text:
            return Text(str(value), style="white")
        return str(value)

    def log(
        self,
        event: str,
        level: str = "info",
        exc: Exception | None = None,
        **kwargs,
    ):
        logger = self.manager.get_logger()

        merged = {**self.context, **kwargs}
        msg = event.replace("_", " ")

        if exc:
            logger.log(LOG_LEVELS[level], msg, exc_info=exc)
        else:
            logger.log(LOG_LEVELS[level], msg)

        style, icon = LOG_STYLES[level]

        # Build content for the box
        content_lines = []

        # Event title
        content_lines.append(f"{icon} {event.upper().replace('_', ' ')}")
        content_lines.append("")  # Blank line

        # Add context/kwargs
        if merged:
            for k, v in merged.items():
                formatted_val = self._format_value(v, for_text=False)
                content_lines.append(f"  {k}: {formatted_val}")

        # Add exception traceback if present
        if exc:
            content_lines.append("")  # Blank line
            content_lines.append("  Exception Details:")
            tb_lines = traceback.format_exception(exc)
            for line in tb_lines:
                for tb_line in line.strip().split("\n"):
                    if tb_line.strip():
                        content_lines.append(f"    {tb_line}")

        content = "\n".join(content_lines)

        # Determine border style based on level
        border_styles = {
            "debug": "dim white",
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red bold",
        }
        border_style = border_styles.get(level, "cyan")

        # Only print to console if verbose is True
        if self.verbose:
            with _lock:
                console.print()  # Spacing before
                console.print(
                    Panel(
                        content,
                        title=f"[{border_style}]{event.upper().replace('_', ' ')}[/{border_style}]",
                        border_style=border_style,
                        box=box.ROUNDED,
                        padding=(1, 2),
                    )
                )
                console.print()  # Spacing after

    # ------------------------------------------------------------------
    # LEVEL HELPERS
    # ------------------------------------------------------------------

    def debug(self, event: str, **kwargs):
        self.log(event, "debug", **kwargs)

    def info(self, event: str, **kwargs):
        self.log(event, "info", **kwargs)

    def success(self, event: str, **kwargs):
        self.log(event, "success", **kwargs)

    def warning(self, event: str, **kwargs):
        self.log(event, "warning", **kwargs)

    def error(self, event: str, exc: Exception | None = None, **kwargs):
        self.log(event, "error", exc=exc, **kwargs)

    # ------------------------------------------------------------------
    # RICH UI HELPERS
    # ------------------------------------------------------------------

    def panel(self, content: str, title: str = "", style: str = "cyan"):
        if not self.verbose:
            return
        with _lock:
            console.print()
            console.print(
                Panel(
                    content,
                    title=title,
                    border_style=style,
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
            )
            console.print()

    def table(self, data: Dict[str, Any], title: str = ""):
        if not self.verbose:
            return
        table = Table(
            title=title, box=box.ROUNDED, show_header=True, header_style="bold magenta"
        )
        table.add_column("Key", style="cyan bold")
        table.add_column("Value", style="white")

        for k, v in data.items():
            formatted = self._format_value(v, for_text=True)
            if isinstance(formatted, Text):
                table.add_row(k, formatted)
            else:
                table.add_row(k, str(formatted))

        with _lock:
            console.print()
            console.print(table)
            console.print()

    def json(self, data: dict, title: str = ""):
        syntax = Syntax(
            json.dumps(data, indent=2), "json", theme="monokai", line_numbers=False
        )
        if not self.verbose:
            return
        with _lock:
            console.print()
            if title:
                console.print(
                    Panel(
                        syntax,
                        title=title,
                        border_style="blue",
                        box=box.ROUNDED,
                        padding=(1, 2),
                    )
                )
            else:
                console.print(syntax)
            console.print()

    def progress_spinner(self, description: str = "Processing..."):
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        )

    def divider(self, title: str = "", style: str = "dim"):
        """Print a horizontal divider line."""
        if not self.verbose:
            return
        with _lock:
            if title:
                console.rule(title, style=style)
            else:
                console.rule(style=style)
            console.print()

    def section(self, title: str, style: str = "bold cyan"):
        """Print a section header."""
        if not self.verbose:
            return
        with _lock:
            console.print()
            console.rule(f"[{style}]{title}[/{style}]", style=style)
            console.print()

    def header(self, title: str, style: str = "bold cyan"):
        """Print a main header (alias for section with default styling)."""
        self.section(title, style=style)

    def subheader(self, title: str, style: str = "dim cyan"):
        """Print a subsection header."""
        if not self.verbose:
            return
        with _lock:
            console.print()
            text = Text(title, style=style)
            console.print(text)
            console.print()

    def todo_list(self, todos: list, title: str = ""):
        """Display a list of todo items in a formatted table."""
        if not self.verbose:
            return
        if not todos:
            return

        table = Table(
            title=title, box=box.ROUNDED, show_header=True, header_style="bold magenta"
        )
        table.add_column("#", style="cyan bold", width=4)
        table.add_column("Todo Item", style="white")
        table.add_column("Status", style="yellow")

        for i, todo in enumerate(todos, 1):
            # Handle both TodoItem objects and strings
            if hasattr(todo, "todo"):
                todo_text = todo.todo
                if todo.is_completed:
                    status = Text("✓ COMPLETED", style="green bold")
                elif todo.is_in_progress:
                    status = Text("⏳ IN PROGRESS", style="yellow bold")
                else:
                    status = Text("PENDING", style="dim")
            else:
                todo_text = str(todo)
                status = Text("PENDING", style="dim")

            table.add_row(str(i), todo_text, status)

        with _lock:
            console.print()
            console.print(table)
            console.print()


# =============================================================================
# PUBLIC API
# =============================================================================

_manager = FileTrackingManager()
logger = RichLogger(_manager)


def get_logger(verbose: bool = True) -> RichLogger:
    """Get a logger instance with optional verbose control."""
    return RichLogger(_manager, verbose=verbose)


def log_transition(from_module: str, to_module: str):
    _manager.log_transition(from_module, to_module)
