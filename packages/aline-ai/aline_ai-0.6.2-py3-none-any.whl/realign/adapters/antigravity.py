"""
Antigravity IDE Adapter

Handles session discovery for Antigravity IDE (Gemini in IDE).
Since .pb conversation files are encrypted, this adapter uses
readable brain artifacts (walkthrough.md, task.md) as session indicators.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base import SessionAdapter
from ..triggers.antigravity_trigger import AntigravityTrigger


class AntigravityAdapter(SessionAdapter):
    """Adapter for Antigravity IDE sessions."""

    name = "antigravity"
    trigger_class = AntigravityTrigger

    def discover_sessions(self) -> List[Path]:
        """
        Find all active Antigravity IDE sessions.
        Returns the directory path for each conversation that contains relevant artifacts.
        """
        sessions = []
        gemini_brain = Path.home() / ".gemini" / "antigravity" / "brain"

        if not gemini_brain.exists():
            return sessions

        try:
            for conv_dir in gemini_brain.iterdir():
                if not conv_dir.is_dir():
                    continue

                # Check for key artifacts
                has_artifacts = any(
                    (conv_dir / filename).exists()
                    for filename in ["task.md", "walkthrough.md", "implementation_plan.md"]
                )

                if has_artifacts:
                    sessions.append(conv_dir)
        except Exception:
            pass

        return sessions

    def discover_sessions_for_project(self, project_path: Path) -> List[Path]:
        """
        Find sessions for a specific project.
        """
        all_sessions = self.discover_sessions()
        project_sessions = []

        for session in all_sessions:
            extracted_path = self.extract_project_path(session)
            if extracted_path and extracted_path == project_path:
                project_sessions.append(session)

        return project_sessions

    def extract_project_path(self, session_file: Path) -> Optional[Path]:
        """
        Infer project root from Antigravity brain artifacts.

        Antigravity stores readable artifacts (task.md / walkthrough.md / implementation_plan.md).
        We attempt to extract a `file://...` reference, then walk upward to find a `.git` root.
        """
        session_dir = session_file if session_file.is_dir() else session_file.parent
        candidates: List[Path] = []

        artifact_names = ["task.md", "walkthrough.md", "implementation_plan.md"]
        for name in artifact_names:
            p = session_dir / name
            if not p.exists():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Capture file:// paths from Markdown links or plain text.
            # Example: file:///Users/me/Project/src/main.py or file://.../src/main.py
            for match in re.findall(r"file://([^)\s]+)", text):
                raw = match.strip()
                if raw.startswith("/"):
                    candidates.append(Path(raw))
                else:
                    # Some tools emit file://Users/... (missing leading slash)
                    candidates.append(Path("/" + raw))

        for candidate in candidates:
            try:
                # Prefer the nearest VCS root
                path = candidate
                if path.is_file():
                    path = path.parent
                for parent in [path] + list(path.parents):
                    git_dir = parent / ".git"
                    if git_dir.exists():
                        return parent
            except Exception:
                continue

        # Fallback: if we found a candidate that exists, return its parent directory.
        for candidate in candidates:
            try:
                if candidate.exists():
                    return candidate.parent if candidate.is_file() else candidate
            except Exception:
                continue

        return None

    def get_session_metadata(self, session_file: Path) -> Dict[str, Any]:
        """Extract rich metadata from Antigravity brain artifacts."""
        metadata = super().get_session_metadata(session_file)

        if not session_file.exists():
            return metadata

        session_dir = session_file if session_file.is_dir() else session_file.parent

        try:
            # We just return the turn count (always 1 if exists)
            # No task progress parsing required
            metadata["turn_count"] = self.trigger.count_complete_turns(session_file)

        except Exception:
            pass

        return metadata

    def is_session_valid(self, session_file: Path) -> bool:
        """Check if this is an Antigravity artifact directory."""
        if not session_file.is_dir():
            if (
                session_file.parent.name == "brain"
                and session_file.parent.parent.name == "antigravity"
            ):
                # It's a directory inside brain
                return True
            return False

        # Check parent hierarchy
        # .../.gemini/antigravity/brain/<uuid>
        try:
            if (
                session_file.parent.name == "brain"
                and session_file.parent.parent.name == "antigravity"
            ):
                return True
        except Exception:
            pass
        return False
