"""Codex home/session path helpers.

To guarantee terminal↔session binding even when multiple Codex instances run in the same cwd,
we can isolate Codex storage per dashboard terminal via the `CODEX_HOME` environment variable.

We choose deterministic paths under `~/.aline/` so the watcher (a separate process) can
derive the owning terminal_id purely from the session file path.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


ENV_CODEX_HOME = "CODEX_HOME"


def aline_codex_homes_dir() -> Path:
    override = os.environ.get("ALINE_CODEX_HOMES_DIR", "").strip()
    if override:
        return Path(os.path.expanduser(override))
    return Path.home() / ".aline" / "codex_homes"


def codex_home_for_terminal(terminal_id: str) -> Path:
    tid = (terminal_id or "").strip()
    return aline_codex_homes_dir() / tid


def codex_sessions_dir_for_home(codex_home: Path) -> Path:
    return codex_home / "sessions"


def codex_sessions_dir_for_terminal(terminal_id: str) -> Path:
    return codex_sessions_dir_for_home(codex_home_for_terminal(terminal_id))


def terminal_id_from_codex_session_file(session_file: Path) -> Optional[str]:
    """If session_file is under an Aline-managed CODEX_HOME, return terminal_id."""
    try:
        homes = aline_codex_homes_dir().resolve()
        p = session_file.resolve()
    except Exception:
        return None

    try:
        rel = p.relative_to(homes)
    except ValueError:
        return None

    parts = rel.parts
    if len(parts) < 3:
        return None
    terminal_id = (parts[0] or "").strip()
    if not terminal_id:
        return None
    if parts[1] != "sessions":
        return None
    return terminal_id


def prepare_codex_home(terminal_id: str) -> Path:
    """Create/prepare an isolated CODEX_HOME for a terminal (best-effort)."""
    home = codex_home_for_terminal(terminal_id)
    sessions = codex_sessions_dir_for_home(home)
    try:
        sessions.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Keep Codex skills working under the isolated home by symlinking to the global skills dir.
    try:
        global_skills = Path.home() / ".codex" / "skills"
        if global_skills.exists():
            skills_link = home / "skills"
            if not skills_link.exists():
                skills_link.parent.mkdir(parents=True, exist_ok=True)
                skills_link.symlink_to(global_skills)
    except Exception:
        pass

    return home

