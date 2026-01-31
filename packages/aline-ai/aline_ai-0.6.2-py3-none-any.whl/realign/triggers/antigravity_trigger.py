"""
AntigravityTrigger - Trigger for Antigravity IDE (Markdown artifacts)

Since Antigravity produces walkthrough.md and task.md instead of turn-based JSONL,
this trigger uses file content/structure as a signal for "turns".
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import re
from .base import TurnTrigger, TurnInfo


class AntigravityTrigger(TurnTrigger):
    """
    Trigger for Antigravity IDE markdown artifacts.
    Each distinct Task in task.md or major change in walkthrough.md can be
    treated as a 'turn'.
    """

    def get_supported_formats(self) -> List[str]:
        return ["antigravity_markdown"]

    def detect_session_format(self, session_file: Path) -> Optional[str]:
        """Detect if this is an Antigravity brain artifact directory."""
        try:
            # Check if directory
            if session_file.is_dir():
                if session_file.parent.name == "brain" and "antigravity" in str(session_file):
                    return "antigravity_markdown"
                return None

            # Legacy/Fallback: Check if file
            if session_file.suffix == ".md":
                path_str = str(session_file)
                if "gemini" in path_str and "brain" in path_str:
                    return "antigravity_markdown"
                if ".antigravity" in path_str or "antigravity" in path_str.lower():
                    return "antigravity_markdown"
            return None
        except Exception:
            return None

    def count_complete_turns(self, session_file: Path) -> int:
        """
        Antigravity sessions are effectively "single-turn" persistent states.
        We return 1 if the artifacts exist, 0 otherwise.

        The watcher will handle change detection via content hashing or mtime,
        even if this count stays at 1.

        Args:
            session_file: Path to brain directory (or file)

        Returns:
            int: 1 if artifacts exist, 0 otherwise.
        """
        if not session_file.exists():
            return 0

        session_dir = session_file if session_file.is_dir() else session_file.parent
        artifacts = ["task.md", "walkthrough.md", "implementation_plan.md"]

        has_artifacts = False
        for filename in artifacts:
            path = session_dir / filename
            if path.exists():
                has_artifacts = True
                break

        return 1 if has_artifacts else 0

    def extract_turn_info(self, session_file: Path, turn_number: int) -> Optional[TurnInfo]:
        """Extract information by aggregating artifacts."""
        if not session_file.exists():
            return None

        # Ensure we point to the directory
        session_dir = session_file if session_file.is_dir() else session_file.parent

        content_parts = []
        artifacts = ["task.md", "walkthrough.md", "implementation_plan.md"]

        # Aggregate content
        for filename in artifacts:
            path = session_dir / filename
            if path.exists():
                text = path.read_text(encoding="utf-8")
                content_parts.append(f"--- {filename} ---\n{text}")

        full_content = "\n\n".join(content_parts)
        if not full_content:
            return None

        # Always use current time for timestamp as this is an evolving state
        timestamp = datetime.now().isoformat()

        return TurnInfo(
            turn_number=1,  # Always Turn 1
            user_message="",  # Empty - full content used elsewhere for summary generation
            start_line=1,
            end_line=len(full_content.splitlines()) if full_content else 0,
            timestamp=timestamp,
        )

    def is_turn_complete(self, session_file: Path, turn_number: int) -> bool:
        # For Antigravity, if we have artifacts, it's "complete" in the sense that it exists.
        return self.count_complete_turns(session_file) >= 1

    def get_detailed_analysis(self, session_file: Path) -> Dict[str, Any]:
        """
        Get detailed analysis of the session.
        Since we treat the state as a single accumulated turn, we return one turn group.
        """
        current_turn = self.count_complete_turns(session_file)

        groups = []
        # Return a single entry representing the current state
        if current_turn > 0:
            info = self.extract_turn_info(session_file, 1)
            if info:
                groups.append(
                    {
                        "turn_number": 1,
                        "user_message": info.user_message,
                        "summary_message": "Antigravity Session State",
                        "turn_status": "completed",
                        "start_line": info.start_line,
                        "end_line": info.end_line,
                        "timestamp": info.timestamp,
                    }
                )

        return {
            "groups": groups,
            "total_turns": 1 if current_turn > 0 else 0,  # Conceptually one continuous session
            "latest_turn_id": 1 if current_turn > 0 else 0,
            "format": "antigravity_markdown",
        }
