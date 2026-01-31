"""Adapter for OpenAI Codex CLI."""

from __future__ import annotations

from typing import ClassVar

from .base import AIAdapter


class CodexAdapter(AIAdapter):
    """Adapter for OpenAI Codex CLI responses."""

    name: ClassVar[str] = "codex"
    BASE_INDENT: ClassVar[int] = 2

    def _next_non_empty_starts_with_prompt(self, lines: list[str], start: int) -> bool:
        """Check if the next non-empty line starts with prompt indicator."""
        for line in lines[start:]:
            stripped = line.strip()
            if stripped:
                return stripped.startswith("›")
        return False

    def extract_last_response(self, text: str) -> str:
        """Extract the last response block starting with bullet."""
        lines = text.split("\n")

        response_start_indices = [
            i for i, line in enumerate(lines) if line.strip().startswith("•")
        ]

        if not response_start_indices:
            return ""

        last_start = response_start_indices[-1]
        response_lines: list[str] = []

        for i in range(last_start, len(lines)):
            line = lines[i]
            stripped = line.strip()

            if i == last_start:
                response_lines.append(stripped[1:].strip())
                continue

            if stripped.startswith("›"):
                break

            if not stripped:
                if self._next_non_empty_starts_with_prompt(lines, i + 1):
                    break
                continue

            if line.startswith(" " * self.BASE_INDENT):
                response_lines.append(self.strip_indent(line))
            else:
                break

        return self.finalize_response(response_lines)
