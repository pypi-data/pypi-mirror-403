"""Main editor class that orchestrates the edit workflow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.live import Live
from rich.spinner import Spinner

from src.ai.base import EditRequest
from src.core.diff import generate_diff
from src.core.file_handler import (
    create_backup,
    read_file,
    restore_backup,
    write_file,
)
from src.ui.diff_view import render_diff
from src.ui.display import display_error, display_file, display_info, display_status
from src.ui.prompt import get_action, get_edit_prompt
from src.utils.syntax import get_language_name

if TYPE_CHECKING:
    from pathlib import Path

    from rich.console import Console

    from src.ai.base import AIProvider
    from src.core.diff import DiffResult
    from src.core.file_handler import FileInfo
    from src.utils.config import Config

logger = logging.getLogger(__name__)


class Editor:
    """Main editor that manages the file editing loop."""

    def __init__(
        self,
        console: Console,
        provider: AIProvider,
        config: Config,
    ) -> None:
        self._console = console
        self._provider = provider
        self._config = config
        self._file_info: FileInfo | None = None
        self._backup_path: Path | None = None
        self._current_content: str = ""
        self._history: list[str] = []

    def open_file(self, filepath: Path) -> None:
        """Load a file and display it."""
        self._file_info = read_file(filepath, self._config.max_file_size_mb)
        self._current_content = self._file_info.content
        self._history = []
        self._backup_path = None

        display_file(
            self._console,
            self._current_content,
            self._file_info.path,
            self._config.theme,
        )

    def run_interactive(self, initial_prompt: str = "") -> None:
        """Run the interactive edit loop.

        Loops: prompt -> AI edit -> diff -> accept/reject/edit/quit.
        """
        if self._file_info is None:
            display_error(self._console, "No file loaded.")
            return

        prompt = initial_prompt

        while True:
            if not prompt:
                prompt = get_edit_prompt(self._console)
                if not prompt:
                    continue

            edited = self._request_edit(prompt)
            if edited is None:
                prompt = ""
                continue

            diff = generate_diff(
                self._current_content,
                edited,
                self._file_info.path,
                self._config.context_lines,
            )

            if not diff.has_changes:
                display_info(self._console, "No changes were generated.")
                prompt = ""
                continue

            render_diff(self._console, diff)

            action = get_action(
                self._console,
                undo_available=bool(self._history),
            )

            if action == "accept":
                self._accept(diff)
                prompt = ""
            elif action == "reject":
                display_info(self._console, "Changes rejected.")
                prompt = ""
            elif action == "edit":
                prompt = ""
            elif action == "undo":
                self._undo()
                prompt = ""
            elif action == "quit":
                display_info(self._console, "Goodbye.")
                break

    def run_noninteractive(self, prompt: str) -> bool:
        """Run a single edit without interaction. Returns True if changes were applied."""
        if self._file_info is None:
            display_error(self._console, "No file loaded.")
            return False

        edited = self._request_edit(prompt)
        if edited is None:
            return False

        diff = generate_diff(
            self._current_content,
            edited,
            self._file_info.path,
            self._config.context_lines,
        )

        if not diff.has_changes:
            display_info(self._console, "No changes were generated.")
            return False

        render_diff(self._console, diff)
        self._accept(diff)
        return True

    def _request_edit(self, prompt: str) -> str | None:
        """Send an edit request to the AI and return the edited content."""
        if self._file_info is None:
            return None

        language = get_language_name(self._file_info.path)
        request = EditRequest(
            file_path=self._file_info.path,
            file_content=self._current_content,
            prompt=prompt,
            language=language,
        )

        try:
            if self._config.streaming:
                return self._stream_edit(request)
            response = self._provider.edit(request)
            return response.edited_content
        except RuntimeError as exc:
            display_error(self._console, str(exc))
            return None

    def _stream_edit(self, request: EditRequest) -> str:
        """Stream the AI response with a spinner."""
        chunks: list[str] = []

        with Live(
            Spinner("dots", text="[bold cyan] Generating edits...[/bold cyan]"),
            console=self._console,
            transient=True,
        ):
            for chunk in self._provider.edit_stream(request):
                chunks.append(chunk)

        return "".join(chunks)

    def _accept(self, diff: DiffResult) -> None:
        """Accept changes: save to file with backup."""
        if self._file_info is None:
            return

        self._history.append(self._current_content)

        if self._config.backup_enabled and self._backup_path is None:
            self._backup_path = create_backup(self._file_info)

        self._current_content = diff.modified
        write_file(self._file_info, self._current_content)
        display_status(self._console, "Changes saved.")

    def _undo(self) -> None:
        """Undo the last accepted change."""
        if not self._history:
            display_info(self._console, "Nothing to undo.")
            return

        if self._file_info is None:
            return

        previous = self._history.pop()

        if self._backup_path is not None:
            restore_backup(self._file_info.path, self._backup_path)
            self._backup_path = None

        self._current_content = previous
        write_file(self._file_info, self._current_content)
        display_status(self._console, "Undone. File restored to previous state.")
        display_file(
            self._console,
            self._current_content,
            self._file_info.path,
            self._config.theme,
        )
