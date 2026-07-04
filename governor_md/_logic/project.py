"""Project lifecycle logic: init, set."""

from __future__ import annotations

import os

from ..core import VisionCore
from ._session import get_registry, register


def project_init(
    project_name: str, path: str | None = None, backlog_path: str | None = None
) -> str:
    """Initialize governor in a project directory."""
    # init is a creation op: with no explicit --path, target CWD (per --help),
    # never resolve() — there is no registered project yet, which is the whole
    # point of init. Resolving here caused a circular init/set bootstrap error.
    abs_path = os.path.abspath(path) if path else os.getcwd()
    core = VisionCore(abs_path)
    core.init(project_name, backlog_path)
    pid = core.get_project_id()
    get_registry()[pid] = core
    return (
        f'Initialized governor for "{project_name}" at {core.root}\n'
        f"project_id: {pid}\n\n"
        "Call project_set with the same path to register it for this session."
    )


def project_set(path: str) -> str:
    """Register a project by its filesystem path and return its UUID."""
    try:
        root, pid = register(path)
    except FileNotFoundError as e:
        return f"Error: {e}"
    except ValueError as e:
        return f"Error: {e}"
    return (
        f"Registered project at {root}\nproject_id: {pid}\n\n"
        "Pass this project_id to all governor tool calls targeting this project."
    )
